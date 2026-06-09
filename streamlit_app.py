"""Streamlit web UI — K-pop Concert Dynamic Pricing Agent."""
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).parent.resolve()
os.chdir(_HERE)
sys.path.insert(0, str(_HERE))

from dotenv import load_dotenv
load_dotenv(dotenv_path=_HERE / ".env", override=True)

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm

from tools.kopis_tool import list_concerts
from tools.constraint_calibrator import followers_to_popularity


@st.cache_data
def _load_data_stats() -> dict | None:
    """티켓베이 CSV에서 데이터 통계 요약."""
    try:
        df = pd.read_csv(_HERE / "data" / "ticketbay_real.csv")
        price_col = "resale_price" if "resale_price" in df.columns else "listing_price"
        concerts  = df["concert_name"].nunique() if "concert_name" in df.columns else "?"
        return {
            "n_rows":       len(df),
            "n_concerts":   concerts,
            "price_min":    int(df[price_col].min())   if price_col in df.columns else 0,
            "price_max":    int(df[price_col].max())   if price_col in df.columns else 0,
            "price_median": int(df[price_col].median()) if price_col in df.columns else 0,
            "d_day_range":  f"{int(df['d_day'].min())}~{int(df['d_day'].max())}" if "d_day" in df.columns else "?",
        }
    except Exception:
        return None
from tools.simulation import simulate_sensitivity_scenarios
from main import run_agent

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="K-pop Dynamic Pricing Agent",
    page_icon="🎵",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 12px 16px;
}
.insight-box {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-left: 4px solid #667eea;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 8px 0;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #111111 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🎵 K-pop Concert Dynamic Pricing Agent")
st.caption(
    "티켓베이 실거래 데이터 기반 WTP 회귀 → LP 최적화 → 동적 가격 책정  ·  "
    "Claude AI 좌석 분석 + KOPIS 실시간 연동"
)

# ── Session state ─────────────────────────────────────────────────────────────
for _k, _v in [("concerts", []), ("result", None), ("searched_artist", "")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎤 아티스트 입력")
    artist    = st.text_input("아티스트명", placeholder="예: aespa, DAY6, IU")
    followers = st.number_input(
        "Instagram 팔로워 (만명)", min_value=0.1, max_value=10000.0,
        value=150.0, step=1.0, help="150만명 → 150 입력",
    )
    if followers:
        pop = followers_to_popularity(followers)
        label = {7:"🔥 메가", 6:"⭐ 톱", 5:"✨ 인기", 4:"🎵 중견",
                 3:"🎶 신진", 2:"🌱 성장", 1:"🌱 인디"}.get(pop, "")
        st.metric("인기도 점수", f"{pop} / 7", label)

    st.divider()
    if st.button("🔍 KOPIS 공연 검색", type="primary",
                 use_container_width=True, disabled=not artist):
        with st.spinner(f"'{artist}' 검색 중..."):
            st.session_state.concerts       = list_concerts(artist)
            st.session_state.searched_artist = artist
            st.session_state.result          = None

    st.divider()
    st.caption("IE209 생산운영관리 팀 프로젝트")

# ── Main layout ───────────────────────────────────────────────────────────────
col_in, col_out = st.columns([1, 2], gap="large")

# ── 입력 패널 ─────────────────────────────────────────────────────────────────
with col_in:
    st.subheader("📋 공연 정보")

    concert_index = None
    extra         = {}
    manual_mode   = False
    concerts      = st.session_state.concerts

    if concerts:
        st.success(f"{len(concerts)}개 공연 발견")
        opts = ["자동 선택 (가장 가까운 공연)"] + [
            f"[{c['index']}]  {c['date']}  |  {c['name']}  @  {c['venue']}"
            for c in concerts
        ]
        chosen = st.selectbox("공연 선택", opts)
        if chosen != opts[0]:
            concert_index = int(chosen.split("]")[0].replace("[", "").strip())

    elif st.session_state.searched_artist:
        st.warning("KOPIS 결과 없음 → 수동 입력")
        manual_mode = True
        venue  = st.text_input("공연장명", placeholder="예: 올림픽체조경기장")
        d_day  = st.number_input("공연까지 남은 일수", 1, 365, 60)
        n_seat = st.number_input("총 좌석 수", 100, 200000, 10000, 500)
        extra  = {
            "skip_kopis": True, "venue": venue,
            "sale_start_d_day": int(d_day), "total_seats": int(n_seat),
        }
    else:
        st.info("사이드바에서 아티스트명을 입력하고 KOPIS 검색을 눌러주세요.")

    st.divider()
    st.subheader("🗺️ 좌석배치도 (선택)")
    uploaded = st.file_uploader(
        "Claude Vision이 구역별 Z1/Z2/Z3 자동 분석",
        type=["png", "jpg", "jpeg", "webp"],
    )
    img_path = None
    if uploaded:
        (_HERE / "data").mkdir(exist_ok=True)
        img_path = str(_HERE / "data" / uploaded.name)
        with open(img_path, "wb") as f:
            f.write(uploaded.read())
        st.image(img_path, caption="업로드된 좌석배치도", use_column_width=True)

    st.divider()
    disabled = not artist or not followers or (not concerts and not manual_mode)
    if st.button("🚀 가격 최적화 실행", type="primary",
                 use_container_width=True, disabled=disabled):
        inp = {"artist": artist, "followers_in_10k": followers,
               "concert_index": concert_index, **extra}
        if img_path:
            inp["venue_image_path"] = img_path

        with col_out:
            with st.status("AI 에이전트 실행 중...", expanded=True) as status:
                st.write("① 콘서트 정보 확인 + KOPIS 조회")
                st.write("② Claude API 좌석 헤도닉 변수 할당")
                st.write("③ WTP 회귀 분석 → floor/ceiling 도출")
                st.write("④ LP 최적화 (D60/D30/D14/D7/D1)")
                st.write("⑤ 3전략 시뮬레이션 + 민감도 분석 + 시각화")
                try:
                    st.session_state.result = run_agent(inp)
                    status.update(label="✅ 완료!", state="complete")
                except Exception as e:
                    status.update(label=f"❌ 오류: {e}", state="error")
                    st.error(str(e))

# ── 결과 패널 ─────────────────────────────────────────────────────────────────
with col_out:
    if not st.session_state.result:
        st.info("실행 결과가 여기에 표시됩니다.")
        st.stop()

    res  = st.session_state.result
    kpi  = res.get("kpi",            {})
    cons = res.get("constraints",    {})
    lp   = res.get("pricing_result", {})
    wtp  = res.get("wtp_model",      {})
    ci   = res.get("concert_info",   {})
    ins  = res.get("insight",        "")

    total_seats = ci.get("total_seats", 10000)
    floor_p     = float(cons.get("floor",    50000))
    ceiling_p   = float(cons.get("ceiling", 300000))
    mu          = float(wtp.get("mu_final",  150000))
    sigma       = float(wtp.get("sigma",      45000))
    b1m         = float(wtp.get("beta1_over_mu", -0.003))

    # ── KPI 메트릭 ────────────────────────────────────────────────────────────
    st.subheader("📊 핵심 KPI")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue Gain",     f"+{kpi.get('revenue_gain_pct', 0):.1f}%", "동적 vs 고정가")
    m2.metric("MAPE",              f"{kpi.get('mape', 0):.3f}")
    m3.metric("Floor (하한)",  f"{floor_p/10000:.1f}만원")
    m4.metric("Ceiling (상한)", f"{ceiling_p/10000:.1f}만원")

    w1, w2, w3 = st.columns(3)
    w1.metric("μ_final (WTP 평균)", f"{mu/10000:.1f}만원")
    w2.metric("σ (표준편차)",        f"{sigma/10000:.1f}만원")
    w3.metric("LOGO MAPE",          f"{wtp.get('logo_mape', 0):.3f}")

    # 데이터 통계
    stats = _load_data_stats()
    if stats:
        with st.expander("📂 학습 데이터 통계 (티켓베이 크롤링)", expanded=False):
            d1, d2, d3, d4, d5 = st.columns(5)
            d1.metric("총 관측치",    f"{stats['n_rows']:,}건")
            d2.metric("공연 수",      f"{stats['n_concerts']}개")
            d3.metric("최저 재판매가", f"{stats['price_min']//10000}만원")
            d4.metric("최고 재판매가", f"{stats['price_max']//10000}만원")
            d5.metric("D-day 범위",   f"D-{stats['d_day_range']}")

    st.divider()

    # ── 탭 ────────────────────────────────────────────────────────────────────
    tab_price, tab_revenue, tab_strat, tab_sens, tab_whatif, tab_insight, tab_model = st.tabs([
        "🎫 가격표",
        "💰 수익 분석",
        "📈 3전략 비교",
        "📉 민감도 시나리오",
        "🎚️ What-if 시뮬레이터",
        "🤖 AI 해설",
        "📐 모델 수식",
    ])

    # ── Tab 1: 가격표 ─────────────────────────────────────────────────────────
    with tab_price:
        rev3_total = kpi.get("revenue_strategy3", 0)
        gain_pct   = kpi.get("revenue_gain_pct", 0)

        st.subheader("총 예상 수익")
        rc1, rc2 = st.columns(2)
        rc1.metric(
            "동적 가격 (D-0까지 전석 판매 시)",
            f"{rev3_total / 1e8:.1f}억원",
            delta=f"고정가 대비 +{gain_pct:.1f}%",
        )
        rc2.metric(
            "고정가 기준 예상 수익",
            f"{kpi.get('revenue_strategy1', 0) / 1e8:.1f}억원",
        )

        st.divider()
        report_png = _HERE / "results" / "report.png"
        if report_png.exists():
            st.download_button(
                "⬇️ 분석 차트 PNG 다운로드",
                data=report_png.read_bytes(),
                file_name=f"{ci.get('artist', 'pricing')}_report.png",
                mime="image/png",
            )

    # ── Tab 2: 수익 분석 ─────────────────────────────────────────────────────
    with tab_revenue:
        st.subheader("총 예상 수익 분석")
        st.caption("D-0까지 전석 판매 완료 시 기준 · Joint LP 동적 가격 적용 결과")

        rev1 = kpi.get("revenue_strategy1", 0)
        rev2 = kpi.get("revenue_strategy2", 0)
        rev3 = kpi.get("revenue_strategy3", 0)
        gain = kpi.get("revenue_gain_pct", 0)

        # 핵심 수치 강조
        m1, m2, m3 = st.columns(3)
        m1.metric("고정가 (S1)", f"{rev1/1e8:.2f}억원", help="mu_final 고정가로 전 구간 판매 시")
        m2.metric("최적 고정가 (S2)", f"{rev2/1e8:.2f}억원", help="단일 최적가 적용 시")
        m3.metric("동적 가격 (S3)", f"{rev3/1e8:.2f}억원",
                  delta=f"+{gain:.1f}% vs 고정가",
                  delta_color="normal")

        st.divider()

        # 바 차트
        fig_rev = go.Figure(data=[
            go.Bar(
                x=["S1  고정가\n(mu_final)", "S2  최적 고정가", "S3  동적 LP\n(Joint 최적화)"],
                y=[rev1/1e8, rev2/1e8, rev3/1e8],
                marker_color=["#a8d8ea", "#f8b195", "#f67280"],
                text=[f"{rev1/1e8:.2f}억", f"{rev2/1e8:.2f}억", f"{rev3/1e8:.2f}억"],
                textposition="outside",
                textfont=dict(size=14, color="white"),
            )
        ])
        fig_rev.update_layout(
            title=dict(
                text=f"동적 가격 적용 시 고정가 대비 <b>+{gain:.1f}%</b> 수익 증가",
                font=dict(size=16),
            ),
            yaxis_title="총 수익 (억원)",
            showlegend=False,
            height=420,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        )
        st.plotly_chart(fig_rev, use_container_width=True)

        st.info(
            f"**해석:** 동적 가격 책정(S3)을 적용하면 고정가(S1) 대비 "
            f"**{rev3/1e8 - rev1/1e8:.2f}억원 추가 수익** 발생 "
            f"(+{gain:.1f}%). D-0까지 전 구간 티켓 판매 기준."
        )

    # ── Tab 3: 3전략 비교 (Plotly) ────────────────────────────────────────────
    with tab_strat:
        _IV_ALL    = ["D60", "D30", "D14", "D7", "D1"]
        _DDAYS     = {"D60": 60, "D30": 30, "D14": 14, "D7": 7, "D1": 1}
        _INTERVALS = [iv for iv in _IV_ALL if iv in lp]  # 실제 존재하는 구간만

        def _d_factor(d_day: int) -> float:
            return max(0.5, min(1.0 + b1m * (14 - d_day), 1.5))

        def _demand(price: float, d_day: int) -> float:
            mu_adj = mu * _d_factor(d_day)
            return total_seats * (1 - norm.cdf(price, mu_adj, sigma))

        st.subheader("전략별 총수익 비교")
        st.caption("S3 Dynamic LP는 전 구간 가격을 동시에 최적화(Joint LP)하여 총수익을 극대화합니다.")

        rev1 = kpi.get("revenue_strategy1", 0)
        rev2 = kpi.get("revenue_strategy2", 0)
        rev3 = kpi.get("revenue_strategy3", 0)

        fig_bar = go.Figure(data=[
            go.Bar(name="S1 Fixed",        x=["Fixed"],   y=[rev1/1e8],
                   marker_color="#a8d8ea", text=[f"{rev1/1e8:.2f}억"], textposition="outside"),
            go.Bar(name="S2 Optimal Static", x=["Static"],  y=[rev2/1e8],
                   marker_color="#f8b195", text=[f"{rev2/1e8:.2f}억"], textposition="outside"),
            go.Bar(name="S3 Dynamic LP",   x=["Dynamic"], y=[rev3/1e8],
                   marker_color="#f67280", text=[f"{rev3/1e8:.2f}억"], textposition="outside"),
        ])
        fig_bar.update_layout(
            title=f"총 수익 비교  (Dynamic Gain: +{kpi.get('revenue_gain_pct',0):.1f}%)",
            yaxis_title="총 수익 (억원)", showlegend=True, height=350,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("D-day별 가격 궤적")
        fig_line = go.Figure()
        strategy_colors = {"Fixed": "#a8d8ea", "Static": "#f8b195", "Dynamic": "#f67280"}
        for s_name, s_data, s_color in [
            ("Fixed",   {iv: lp[iv] for iv in _INTERVALS if iv in lp}, "#a8d8ea"),
            ("Dynamic", lp, "#f67280"),
        ]:
            ys = [s_data[iv]["price"] / 1000 for iv in _INTERVALS if iv in s_data]
            xs = [iv for iv in _INTERVALS if iv in s_data]
            fig_line.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines+markers", name=s_name,
                line=dict(color=s_color, width=2.5), marker=dict(size=8),
                hovertemplate="%{x}: %{y:.0f}k KRW<extra></extra>",
            ))
        # μ_final 기준선
        fig_line.add_hline(y=mu/1000, line_dash="dot", line_color="#95a5a6",
                           annotation_text=f"μ_final {mu/1000:.0f}k")
        fig_line.update_layout(
            yaxis_title="가격 (천원)", height=350,
            xaxis=dict(categoryorder="array", categoryarray=_INTERVALS),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # ── Tab 3: 민감도 시나리오 (Plotly) ──────────────────────────────────────
    with tab_sens:
        st.subheader("가격 민감도 시나리오 분석")
        st.caption("D-14 기준 · ceiling 제거 → 이탈이 자연 천장 역할")

        with st.spinner("시나리오 계산 중..."):
            scenarios = simulate_sensitivity_scenarios(
                wtp_model=wtp, total_seats=total_seats,
                floor_price=floor_p, d_day=14,
            )

        fig_sens = go.Figure()
        for sc in scenarios:
            xs = [p / 1000 for p in sc["price_candidates"]]
            ys = [r / 1e8  for r in sc["net_revenues"]]
            fig_sens.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", name=sc["name"],
                line=dict(color=sc["color"], width=2.2),
                hovertemplate="가격: %{x:.0f}k원<br>순수익: %{y:.2f}억원<extra></extra>",
            ))
            fig_sens.add_trace(go.Scatter(
                x=[sc["optimal_price"] / 1000],
                y=[sc["optimal_net_revenue"] / 1e8],
                mode="markers", showlegend=False,
                marker=dict(color=sc["color"], size=11, symbol="star"),
                hovertemplate=f"{sc['name']}<br>최적가: %{{x:.0f}}k<extra></extra>",
            ))

        # LP 추천가 (D14)
        lp_d14 = lp.get("D14", lp.get("D7", {})).get("price", mu)
        fig_sens.add_vline(
            x=lp_d14 / 1000, line_dash="dash", line_color="#7f8c8d",
            annotation_text=f"LP 추천 {lp_d14/1000:.0f}k",
        )
        fig_sens.add_vline(
            x=mu / 1000, line_dash="dot", line_color="#bdc3c7",
            annotation_text=f"μ_final {mu/1000:.0f}k",
        )
        fig_sens.update_layout(
            xaxis_title="가격 (천원)", yaxis_title="순수익 (억원)",
            height=420, legend=dict(orientation="v", x=1.01),
        )
        st.plotly_chart(fig_sens, use_container_width=True)

        # 시나리오 요약 표
        tbl_data = []
        for sc in scenarios:
            gain = sc["revenue_gain_vs_s1_pct"]
            tbl_data.append({
                "시나리오":     sc["name"],
                "가정":         sc["label"],
                "최적가":       f"{sc['optimal_price']/1000:,.0f}k원",
                "순수익 (억)":  f"{sc['optimal_net_revenue']/1e8:.2f}",
                "vs S1":        f"{'▲' if gain >= 0 else '▼'} {abs(gain):.1f}%",
            })
        df_tbl = pd.DataFrame(tbl_data)

        def _color_gain(val):
            if "▼" in str(val):
                return "color: #c0392b; font-weight: bold"
            return "color: #1a7a3c; font-weight: bold"

        st.dataframe(
            df_tbl.style.map(_color_gain, subset=["vs S1"]),
            use_container_width=True, hide_index=True,
        )

        st.info(
            "**해석 가이드**  \n"
            "★점 = 해당 시나리오의 순수익 최대 가격  |  "
            "LP 추천가(점선)가 S4/S5 ★보다 **오른쪽** = 현실에서 손해  \n"
            "S4·S5는 구매포기 + 브랜드 이미지 훼손 패널티 포함"
        )

        sens_png = _HERE / "results" / "sensitivity_report.png"
        if sens_png.exists():
            st.download_button(
                "⬇️ 시나리오 차트 PNG 다운로드",
                data=sens_png.read_bytes(),
                file_name=f"{ci.get('artist','pricing')}_sensitivity.png",
                mime="image/png",
            )

    # ── Tab 4: D-day별 가격 ───────────────────────────────────────────────────
    with tab_whatif:
        st.subheader("D-day별 좌석 가격 및 판매 현황")
        st.caption("구간을 선택하면 해당 시점의 잔여 좌석·예상 판매량·좌석별 티켓 가격을 확인합니다.")

        _dday_opts = [iv for iv in ["D60", "D30", "D14", "D7", "D1"] if iv in lp]
        selected   = st.selectbox("D-day 구간 선택", _dday_opts,
                                  index=min(2, len(_dday_opts) - 1))

        # 잔여 좌석 누적 계산 (D60 → 선택 구간 직전까지)
        _all_order = ["D60", "D30", "D14", "D7", "D1"]
        cumulative_sold = 0
        for iv in _all_order:
            if iv == selected:
                break
            if iv in lp:
                cumulative_sold += int(lp[iv].get("quantity", 0))
        remaining_before = total_seats - cumulative_sold

        v_sel       = lp[selected]
        sold_this   = int(v_sel.get("quantity", 0))
        price_base  = int(v_sel.get("price", 0))
        zone_prices = v_sel.get("zone_prices", {})

        # 핵심 지표
        m1, m2, m3 = st.columns(3)
        m1.metric("이 시점 잔여 좌석", f"{remaining_before:,}석")
        m2.metric("이 구간 예상 판매", f"{sold_this:,}석")
        m3.metric("기준가", f"{price_base:,}원")

        st.divider()

        # 좌석별 티켓 가격 표
        if zone_prices:
            st.markdown("**좌석 구역별 티켓 가격**")
            zone_rows = [{"구역": z, "티켓 가격 (원)": f"{p:,}"} for z, p in zone_prices.items()]
            df_zone = pd.DataFrame(zone_rows)
            st.dataframe(df_zone, use_container_width=True, hide_index=True)
        else:
            st.info("좌석 배치도 이미지를 업로드하면 구역별 가격이 표시됩니다.")

        st.divider()
        st.markdown("**전 구간 요약**")
        _sum_rows = []
        _rem = total_seats
        for iv in _all_order:
            if iv not in lp:
                continue
            qty = int(lp[iv].get("quantity", 0))
            _sum_rows.append({
                "D-day": iv,
                "잔여 좌석 (판매 전)": f"{_rem:,}",
                "예상 판매": f"{qty:,}",
                "기준가 (원)": f"{int(lp[iv]['price']):,}",
            })
            _rem = max(0, _rem - qty)
        st.dataframe(pd.DataFrame(_sum_rows), use_container_width=True, hide_index=True)

    # ── Tab 5: Claude AI 해설 ─────────────────────────────────────────────────
    with tab_insight:
        st.subheader("🤖 AI 전략 해설 (Claude)")
        if ins:
            st.markdown(
                f'<div class="insight-box">{ins.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Claude insight가 생성되지 않았습니다. (API 키 확인 필요)")

    # ── Tab 6: 모델 수식 ──────────────────────────────────────────────────────
    with tab_model:
        st.subheader("📐 모델 수식 요약")
        st.caption("본 에이전트에서 사용하는 핵심 수식입니다.")

        st.markdown("#### 1. 헤도닉 좌석 가중치 (Hedonic Seat Weight)")
        st.latex(r"W_g = \beta_{Z1} \cdot Z1_g + \beta_{Z2} \cdot Z2_g + \beta_{Z3} \cdot Z3_g")
        st.markdown("""
- $Z1$: 무대 근접도 (0=최원거리, 1=최근접)
- $Z2$: 정면성 (0=측면, 1=정면)
- $Z3$: 런웨이 인접 여부 (0 or 1)
- $\\beta$ 계수는 티켓베이 구역별 재판매가 OLS 회귀로 추정
        """)

        st.divider()
        st.markdown("#### 2. WTP 평균 조정 (Temporal D-factor)")
        st.latex(r"\mu_{adj,t} = \mu_{final} \times \underbrace{\text{clamp}\!\left(1 + \frac{\beta_1}{\mu_{base}} \cdot (14 - D_t),\ 0.5,\ 1.5\right)}_{d_t}")
        st.markdown("""
- $D_t$: 공연까지 남은 일수 (D60, D30, D14, D7, D1)
- $d_t > 1$: 공연이 가까울수록 팬들의 WTP 상승
- $\\mu_{final} = \\mu_{base} \\times f(\\text{popularity score})$
        """)

        st.divider()
        st.markdown("#### 3. WTP 수요 함수 (Demand Model, B-method)")
        st.latex(r"Q_t(P_t) = N \times \left(1 - \Phi\!\left(\frac{P_t - \mu_{adj,t}}{\sigma}\right)\right)")
        st.markdown("""
- $\\Phi$: 표준 정규 CDF
- $N$: 총 좌석 수
- 가격 $P_t$가 높아질수록 수요 감소 — 정규분포 꼬리 면적
        """)

        st.divider()
        st.markdown("#### 4. LP 최적화 (Price Optimization)")
        st.latex(r"\max_{P_t} \sum_{t \in \mathcal{T}} P_t \cdot Q_t(P_t)")
        st.latex(r"\text{s.t.} \quad P_{floor} \leq P_t \leq P_{ceiling}, \quad \sum_{k} x_{t,k} = 1 \quad (x_{t,k} \in \{0,1\})")
        st.markdown("""
- 비선형 목적함수 → 가격 후보 20개 이산화 후 Binary LP로 선형화
- Solver: PuLP CBC
- $P_{floor}, P_{ceiling}$: WTP 분포에서 자동 도출 ($\\mu_{final} \\pm c \\cdot \\sigma$)
        """)

        st.divider()
        st.markdown("#### 5. 구역별 가격 (Zone Pricing)")
        st.latex(r"P_{t,g} = P_t \times \frac{W_g}{\bar{W}}, \quad \bar{W} = \frac{1}{G}\sum_g W_g")
        st.markdown("기준가 $P_t$에 헤도닉 가중치 비율을 곱해 구역별 차등 가격 산출")

        st.divider()
        st.markdown("#### 6. 가격 민감도 시나리오 (Sensitivity)")
        st.latex(r"\text{churn} = \min\!\left(0.99,\ r \cdot \frac{P - P_{floor}}{0.1 \cdot P_{floor}}\right)")
        st.latex(r"R_{net} = P \cdot Q \cdot (1-\text{churn}) - \underbrace{Q \cdot \text{churn} \cdot \mu_{final} \cdot \alpha}_{\text{brand penalty}}")
        st.markdown("""
| 시나리오 | $r$ (10% 인상당 이탈) | $\\alpha$ (브랜드 패널티) |
|---------|----------------------|------------------------|
| S1 (현재 모델) | 0% | 0% |
| S2 | 3% | 0% |
| S3 | 6% | 0% |
| S4 | 10% | 5% |
| S5 | 15% | 12% |
        """)

    # ── 오류 ──────────────────────────────────────────────────────────────────
    if res.get("errors"):
        with st.expander("⚠️ 실행 중 발생한 경고"):
            for e in res["errors"]:
                st.warning(e)
