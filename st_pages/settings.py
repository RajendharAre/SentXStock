"""Settings page — configure tickers, portfolio & risk."""

import streamlit as st


def render_settings():
    api = st.session_state.api
    settings = api.get_settings()

    st.markdown("### Settings")
    st.caption("Configure your watchlist, portfolio size, and risk preference")

    # ── Tickers ───────────────────────────────────────
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown("**Watchlist**")

    current_tickers = ", ".join(settings.get("tickers", []))
    tickers_input = st.text_input(
        "Tickers (comma-separated)",
        value=current_tickers,
        placeholder="AAPL, TSLA, NVDA, MSFT, GOOGL",
    )

    if st.button("Update Watchlist", key="btn_tickers"):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        if tickers:
            result = api.set_user_tickers(tickers)
            if result.get("success"):
                st.success(f"Watchlist updated: {', '.join(tickers)}")
            else:
                st.error(result.get("error", "Failed to update tickers"))
        else:
            st.warning("Enter at least one ticker symbol")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Portfolio ─────────────────────────────────────
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown("**Portfolio**")

    col1, col2 = st.columns(2)

    with col1:
        cash = st.number_input(
            "Investment Amount ($)",
            min_value=1000,
            max_value=10_000_000,
            value=int(settings.get("cash", 50000)),
            step=1000,
            format="%d",
        )

    risk_map_display = {"low": "Conservative", "medium": "Moderate", "high": "Aggressive"}
    risk_options = ["Conservative", "Moderate", "Aggressive"]
    current_risk = risk_map_display.get(settings.get("risk_preference", "medium"), "Moderate")

    with col2:
        risk = st.selectbox("Risk Preference", risk_options, index=risk_options.index(current_risk))

    if st.button("Save Portfolio", key="btn_portfolio"):
        result = api.set_user_portfolio(cash=float(cash), risk=risk)
        if result.get("success"):
            st.success(result.get("message", "Portfolio updated"))
        else:
            st.error(result.get("error", "Failed to update"))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Info Card ─────────────────────────────────────
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown("**About SentXStock**")
    st.markdown(
        """
        <div style="color:#6b7280; font-size:13px; line-height:1.6;">
        <b>3-Tier Sentiment Pipeline</b><br>
        FinBERT (local ML) → Gemini 2.0-flash (LLM) → VADER (fallback)<br><br>
        <b>Data Sources</b><br>
        Finnhub news · NewsAPI (80 k+ sources) · Reddit (WSB, r/stocks, r/investing)<br><br>
        <b>Risk Allocations</b><br>
        Conservative — 30 % equity · 50 % bonds · 20 % cash<br>
        Moderate — 60 % equity · 30 % bonds · 10 % cash<br>
        Aggressive — 80 % equity · 10 % bonds · 10 % cash
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
