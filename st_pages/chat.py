"""Chat page — AI trading advisor using native Streamlit chat."""

import streamlit as st
from datetime import datetime


def render_chat():
    api = st.session_state.api
    msgs = st.session_state.chat_msgs

    # ── Header ────────────────────────────────────────
    h_left, h_right = st.columns([4, 1])
    with h_left:
        st.markdown(
            '<div style="font-size:22px; font-weight:700; color:#e6edf3; margin-bottom:2px;">AI Advisor</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size:13px; color:#636e7b;">Powered by Gemini 2.0-flash with live sentiment data</div>',
            unsafe_allow_html=True,
        )
    with h_right:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_msgs = []
            api.clear_chat()
            st.rerun()

    st.markdown("")

    # ── Empty state with suggestions ──────────────────
    if not msgs:
        st.markdown("")
        st.markdown("""
        <div style="text-align:center; padding:30px 0 20px; color:#636e7b;">
            <div style="font-size:13px; color:#4b5563;">Ask a question to get started</div>
        </div>
        """, unsafe_allow_html=True)

        suggestions = [
            ("📊", "What is the overall market sentiment right now?"),
            ("💰", "Should I buy AAPL at the current price?"),
            ("⚖️", "Explain my current portfolio allocation"),
            ("⚠️", "What are the biggest market risks today?"),
        ]
        cols = st.columns(2)
        for i, (icon, text) in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"{icon}  {text}", key=f"sug_{i}", use_container_width=True):
                    _send(api, text)
                    st.rerun()
        return

    # ── Conversation ──────────────────────────────────
    for msg in msgs:
        role = msg["role"]
        with st.chat_message("user" if role == "user" else "assistant",
                             avatar="👤" if role == "user" else "🤖"):
            st.markdown(msg["text"])

    # ── Chat input ────────────────────────────────────
    if prompt := st.chat_input("Ask about sentiment, tickers, strategy…"):
        # Show user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.chat_msgs.append({"role": "user", "text": prompt})

        # Get + show assistant response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking…"):
                try:
                    resp = api.chat(prompt)
                    answer = resp.get("answer", resp.get("response", "No response."))
                except Exception as e:
                    answer = f"Sorry, something went wrong: {e}"
            st.markdown(answer)
        st.session_state.chat_msgs.append({"role": "assistant", "text": answer})


def _send(api, text):
    """Queue a message (for suggestion chip clicks)."""
    st.session_state.chat_msgs.append({"role": "user", "text": text})
    try:
        resp = api.chat(text)
        answer = resp.get("answer", resp.get("response", "No response."))
    except Exception as e:
        answer = f"Sorry, something went wrong: {e}"
    st.session_state.chat_msgs.append({"role": "assistant", "text": answer})


def _escape(text):
    """Basic HTML escape."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
