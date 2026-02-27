"""Dashboard page — main analysis view."""

import streamlit as st


def render_dashboard():
    api = st.session_state.api

    # ── Header row ────────────────────────────────────
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown("### Dashboard")
        current = api.get_settings()
        tickers = current.get("tickers", [])
        if tickers:
            st.caption(" · ".join(tickers))
        else:
            st.caption("Sentiment Trading Agent")

    with col_btn:
        st.write("")  # spacer
        analyze_clicked = st.button("▶ Run Analysis", use_container_width=True)

    # ── Run analysis ──────────────────────────────────
    if analyze_clicked:
        with st.spinner("Running sentiment pipeline — FinBERT → Gemini → NewsAPI → Reddit…"):
            try:
                result = api.run_analysis(use_mock=False)
                st.session_state.result = result
                st.success("Analysis complete!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return

    result = st.session_state.result
    if result is None:
        # Also try loading from api cache
        dash = api.get_dashboard_data()
        if dash.get("status") == "ok":
            result = dash
            st.session_state.result = None  # keep using dash directly
        else:
            st.markdown("""
            <div class="card-box" style="text-align:center; padding: 60px 20px;">
                <div style="font-size:28px; margin-bottom:12px; opacity:0.15;">⚡</div>
                <div style="color:#64748b; font-size:14px; font-weight:500;">No data yet</div>
                <div style="color:#374151; font-size:12px; margin-top:4px;">
                    Set your tickers in Settings, then hit Run Analysis.
                </div>
            </div>
            """, unsafe_allow_html=True)
            return

    # ── Extract data ──────────────────────────────────
    # If result is from run_analysis() it has different keys than get_dashboard_data()
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
    else:
        # From get_dashboard_data()
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

    # ── Stat strip ────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Headlines", total)
    c2.metric("Bullish", bull)
    c3.metric("Bearish", bear)
    c4.metric("Neutral", flat)

    score_delta = "bullish" if score > 0.05 else ("bearish" if score < -0.05 else "flat")
    c5.metric("Score", f"{'+' if score > 0 else ''}{score:.3f}", delta=score_delta, delta_color="normal" if score > 0.05 else ("inverse" if score < -0.05 else "off"))

    # ── Main grid: Sentiment + Risk + Portfolio ───────
    st.markdown("")
    col_sent, col_risk, col_port = st.columns(3)

    # Sentiment gauge
    with col_sent:
        color = "#22c55e" if score > 0.05 else ("#ef4444" if score < -0.05 else "#64748b")
        pct = ((score + 1) / 2) * 100

        st.markdown(f"""
        <div class="card-box">
            <div class="card-title">Sentiment</div>
            <div class="big-score" style="color:{color}">{'+' if score > 0 else ''}{score:.3f}</div>
            <div class="score-label" style="color:{color}">{label}</div>
            <div class="gauge-container">
                <div class="gauge-dot" style="left:{pct}%; background:{color};"></div>
            </div>
            <div class="gauge-labels">
                <span>-1.0</span><span>0</span><span>+1.0</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Risk level
    with col_risk:
        risk_map = {
            "high": ("High", "Aggressive", "#ef4444", "🔴"),
            "medium": ("Medium", "Balanced", "#3b82f6", "🔵"),
            "low": ("Low", "Defensive", "#22c55e", "🟢"),
            "High": ("High", "Aggressive", "#ef4444", "🔴"),
            "Medium": ("Medium", "Balanced", "#3b82f6", "🔵"),
            "Low": ("Low", "Defensive", "#22c55e", "🟢"),
        }
        r = risk_map.get(risk_level, risk_map["medium"])

        st.markdown(f"""
        <div class="card-box">
            <div class="card-title">Risk Level</div>
            <div style="font-size:28px; font-weight:700; color:white; margin-bottom:4px;">{r[0]}</div>
            <div style="font-size:12px; color:{r[2]}; font-weight:500;">{r[1]}</div>
        </div>
        """, unsafe_allow_html=True)

    # Portfolio allocation
    with col_port:
        equity = snapshot.get("equity_pct", 0)
        bonds = snapshot.get("bonds_pct", 0)
        cash_pct = snapshot.get("cash_pct", 0)
        total_val = snapshot.get("total_value", 0)

        st.markdown(f"""
        <div class="card-box">
            <div class="card-title">Allocation</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:20px; font-weight:700; color:white; margin-bottom:12px;">
                ${total_val:,.0f}
            </div>
            <div style="display:flex; gap:16px; font-size:12px;">
                <div><span style="color:#3b82f6;">●</span> <span style="color:#64748b;">Equity</span> <span style="color:#94a3b8; font-family:'JetBrains Mono',monospace; font-weight:600;">{equity:.1f}%</span></div>
                <div><span style="color:#8b5cf6;">●</span> <span style="color:#64748b;">Bonds</span> <span style="color:#94a3b8; font-family:'JetBrains Mono',monospace; font-weight:600;">{bonds:.1f}%</span></div>
                <div><span style="color:#1e293b;">●</span> <span style="color:#64748b;">Cash</span> <span style="color:#94a3b8; font-family:'JetBrains Mono',monospace; font-weight:600;">{cash_pct:.1f}%</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Orders ────────────────────────────────────────
    if orders:
        st.markdown("")
        order_html = '<div class="card-box"><div class="card-title">Orders</div>'
        for o in orders:
            action = (o.get("action", "HOLD")).upper()
            cls = "pill-buy" if action == "BUY" else ("pill-sell" if action == "SELL" else "pill-hold")
            asset = o.get("asset", "—")
            reason = o.get("reason", "")
            order_html += f"""
            <div style="display:flex; align-items:flex-start; gap:10px; padding:10px 0; border-top:1px solid #151d2e;">
                <span class="{cls}">{action}</span>
                <div>
                    <span style="font-size:13px; font-weight:600; color:white;">{asset}</span>
                    <div style="font-size:11px; color:#4b5563; margin-top:2px;">{reason}</div>
                </div>
            </div>
            """
        order_html += "</div>"
        st.markdown(order_html, unsafe_allow_html=True)
