"""Chat page — AI trading advisor."""

import streamlit as st


def render_chat():
    api = st.session_state.api

    st.markdown("### Chat")
    st.caption("Ask about market sentiment, tickers, or portfolio strategy")

    # ── Message history ───────────────────────────────
    msgs = st.session_state.chat_msgs

    # Chat container
    chat_container = st.container()

    with chat_container:
        if not msgs:
            st.markdown("""
            <div class="card-box" style="text-align:center; padding:40px 20px;">
                <div style="font-size:22px; margin-bottom:8px; opacity:0.2;">🤖</div>
                <div style="color:#4b5563; font-size:13px;">Ask anything about the market.</div>
            </div>
            """, unsafe_allow_html=True)

            # Suggestion chips
            suggestions = [
                "What is the overall market sentiment?",
                "Should I buy AAPL right now?",
                "Explain my portfolio allocation",
                "What are the biggest risks today?",
            ]
            cols = st.columns(2)
            for i, s in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(s, key=f"sug_{i}", use_container_width=True):
                        _send_message(api, s)
                        st.rerun()
        else:
            # Render messages
            for msg in msgs:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div style="display:flex; justify-content:flex-end; margin-bottom:8px;">'
                        f'<div class="chat-user">{_escape(msg["text"])}</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="margin-bottom:8px;">'
                        f'<div class="chat-bot">{_escape(msg["text"])}</div></div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # ── Input ─────────────────────────────────────────
    col_input, col_send, col_clear = st.columns([6, 1, 1])

    with col_input:
        user_input = st.text_input(
            "Message",
            placeholder="Ask about sentiment, tickers, strategy…",
            label_visibility="collapsed",
            key="chat_input",
        )

    with col_send:
        send = st.button("Send", use_container_width=True)

    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state.chat_msgs = []
            api.clear_chat()
            st.rerun()

    if send and user_input.strip():
        _send_message(api, user_input.strip())
        st.rerun()


def _send_message(api, text):
    """Send a message and get response."""
    st.session_state.chat_msgs.append({"role": "user", "text": text})
    try:
        result = api.chat(text)
        answer = result.get("answer", result.get("response", "No response."))
        st.session_state.chat_msgs.append({"role": "assistant", "text": answer})
    except Exception as e:
        st.session_state.chat_msgs.append({"role": "assistant", "text": f"Error: {e}"})


def _escape(text):
    """Basic HTML escape."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
