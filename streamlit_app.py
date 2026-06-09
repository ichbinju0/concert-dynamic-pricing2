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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Hide hamburger menu & footer, keep header (loading spinner lives there) ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; }

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Dark background ── */
.stApp {
    background: #0a0a0f;
    color: #f0eaf8;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #100d1a !important;
    border-right: 1px solid #1f1535;
}
[data-testid="stSidebar"] * {
    color: #d4c8f0 !important;
}

/* ── Hero ── */
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #a855f7, #ec4899, #f97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    line-height: 1.15;
    margin-bottom: 6px;
}
.hero-caption {
    color: #7c6fa0;
    font-size: 0.88rem;
    margin-bottom: 28px;
    letter-spacing: 0.01em;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #13101f !important;
    border: 1px solid #231840 !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
}
[data-testid="metric-container"] label {
    color: #7c6fa0 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f0eaf8 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1f1535 !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: #7c6fa0 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 8px 8px 0 0 !important;
    transition: color 0.15s !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: #c084fc !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #c084fc !important;
    border-bottom: 2px solid #a855f7 !important;
    background: rgba(168, 85, 247, 0.06) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    padding: 12px 22px !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s, transform 0.15s !important;
}
.stButton > button:hover {
    opacity: 0.85 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:disabled {
    background: #1f1535 !important;
    color: #3d3060 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #13101f !important;
    border: 1px solid #231840 !important;
    border-radius: 10px !important;
    color: #f0eaf8 !important;
    font-size: 0.9rem !important;
    padding: 10px 14px !important;
}
.stSelectbox > div > div {
    background: #13101f !important;
    border: 1px solid #231840 !important;
    border-radius: 10px !important;
    color: #f0eaf8 !important;
}

/* ── Divider ── */
hr {
    border-color: #1f1535 !important;
    margin: 16px 0 !important;
}

/* ── Alert boxes ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: none !important;
    font-size: 0.88rem !important;
}

/* ── Insight box ── */
.insight-box {
    background: #13101f;
    border-left: 3px solid #a855f7;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 10px 0;
    font-size: 0.9rem;
    line-height: 1.85;
    color: #d4c8f0 !important;
}

/* ── Section label ── */
.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #a855f7;
    margin-bottom: 10px;
    margin-top: 4px;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    font-size: 0.9rem !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #13101f !important;
    border: 1px solid #231840 !important;
    border-radius: 12px !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: #13101f !important;
    border: 1px solid #7c3aed !important;
    color: #a855f7 !important;
    border-radius: 10px !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
}

/* ── Status box ── */
[data-testid="stStatusWidget"] {
    background: #13101f !important;
    border: 1px solid #231840 !important;
    border-radius: 12px !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #a855f7 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">K-pop Concert Dynamic Pricing</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-caption">'
    'Ticketbay resale data &nbsp;·&nbsp; WTP regression &rarr; LP optimization &rarr; dynamic pricing &nbsp;·&nbsp; '
    'Claude AI seat analysis + KOPIS live integration'
    '</div>',
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
for _k, _v in [("concerts", []), ("result", None), ("searched_artist", "")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Artist Setup</div>', unsafe_allow_html=True)
    artist    = st.text_input("Artist Name", placeholder="e.g. aespa, DAY6, IU")
    followers = st.number_input(
        "Instagram Followers (10k units)", min_value=0.1, max_value=10000.0,
        value=150.0, step=1.0, help="e.g. 1.5M followers → enter 150",
    )
    if followers:
        pop = followers_to_popularity(followers)
        label = {7:"Mega", 6:"Top", 5:"Popular", 4:"Mid-tier",
                 3:"Rising", 2:"Growing", 1:"Indie"}.get(pop, "")
        st.metric("Popularity Score", f"{pop} / 7", label)

    st.divider()
    if st.button("Search KOPIS", type="primary",
                 use_container_width=True, disabled=not artist):
        with st.spinner(f"Searching '{artist}'..."):
            st.session_state.concerts        = list_concerts(artist)
            st.session_state.searched_artist = artist
            st.session_state.result          = None

    st.divider()
    st.caption("IE209 Operations Management · Team Project")

# ── Main layout ───────────────────────────────────────────────────────────────
col_in, col_out = st.columns([1, 2], gap="large")

# ── Input panel ───────────────────────────────────────────────────────────────
with col_in:
    st.markdown('<div class="section-label">Concert Info</div>', unsafe_allow_html=True)

    concert_index = None
    extra         = {}
    manual_mode   = False
    concerts      = st.session_state.concerts

    if concerts:
        st.success(f"{len(concerts)} concert(s) found")
        opts = ["Auto-select (nearest upcoming)"] + [
            f"[{c['index']}]  {c['date']}  |  {c['name']}  @  {c['venue']}"
            for c in concerts
        ]
        chosen = st.selectbox("Select Concert", opts)
        if chosen != opts[0]:
            concert_index = int(chosen.split("]")[0].replace("[", "").strip())

    elif st.session_state.searched_artist:
        st.warning("No KOPIS results — manual input mode")
        manual_mode = True
        venue  = st.text_input("Venue Name", placeholder="e.g. Olympic Gymnastics Arena")
        d_day  = st.number_input("Days Until Concert", 1, 365, 60)
        n_seat = st.number_input("Total Seats", 100, 200000, 10000, 500)
        extra  = {
            "skip_kopis": True, "venue": venue,
            "sale_start_d_day": int(d_day), "total_seats": int(n_seat),
        }
    else:
        st.info("Enter an artist name in the sidebar and click Search KOPIS.")

    st.divider()
    st.markdown('<div class="section-label">Seat Map — Optional</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Claude Vision auto-assigns Z1/Z2/Z3 zone weights",
        type=["png", "jpg", "jpeg", "webp"],
    )
    img_path = None
    if uploaded:
        (_HERE / "data").mkdir(exist_ok=True)
        img_path = str(_HERE / "data" / uploaded.name)
        with open(img_path, "wb") as f:
            f.write(uploaded.read())
        st.image(img_path, caption="Uploaded seat map", use_column_width=True)

    st.divider()
    disabled = not artist or not followers or (not concerts and not manual_mode)
    if st.button("Run Pricing Optimization", type="primary",
                 use_container_width=True, disabled=disabled):
        inp = {"artist": artist, "followers_in_10k": followers,
               "concert_index": concert_index, **extra}
        if img_path:
            inp["venue_image_path"] = img_path

        with col_out:
            with st.status("Running AI agent...", expanded=True) as status:
                st.write("① Concert info verification + KOPIS lookup")
                st.write("② Claude API hedonic seat variable assignment")
                st.write("③ WTP regression → deriving floor / ceiling")
                st.write("④ LP optimization (D60 / D30 / D14 / D7 / D1)")
                st.write("⑤ 3-strategy simulation + sensitivity analysis + charts")
                try:
                    st.session_state.result = run_agent(inp)
                    status.update(label="Done!", state="complete")
                except Exception as e:
                    status.update(label=f"Error: {e}", state="error")
                    st.error(str(e))

# ── Results panel ─────────────────────────────────────────────────────────────
with col_out:
    if not st.session_state.result:
        st.info("Results will appear here after running the optimization.")
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

    def _krw(won: float) -> str:
        """Format KRW in 만원."""
        man = won / 10000
        return f"{man:.1f}만원" if man < 100 else f"{man:,.0f}만원"

    # ── KPI metrics ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Key Performance Indicators</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue Gain",    f"+{kpi.get('revenue_gain_pct', 0):.1f}%", "Dynamic vs Fixed")
    m2.metric("MAPE",             f"{kpi.get('mape', 0):.3f}")
    m3.metric("Price Floor",      _krw(floor_p))
    m4.metric("Price Ceiling",    _krw(ceiling_p))

    w1, w2, w3 = st.columns(3)
    w1.metric("WTP Mean (mu_final)", _krw(mu))
    w2.metric("Std Dev (sigma)",      _krw(sigma))
    w3.metric("LOGO MAPE",            f"{wtp.get('logo_mape', 0):.3f}")

    # Data stats
    stats = _load_data_stats()
    if stats:
        with st.expander("Training Data Stats (Ticketbay crawl)", expanded=False):
            d1, d2, d3, d4, d5 = st.columns(5)
            d1.metric("Total Records",  f"{stats['n_rows']:,}")
            d2.metric("Concerts",       f"{stats['n_concerts']}")
            d3.metric("Min Resale",     _krw(stats['price_min']))
            d4.metric("Max Resale",     _krw(stats['price_max']))
            d5.metric("D-day Range",    f"D-{stats['d_day_range']}")

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_price, tab_revenue, tab_strat, tab_sens, tab_whatif, tab_insight, tab_model = st.tabs([
        "Pricing Table",
        "Revenue Analysis",
        "Strategy Comparison",
        "Sensitivity Scenarios",
        "What-if Simulator",
        "AI Insight",
        "Model Equations",
    ])

    # ── Tab 1: Pricing Table ──────────────────────────────────────────────────
    with tab_price:
        rev3_total = kpi.get("revenue_strategy3", 0)
        gain_pct   = kpi.get("revenue_gain_pct", 0)

        st.markdown('<div class="section-label">Projected Revenue</div>', unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)
        rc1.metric(
            "Dynamic Pricing (full sellout by D-0)",
            f"{rev3_total / 1e8:.1f}억원",
            delta=f"+{gain_pct:.1f}% vs fixed price",
        )
        rc2.metric(
            "Fixed Price Baseline",
            f"{kpi.get('revenue_strategy1', 0) / 1e8:.1f}억원",
        )

        st.divider()
        report_png = _HERE / "results" / "report.png"
        if report_png.exists():
            st.download_button(
                "Download Analysis Chart (PNG)",
                data=report_png.read_bytes(),
                file_name=f"{ci.get('artist', 'pricing')}_report.png",
                mime="image/png",
            )

    # ── Tab 2: Revenue Analysis ───────────────────────────────────────────────
    with tab_revenue:
        st.markdown('<div class="section-label">Revenue Breakdown</div>', unsafe_allow_html=True)
        st.caption("Assumes full sellout by D-0 · Joint LP dynamic pricing applied")

        rev1 = kpi.get("revenue_strategy1", 0)
        rev2 = kpi.get("revenue_strategy2", 0)
        rev3 = kpi.get("revenue_strategy3", 0)
        gain = kpi.get("revenue_gain_pct", 0)

        m1, m2, m3 = st.columns(3)
        m1.metric("S1 Fixed Price",    f"{rev1/1e8:.2f}억원", help="Fixed at mu_final across all intervals")
        m2.metric("S2 Optimal Static", f"{rev2/1e8:.2f}억원", help="Single optimal price applied")
        m3.metric("S3 Dynamic LP",     f"{rev3/1e8:.2f}억원",
                  delta=f"+{gain:.1f}% vs fixed", delta_color="normal")

        st.divider()

        fig_rev = go.Figure(data=[
            go.Bar(
                x=["S1  Fixed\n(mu_final)", "S2  Optimal Static", "S3  Dynamic LP\n(Joint Opt.)"],
                y=[rev1/1e8, rev2/1e8, rev3/1e8],
                marker_color=["#7c3aed", "#db2777", "#f97316"],
                text=[f"{rev1/1e8:.2f}억원", f"{rev2/1e8:.2f}억원", f"{rev3/1e8:.2f}억원"],
                textposition="outside",
                textfont=dict(size=14, color="#f0eaf8"),
            )
        ])
        fig_rev.update_layout(
            title=dict(
                text=f"Dynamic pricing yields <b>+{gain:.1f}%</b> over fixed price",
                font=dict(size=15, color="#f0eaf8"),
            ),
            yaxis_title="Total Revenue (억원)",
            showlegend=False,
            height=420,
            plot_bgcolor="#0a0a0f",
            paper_bgcolor="#0a0a0f",
            font=dict(color="#7c6fa0", size=13),
            yaxis=dict(gridcolor="#1f1535"),
            xaxis=dict(gridcolor="#1f1535"),
        )
        st.plotly_chart(fig_rev, use_container_width=True)

        st.info(
            f"**Interpretation:** Dynamic pricing (S3) generates an additional "
            f"**{rev3/1e8 - rev1/1e8:.2f}억원 additional revenue** over the fixed baseline (S1) "
            f"(+{gain:.1f}%), assuming full sellout across all D-day intervals."
        )

    # ── Tab 3: Strategy Comparison ────────────────────────────────────────────
    with tab_strat:
        _IV_ALL    = ["D60", "D30", "D14", "D7", "D1"]
        _DDAYS     = {"D60": 60, "D30": 30, "D14": 14, "D7": 7, "D1": 1}
        _INTERVALS = [iv for iv in _IV_ALL if iv in lp]

        def _d_factor(d_day: int) -> float:
            return max(0.5, min(1.0 + b1m * (14 - d_day), 1.5))

        st.markdown('<div class="section-label">Total Revenue by Strategy</div>', unsafe_allow_html=True)
        st.caption("S3 Dynamic LP jointly optimizes prices across all intervals to maximize total revenue.")

        rev1 = kpi.get("revenue_strategy1", 0)
        rev2 = kpi.get("revenue_strategy2", 0)
        rev3 = kpi.get("revenue_strategy3", 0)

        fig_bar = go.Figure(data=[
            go.Bar(name="S1 Fixed",          x=["Fixed"],   y=[rev1/1e8],
                   marker_color="#7c3aed", text=[f"{rev1/1e8:.2f}억원"], textposition="outside"),
            go.Bar(name="S2 Optimal Static", x=["Static"],  y=[rev2/1e8],
                   marker_color="#db2777", text=[f"{rev2/1e8:.2f}억원"], textposition="outside"),
            go.Bar(name="S3 Dynamic LP",     x=["Dynamic"], y=[rev3/1e8],
                   marker_color="#f97316", text=[f"{rev3/1e8:.2f}억원"], textposition="outside"),
        ])
        fig_bar.update_layout(
            title=f"Revenue Comparison  (Dynamic Gain: +{kpi.get('revenue_gain_pct',0):.1f}%)",
            yaxis_title="Total Revenue (억원)", showlegend=True, height=350,
            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font=dict(color="#7c6fa0", size=13),
            yaxis=dict(gridcolor="#1f1535"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown('<div class="section-label">Price Trajectory by D-day</div>', unsafe_allow_html=True)
        fig_line = go.Figure()
        for s_name, s_data, s_color in [
            ("Fixed",   {iv: lp[iv] for iv in _INTERVALS if iv in lp}, "#7c3aed"),
            ("Dynamic", lp, "#f97316"),
        ]:
            ys = [s_data[iv]["price"] / 1000 for iv in _INTERVALS if iv in s_data]
            xs = [iv for iv in _INTERVALS if iv in s_data]
            fig_line.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines+markers", name=s_name,
                line=dict(color=s_color, width=2.5), marker=dict(size=9),
                hovertemplate="%{x}: %{y:.0f}k KRW<extra></extra>",
            ))
        fig_line.add_hline(y=mu/1000, line_dash="dot", line_color="#5a4f72",
                           annotation_text=f"mu_final {mu/1000:.0f}k",
                           annotation_font_color="#7c6fa0")
        fig_line.update_layout(
            yaxis_title="Price (1,000 KRW)", height=350,
            xaxis=dict(categoryorder="array", categoryarray=_INTERVALS),
            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font=dict(color="#7c6fa0", size=13),
            yaxis=dict(gridcolor="#1f1535"),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # ── Tab 4: Sensitivity Scenarios ──────────────────────────────────────────
    with tab_sens:
        st.markdown('<div class="section-label">Price Sensitivity Analysis</div>', unsafe_allow_html=True)
        st.caption("D-14 basis · no ceiling — churn acts as the natural price ceiling")

        with st.spinner("Computing scenarios..."):
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
                hovertemplate="Price: %{x:.0f}k KRW<br>Net Revenue: %{y:.2f}억<extra></extra>",
            ))
            fig_sens.add_trace(go.Scatter(
                x=[sc["optimal_price"] / 1000],
                y=[sc["optimal_net_revenue"] / 1e8],
                mode="markers", showlegend=False,
                marker=dict(color=sc["color"], size=12, symbol="star"),
                hovertemplate=f"{sc['name']}<br>Optimal: %{{x:.0f}}k<extra></extra>",
            ))

        lp_d14 = lp.get("D14", lp.get("D7", {})).get("price", mu)
        fig_sens.add_vline(
            x=lp_d14 / 1000, line_dash="dash", line_color="#5a4f72",
            annotation_text=f"LP {lp_d14/1000:.0f}k",
            annotation_position="top right",
        )
        fig_sens.add_vline(
            x=mu / 1000, line_dash="dot", line_color="#3d3060",
            annotation_text=f"mu_final {mu/1000:.0f}k",
            annotation_position="bottom right",
        )
        fig_sens.update_layout(
            xaxis_title="Price (1,000 KRW)", yaxis_title="Net Revenue (억원)",
            height=440, legend=dict(orientation="v", x=1.01),
            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font=dict(color="#7c6fa0", size=13),
            yaxis=dict(gridcolor="#1f1535"),
            xaxis=dict(gridcolor="#1f1535"),
        )
        st.plotly_chart(fig_sens, use_container_width=True)

        tbl_data = []
        for sc in scenarios:
            gain = sc["revenue_gain_vs_s1_pct"]
            tbl_data.append({
                "Scenario":         sc["name"],
                "Assumption":       sc["label"],
                "Optimal Price":    f"{sc['optimal_price']/1000:,.0f}k KRW",
                "Net Revenue (억)":  f"{sc['optimal_net_revenue']/1e8:.2f}",
                "vs S1":            f"{'▲' if gain >= 0 else '▼'} {abs(gain):.1f}%",
            })
        df_tbl = pd.DataFrame(tbl_data)

        def _color_gain(val):
            if "▼" in str(val):
                return "color: #f87171; font-weight: bold"
            return "color: #4ade80; font-weight: bold"

        st.dataframe(
            df_tbl.style.map(_color_gain, subset=["vs S1"]),
            use_container_width=True, hide_index=True,
        )

        st.info(
            "**Guide** — "
            "Star = optimal price for each scenario.  "
            "If LP recommended (dashed line) sits **right of** S4/S5 star → real-world loss.  "
            "S4 & S5 include churn + brand reputation penalty."
        )

        sens_png = _HERE / "results" / "sensitivity_report.png"
        if sens_png.exists():
            st.download_button(
                "Download Scenario Chart (PNG)",
                data=sens_png.read_bytes(),
                file_name=f"{ci.get('artist','pricing')}_sensitivity.png",
                mime="image/png",
            )

    # ── Tab 5: What-if Simulator ──────────────────────────────────────────────
    with tab_whatif:
        st.markdown('<div class="section-label">D-day Pricing Snapshot</div>', unsafe_allow_html=True)
        st.caption("Select a D-day interval to inspect remaining seats, expected sales, and zone prices.")

        _dday_opts = [iv for iv in ["D60", "D30", "D14", "D7", "D1"] if iv in lp]
        selected   = st.selectbox(
            "Select D-day Interval", _dday_opts,
            index=min(2, len(_dday_opts) - 1),
            key="whatif_dday_select",
        )

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

        m1, m2, m3 = st.columns(3)
        m1.metric("Remaining Seats",          f"{remaining_before:,}")
        m2.metric("Expected Sales (interval)", f"{sold_this:,}")
        m3.metric("Base Price",                f"{price_base:,}원")

        st.divider()

        if zone_prices:
            st.markdown('<div class="section-label">Zone Ticket Prices</div>', unsafe_allow_html=True)
            zone_rows = [{"Zone": z, "Ticket Price": f"{p:,}원"} for z, p in zone_prices.items()]
            st.dataframe(pd.DataFrame(zone_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Upload a seat map image to see zone-level pricing.")

        st.divider()
        st.markdown('<div class="section-label">Full Interval Summary</div>', unsafe_allow_html=True)
        _sum_rows = []
        _rem = total_seats
        for iv in _all_order:
            if iv not in lp:
                continue
            qty = int(lp[iv].get("quantity", 0))
            _sum_rows.append({
                "D-day":               iv,
                "Remaining (pre-sale)": f"{_rem:,}",
                "Expected Sales":       f"{qty:,}",
                "Base Price":       f"{int(lp[iv]['price']):,}원",
            })
            _rem = max(0, _rem - qty)
        st.dataframe(pd.DataFrame(_sum_rows), use_container_width=True, hide_index=True)

    # ── Tab 6: AI Insight ─────────────────────────────────────────────────────
    with tab_insight:
        st.markdown('<div class="section-label">AI Strategy Insight — Claude</div>', unsafe_allow_html=True)
        if ins:
            st.markdown(
                f'<div class="insight-box">{ins.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No Claude insight generated. Check your API key configuration.")

    # ── Tab 7: Model Equations ────────────────────────────────────────────────
    with tab_model:
        st.markdown('<div class="section-label">Model Equations</div>', unsafe_allow_html=True)
        st.caption("Core mathematical formulas used in this pricing agent.")

        st.markdown("#### 1. Hedonic Seat Weight")
        st.latex(r"W_g = \beta_{Z1} \cdot Z1_g + \beta_{Z2} \cdot Z2_g + \beta_{Z3} \cdot Z3_g")
        st.markdown("""
- $Z1$: Stage proximity (0 = farthest, 1 = closest)
- $Z2$: Frontality (0 = side, 1 = front-facing)
- $Z3$: Runway adjacency (0 or 1)
- $\\beta$ coefficients estimated via OLS regression on Ticketbay zone resale prices
        """)

        st.divider()
        st.markdown("#### 2. WTP Mean Adjustment (Temporal D-factor)")
        st.latex(r"\mu_{adj,t} = \mu_{final} \times \underbrace{\text{clamp}\!\left(1 + \frac{\beta_1}{\mu_{base}} \cdot (14 - D_t),\ 0.5,\ 1.5\right)}_{d_t}")
        st.markdown("""
- $D_t$: Days remaining until concert (D60, D30, D14, D7, D1)
- $d_t > 1$: Fan WTP increases as concert day approaches
- $\\mu_{final} = \\mu_{base} \\times f(\\text{popularity score})$
        """)

        st.divider()
        st.markdown("#### 3. Demand Function (B-method, WTP Normal)")
        st.latex(r"Q_t(P_t) = N \times \left(1 - \Phi\!\left(\frac{P_t - \mu_{adj,t}}{\sigma}\right)\right)")
        st.markdown("""
- $\\Phi$: Standard normal CDF
- $N$: Total seat count
- Higher price $P_t$ → lower demand — right-tail area of normal distribution
        """)

        st.divider()
        st.markdown("#### 4. LP Price Optimization")
        st.latex(r"\max_{P_t} \sum_{t \in \mathcal{T}} P_t \cdot Q_t(P_t)")
        st.latex(r"\text{s.t.} \quad P_{floor} \leq P_t \leq P_{ceiling}, \quad \sum_{k} x_{t,k} = 1 \quad (x_{t,k} \in \{0,1\})")
        st.markdown("""
- Nonlinear objective → linearized via 20 price candidate discretization + Binary LP
- Solver: PuLP CBC
- $P_{floor}, P_{ceiling}$: Derived from WTP distribution ($\\mu_{final} \\pm c \\cdot \\sigma$)
        """)

        st.divider()
        st.markdown("#### 5. Zone Pricing")
        st.latex(r"P_{t,g} = P_t \times \frac{W_g}{\bar{W}}, \quad \bar{W} = \frac{1}{G}\sum_g W_g")
        st.markdown("Zone price = base price scaled by the hedonic weight ratio for that zone.")

        st.divider()
        st.markdown("#### 6. Sensitivity Scenarios")
        st.latex(r"\text{churn} = \min\!\left(0.99,\ r \cdot \frac{P - P_{floor}}{0.1 \cdot P_{floor}}\right)")
        st.latex(r"R_{net} = P \cdot Q \cdot (1-\text{churn}) - \underbrace{Q \cdot \text{churn} \cdot \mu_{final} \cdot \alpha}_{\text{brand penalty}}")
        st.markdown("""
| Scenario | $r$ (churn per 10% price hike) | $\\alpha$ (brand penalty) |
|----------|-------------------------------|--------------------------|
| S1 (Current Model) | 0% | 0% |
| S2 | 3% | 0% |
| S3 | 6% | 0% |
| S4 | 10% | 5% |
| S5 | 15% | 12% |
        """)

    # ── Errors ────────────────────────────────────────────────────────────────
    if res.get("errors"):
        with st.expander("Warnings during execution"):
            for e in res["errors"]:
                st.warning(e)