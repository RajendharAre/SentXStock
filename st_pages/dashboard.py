"""Dashboard page — main analysis view with charts."""

import streamlit as st
import plotly.graph_objects as go


# ── Plotly defaults ───────────────────────────────────
_PLOT_BG = "rgba(0,0,0,0)"
_PAPER_BG = "rgba(0,0,0,0)"
_GRID_COLOR = "#1b2332"
_TEXT_COLOR = "#636e7b"
_FONT = dict(family="Inter, sans-serif", color="#c9d1d9")

_GREEN = "#3fb950"
_RED = "#f85149"
_BLUE = "#1f6feb"
_YELLOW = "#d29922"
_GRAY = "#8b949e"
_PURPLE = "#a371f7"


def _base_layout(**kw):
    """Reusable Plotly layout."""
    layout = dict(
        plot_bgcolor=_PLOT_BG,
        paper_bgcolor=_PAPER_BG,
        font=_FONT,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        height=220,
    )
    layout.update(kw)
    return go.Layout(**layout)


def render_dashboard():
    api = st.session_state.api
    settings = api.get_settings()
    tickers = settings.get("tickers", [])

    # ── Header ────────────────────────────────────────
    h_left, h_right = st.columns([4, 1])
    with h_left:
        st.markdown(
            '<div style="font-size:22px; font-weight:700; color:#e6edf3; margin-bottom:2px;">Dashboard</div>',
            unsafe_allow_html=True,
        )
        if tickers:
            st.markdown(
                f'<div style="font-size:13px; color:#636e7b;">Tracking <span style="color:#8b949e; font-weight:500;">{" · ".join(tickers)}</span></div>',
                unsafe_allow_html=True,
            )
    with h_right:
        run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

    # ── Run analysis ──────────────────────────────────
    if run_btn:
        with st.spinner("Running sentiment pipeline …"):
            try:
                result = api.run_analysis(use_mock=False)
                st.session_state.result = result
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return

    result = st.session_state.result
    if result is None:
        dash = api.get_dashboard_data()
        if dash.get("status") == "ok":
            result = dash
        else:
            st.markdown("""
            <div class="sx-empty">
                <div class="sx-empty-icon">📊</div>
                <div class="sx-empty-title">No data yet</div>
                <div class="sx-empty-sub">Configure tickers in Settings, then press Run Analysis.</div>
            </div>
            """, unsafe_allow_html=True)
            return

    # ── Extract data ──────────────────────────────────
    if "sentiment_score" in result:
        score = result.get("sentiment_score", 0)
        label = result.get("overall_sentiment", "Neutral")
        details = result.get("analysis_details", {})
        bull = details.get("bullish_count", 0)
        bear = details.get("bearish_count", 0)
        flat = details.get("neutral_count", 0)
        total = details.get("total_items_analyzed", bull + bear + flat)
        orders = result.get("orders", [])
        snapshot = result.get("portfolio_snapshot", {})
        risk_level = result.get("new_risk_level", "Medium")
        risk_text = result.get("risk_adjustment", "")
        ts = result.get("timestamp", "—")
    else:
        s = result.get("sentiment", {})
        score = s.get("score", 0)
        label = s.get("label", "Neutral")
        bull = s.get("positive", 0)
        bear = s.get("negative", 0)
        flat = s.get("neutral", 0)
        total = s.get("total_headlines", bull + bear + flat)
        orders = result.get("orders", [])
        snapshot = result.get("allocation", {})
        risk_level = result.get("risk_preference", "medium")
        risk_text = ""
        ts = result.get("timestamp", "—")

    # ── KPI strip ─────────────────────────────────────
    st.markdown("")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Headlines", total)
    k2.metric("Bullish", bull, delta=f"{(bull/total*100):.0f}%" if total else None, delta_color="normal")
    k3.metric("Bearish", bear, delta=f"{(bear/total*100):.0f}%" if total else None, delta_color="inverse")
    k4.metric("Neutral", flat)
    score_sign = "+" if score > 0 else ""
    k5.metric("Score", f"{score_sign}{score:.3f}", delta=label, delta_color="normal" if score > 0.05 else ("inverse" if score < -0.05 else "off"))

    # ── Row 1 — Sentiment gauge · Breakdown donut ────
    st.markdown("")
    col_gauge, col_donut = st.columns([3, 2])

    with col_gauge:
        color = _GREEN if score > 0.05 else (_RED if score < -0.05 else _GRAY)
        pct = max(0, min(100, ((score + 1) / 2) * 100))

        # Gradient fill from left to the needle position
        if score > 0.05:
            fill_grad = f"linear-gradient(90deg, #1b2332 0%, {_GREEN}44 {pct}%)"
        elif score < -0.05:
            fill_grad = f"linear-gradient(90deg, {_RED}44 0%, #1b2332 {pct}%)"
        else:
            fill_grad = "#1b2332"

        st.markdown(f"""
        <div class="sx-card">
            <div class="sx-card-label">Market Sentiment</div>
            <div style="display:flex; align-items:baseline; gap:10px;">
                <div class="sx-score" style="color:{color}">{score_sign}{score:.3f}</div>
                <div class="sx-score-label" style="color:{color}">{label}</div>
            </div>
            <div class="sx-gauge-track" style="background:{fill_grad}; margin-top:22px;">
                <div class="sx-gauge-needle" style="left:{pct}%; background:{color};"></div>
            </div>
            <div class="sx-gauge-ticks">
                <span>-1.0 Bearish</span>
                <span>0.0</span>
                <span>+1.0 Bullish</span>
            </div>
            <div style="margin-top:14px; font-size:12px; color:#636e7b;">
                Based on {total} headlines from Finnhub, NewsAPI & Reddit · {ts}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_donut:
        # Plotly donut chart for sentiment breakdown
        fig = go.Figure(data=[go.Pie(
            labels=["Bullish", "Bearish", "Neutral"],
            values=[bull, bear, flat],
            hole=0.65,
            marker=dict(colors=[_GREEN, _RED, _GRAY], line=dict(color="#0a0e17", width=2)),
            textinfo="none",
            hoverinfo="label+value+percent",
        )])
        fig.update_layout(
            _base_layout(height=260),
            annotations=[dict(
                text=f"<b>{total}</b><br><span style='font-size:11px; color:#636e7b'>items</span>",
                x=0.5, y=0.5, font_size=20, font_color="#e6edf3", showarrow=False,
            )],
            legend=dict(
                orientation="h", y=-0.05, x=0.5, xanchor="center",
                font=dict(size=11, color="#8b949e"),
            ),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Row 2 — Risk · Allocation · Portfolio ─────────
    st.markdown("")
    col_risk, col_alloc, col_port = st.columns(3)

    # Risk level
    with col_risk:
        risk_map = {
            "high": ("High", "Aggressive positioning", _RED),
            "medium": ("Medium", "Balanced exposure", _BLUE),
            "low": ("Low", "Defensive posture", _GREEN),
            "High": ("High", "Aggressive positioning", _RED),
            "Medium": ("Medium", "Balanced exposure", _BLUE),
            "Low": ("Low", "Defensive posture", _GREEN),
        }
        r_name, r_desc, r_color = risk_map.get(risk_level, risk_map["medium"])

        st.markdown(f"""
        <div class="sx-card" style="height:100%;">
            <div class="sx-card-label">Risk Level</div>
            <div class="sx-risk-badge" style="color:{r_color}; background:{r_color}18; margin-bottom:10px;">
                <span style="width:10px; height:10px; background:{r_color}; border-radius:50%; display:inline-block;"></span>
                {r_name}
            </div>
            <div style="font-size:13px; color:#8b949e; margin-bottom:6px;">{r_desc}</div>
            <div style="font-size:12px; color:#4b5563; line-height:1.5;">{risk_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # Allocation bar
    with col_alloc:
        equity = snapshot.get("equity_pct", 0)
        bonds = snapshot.get("bonds_pct", 0)
        cash_pct = snapshot.get("cash_pct", 0)

        st.markdown(f"""
        <div class="sx-card" style="height:100%;">
            <div class="sx-card-label">Target Allocation</div>
            <div class="sx-alloc-bar">
                <div style="width:{equity}%; background:{_BLUE}; border-radius:5px 0 0 5px;"></div>
                <div style="width:{bonds}%; background:{_PURPLE};"></div>
                <div style="width:{cash_pct}%; background:#2d333b; border-radius:0 5px 5px 0;"></div>
            </div>
            <div style="display:flex; gap:20px; flex-wrap:wrap;">
                <div class="sx-alloc-item">
                    <div class="sx-alloc-dot" style="background:{_BLUE};"></div>
                    Equity <span class="sx-alloc-pct">{equity:.1f}%</span>
                </div>
                <div class="sx-alloc-item">
                    <div class="sx-alloc-dot" style="background:{_PURPLE};"></div>
                    Bonds <span class="sx-alloc-pct">{bonds:.1f}%</span>
                </div>
                <div class="sx-alloc-item">
                    <div class="sx-alloc-dot" style="background:#2d333b;"></div>
                    Cash <span class="sx-alloc-pct">{cash_pct:.1f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Portfolio value
    with col_port:
        total_val = snapshot.get("total_value", 0)

        st.markdown(f"""
        <div class="sx-card" style="height:100%;">
            <div class="sx-card-label">Portfolio Value</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:28px; font-weight:700; color:#e6edf3;">
                ${total_val:,.2f}
            </div>
            <div style="font-size:12px; color:#636e7b; margin-top:6px;">
                Equity ${total_val * equity / 100:,.0f} · Bonds ${total_val * bonds / 100:,.0f} · Cash ${total_val * cash_pct / 100:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 3 — Orders ───────────────────────────────
    if orders:
        st.markdown("")
        st.markdown(
            '<div class="sx-card"><div class="sx-card-label">Trade Recommendations</div>',
            unsafe_allow_html=True,
        )

        for o in orders:
            action = (o.get("action", "HOLD")).upper()
            pill_cls = "sx-pill-buy" if action == "BUY" else ("sx-pill-sell" if action == "SELL" else "sx-pill-hold")
            asset = o.get("asset", "—")
            reason = o.get("reason", "")

            st.markdown(f"""
            <div class="sx-order-row">
                <span class="sx-pill {pill_cls}">{action}</span>
                <div style="flex:1; min-width:0;">
                    <div style="font-size:14px; font-weight:600; color:#e6edf3;">{asset}</div>
                    <div style="font-size:12px; color:#636e7b; margin-top:2px; line-height:1.4;">{reason}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Row 4 — Sentiment breakdown bar chart ─────────
    if bull or bear or flat:
        st.markdown("")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=["Bullish", "Bearish", "Neutral"],
            y=[bull, bear, flat],
            marker_color=[_GREEN, _RED, _GRAY],
            marker_line_color="#0a0e17",
            marker_line_width=1,
            text=[bull, bear, flat],
            textposition="outside",
            textfont=dict(size=13, color="#c9d1d9", family="JetBrains Mono"),
        ))
        fig_bar.update_layout(
            _base_layout(height=200),
            xaxis=dict(
                color=_TEXT_COLOR, showgrid=False,
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                color=_TEXT_COLOR, showgrid=True, gridcolor=_GRID_COLOR,
                zeroline=False, tickfont=dict(size=11),
            ),
            margin=dict(l=0, r=0, t=10, b=30),
        )

        col_bar_l, col_bar_r = st.columns([1, 3])
        with col_bar_l:
            st.markdown("""
            <div class="sx-card" style="height:100%; display:flex; flex-direction:column; justify-content:center;">
                <div class="sx-card-label">Headline Distribution</div>
                <div style="font-size:13px; color:#8b949e; line-height:1.6;">
                    Breakdown of sentiment<br>across all analyzed items
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_bar_r:
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
