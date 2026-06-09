import numpy as np
from scipy.stats import norm
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD

from tools.file_manager import save_json

_INTERVALS          = [("D60", 60), ("D30", 30), ("D14", 14), ("D7", 7), ("D1", 1)]
_N_PRICE_CANDIDATES = 20


def compute_d_factor(beta1_over_mu: float, d_day: int) -> float:
    return max(0.5, min(1.0 + beta1_over_mu * (14 - d_day), 1.5))


def _active_intervals(sale_start_d_day: int) -> list:
    """sale_start_d_day 이하인 구간만 반환."""
    return [(iv, d) for iv, d in _INTERVALS if d <= sale_start_d_day]


def solve_joint_lp(
    mu_final: float,
    sigma: float,
    total_seats: int,
    floor_price: int,
    ceiling_price: int,
    beta1_over_mu: float,
    sale_start_d_day: int = 60,
) -> dict:
    """Joint LP across all D-day intervals with a single shared capacity constraint.

    모든 구간 가격을 동시에 최적화하여 전체 수익을 극대화.
    공유 제약: 전 구간 판매량 합계 ≤ total_seats (같은 자리를 두 번 팔지 않음).
    """
    active           = _active_intervals(sale_start_d_day)
    price_candidates = np.linspace(floor_price, ceiling_price, _N_PRICE_CANDIDATES)

    # Demand lookup: qt[interval][price] = WTP 수요량
    qt = {}
    for interval, d_day in active:
        mu_adj = mu_final * compute_d_factor(beta1_over_mu, d_day)
        qt[interval] = {
            p: float(total_seats * (1 - norm.cdf(p, mu_adj, sigma)))
            for p in price_candidates
        }

    prob = LpProblem("joint_pricing", LpMaximize)
    x = {
        (interval, p): LpVariable(f"x_{interval}_{p:.0f}", cat="Binary")
        for interval, _ in active
        for p in price_candidates
    }

    # Objective: 전 구간 총수익 최대화
    prob += lpSum(
        p * qt[interval][p] * x[interval, p]
        for interval, _ in active
        for p in price_candidates
    )

    # 각 구간에서 가격 1개만 선택
    for interval, _ in active:
        prob += lpSum(x[interval, p] for p in price_candidates) == 1

    # 핵심: 전체 좌석 공유 제약 (같은 자리 중복 판매 방지)
    prob += lpSum(
        qt[interval][p] * x[interval, p]
        for interval, _ in active
        for p in price_candidates
    ) <= total_seats

    prob.solve(PULP_CBC_CMD(msg=0))

    results = {}
    for interval, _ in active:
        chosen = [p for p in price_candidates if (x[interval, p].value() or 0) > 0.5]
        chosen_price = float(chosen[0]) if chosen else float(price_candidates[_N_PRICE_CANDIDATES // 2])
        qty = qt[interval][chosen_price]
        results[interval] = {
            "price":    chosen_price,
            "quantity": qty,
            "revenue":  chosen_price * qty,
        }
    return results


def compute_zone_prices(base_price: float, zones: dict, floor: int, ceiling: int) -> dict:
    wg_values = [v["W_g"] for v in zones.values()]
    wg_mean   = max(float(np.mean(wg_values)), 1e-9) if wg_values else 1.0
    return {
        zone: int(np.clip(base_price * (v["W_g"] / wg_mean), floor, ceiling))
        for zone, v in zones.items()
    }


def run_lp_agent(state: dict) -> dict:
    print("[lp] Running joint LP optimization across all D-day intervals...")
    ci     = state["concert_info"]
    wtp    = state["wtp_model"]
    cons   = state["constraints"]
    zones  = state.get("seat_weights", {}).get("zones", {})
    errors = list(state.get("errors", []))

    joint_results = solve_joint_lp(
        mu_final         = wtp["mu_final"],
        sigma            = wtp["sigma"],
        total_seats      = ci["total_seats"],
        floor_price      = cons["floor"],
        ceiling_price    = cons["ceiling"],
        beta1_over_mu    = wtp["beta1_over_mu"],
        sale_start_d_day = ci.get("sale_start_d_day", 60),
    )

    results = {}
    for interval, base in joint_results.items():
        base["zone_prices"] = compute_zone_prices(base["price"], zones, cons["floor"], cons["ceiling"])
        results[interval] = base

    total_sold = sum(v["quantity"] for v in results.values())
    print(f"[lp] Joint LP complete — total sold: {total_sold:.0f} / {ci['total_seats']} seats")
    save_json("lp_prices.json", results)
    return {"pricing_result": results, "errors": errors}
