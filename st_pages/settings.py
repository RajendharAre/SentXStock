"""Settings page — configure tickers, portfolio & risk."""

import streamlit as st


def render_settings():
    api = st.session_state.api
    settings = api.get_settings()

    # ── Header ────────────────────────────────────────
    st.markdown(
        '<div style="font-size:22px; font-weight:700; color:#e6edf3; margin-bottom:2px;">Settings</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:13px; color:#636e7b; margin-bottom:20px;">Configure your watchlist, portfolio size, and risk preference</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([3, 2])

    # ── Left column — Watchlist + Portfolio ───────────
    with col_left:
        # Watchlist
        st.markdown(
            '<div class="sx-card"><div class="sx-card-label">Watchlist</div></div>',
            unsafe_allow_html=True,
        )
        current_tickers = ", ".join(settings.get("tickers", []))
        tickers_input = st.text_input(
            "Tickers (comma-separated, max 10)",
            value=current_tickers,
            placeholder="AAPL, TSLA, NVDA, MSFT, GOOGL",
            key="set_tickers",
        )
        if st.button("Save Watchlist", key="btn_tickers"):
            tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            if tickers:
                result = api.set_user_tickers(tickers)
                if result.get("success"):
                    st.session_state.result = None  # clear stale dashboard
                    st.success(f"Watchlist updated — {', '.join(tickers)}")
                    st.info("Go to Dashboard and press Run Analysis to see new results.")
                else:
                    st.error(result.get("error", "Update failed"))
            else:
                st.warning("Enter at least one ticker symbol")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Portfolio
        st.markdown(
            '<div class="sx-card"><div class="sx-card-label">Portfolio</div></div>',
            unsafe_allow_html=True,
        )

        p1, p2 = st.columns(2)
        with p1:
            cash = st.number_input(
                "Investment ($)",
                min_value=1000,
                max_value=10_000_000,
                value=int(settings.get("cash", 50000)),
                step=5000,
                format="%d",
                key="set_cash",
            )
        with p2:
            risk_display = {"low": "Conservative", "medium": "Moderate", "high": "Aggressive"}
            risk_options = ["Conservative", "Moderate", "Aggressive"]
            current_risk = risk_display.get(settings.get("risk_preference", "medium"), "Moderate")
            risk = st.selectbox(
                "Risk Preference",
                risk_options,
                index=risk_options.index(current_risk),
                key="set_risk",
            )

        if st.button("Save Portfolio", key="btn_portfolio"):
            result = api.set_user_portfolio(cash=float(cash), risk=risk)
            if result.get("success"):
                st.session_state.result = None  # clear stale dashboard
                st.success(result.get("message", "Portfolio updated"))
                st.info("Go to Dashboard and press Run Analysis to see updated results.")
            else:
                st.error(result.get("error", "Update failed"))

    # ── Right column — About + Quick reference ────────
    with col_right:
        st.markdown("""
        <div class="sx-card">
            <div class="sx-card-label">About SentXStock</div>

            <div class="sx-about-item">
                <div class="sx-about-label">Sentiment Pipeline</div>
                <div class="sx-about-value">
                    <span style="color:#3fb950;">FinBERT</span> (local ML) →
                    <span style="color:#1f6feb;">Gemini 2.0-flash</span> (LLM) →
                    <span style="color:#d29922;">VADER</span> (fallback)
                </div>
            </div>

            <div class="sx-about-item">
                <div class="sx-about-label">Data Sources</div>
                <div class="sx-about-value">Finnhub news · NewsAPI (80 k+ sources) · Reddit (WSB, r/stocks, r/investing)</div>
            </div>

            <div class="sx-about-item">
                <div class="sx-about-label">Risk Profiles</div>
                <div class="sx-about-value" style="font-family:'JetBrains Mono',monospace; font-size:12px;">
                    <div style="display:flex; gap:8px; margin-bottom:4px;">
                        <span style="color:#3fb950; width:96px;">Conservative</span>
                        <span>30% equity · 50% bonds · 20% cash</span>
                    </div>
                    <div style="display:flex; gap:8px; margin-bottom:4px;">
                        <span style="color:#1f6feb; width:96px;">Moderate</span>
                        <span>60% equity · 30% bonds · 10% cash</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <span style="color:#f85149; width:96px;">Aggressive</span>
                        <span>80% equity · 10% bonds · 10% cash</span>
                    </div>
                </div>
            </div>

            <div class="sx-about-item" style="border-bottom:none;">
                <div class="sx-about-label">Project</div>
                <div class="sx-about-value">
                    NAAC Hackathon 2026 · 
                    <a href="https://github.com/RajendharAre/SentXStock" target="_blank" 
                       style="color:#1f6feb; text-decoration:none;">GitHub ↗</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
