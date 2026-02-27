"""
SentXStock — Streamlit Dashboard
Run: streamlit run streamlit_app.py
"""

import streamlit as st

# ─── Page Config (must be first st call) ──────────────
st.set_page_config(
    page_title="SentXStock",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Shared State ─────────────────────────────────────
from api import TradingAPI

if "api" not in st.session_state:
    st.session_state.api = TradingAPI()
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_msgs" not in st.session_state:
    st.session_state.chat_msgs = []

# ─── Custom CSS ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Base ────────────────────────── */
html, body, .stApp {
    background: #0a0e17 !important;
    color: #c9d1d9 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* ── Sidebar ─────────────────────── */
section[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1b2332 !important;
}
section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

/* ── Metric cards ────────────────── */
[data-testid="stMetric"] {
    background: #111820;
    border: 1px solid #1b2332;
    border-radius: 10px;
    padding: 18px 20px 14px;
}
[data-testid="stMetricLabel"] p {
    color: #636e7b !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}

/* ── Cards ───────────────────────── */
.sx-card {
    background: #111820;
    border: 1px solid #1b2332;
    border-radius: 10px;
    padding: 22px 24px;
}
.sx-card-label {
    font-size: 11px;
    font-weight: 600;
    color: #636e7b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
}

/* ── Sentiment ───────────────────── */
.sx-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 42px;
    font-weight: 700;
    line-height: 1;
}
.sx-score-label {
    font-size: 13px;
    font-weight: 600;
    margin-top: 4px;
}
.sx-gauge-track {
    position: relative;
    height: 8px;
    border-radius: 4px;
    background: #1b2332;
    margin-top: 20px;
    overflow: visible;
}
.sx-gauge-fill {
    position: absolute; top: 0; left: 0;
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
}
.sx-gauge-needle {
    position: absolute;
    top: 50%;
    width: 14px; height: 14px;
    border-radius: 50%;
    border: 2.5px solid #0a0e17;
    transform: translate(-50%, -50%);
    z-index: 2;
    box-shadow: 0 0 8px rgba(0,0,0,0.4);
}
.sx-gauge-ticks {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #3d4752;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}

/* ── Order pills ─────────────────── */
.sx-order-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 0;
    border-bottom: 1px solid #1b2332;
}
.sx-order-row:last-child { border-bottom: none; }
.sx-pill {
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 4px;
    text-transform: uppercase; letter-spacing: 0.04em;
    flex-shrink: 0;
}
.sx-pill-buy  { color: #3fb950; background: rgba(63,185,80,0.12); }
.sx-pill-sell { color: #f85149; background: rgba(248,81,73,0.12); }
.sx-pill-hold { color: #8b949e; background: rgba(139,148,158,0.10); }

/* ── Allocation bar ──────────────── */
.sx-alloc-bar {
    display: flex; height: 10px;
    border-radius: 5px; overflow: hidden;
    margin: 16px 0 12px;
}
.sx-alloc-item {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; color: #8b949e;
}
.sx-alloc-dot {
    width: 8px; height: 8px;
    border-radius: 50%; flex-shrink: 0;
}
.sx-alloc-pct {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600; color: #c9d1d9;
}

/* ── Chat ────────────────────────── */
.sx-msg-user {
    background: #1f6feb; color: #fff;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    font-size: 14px; line-height: 1.5;
    max-width: 72%; word-wrap: break-word;
}
.sx-msg-bot {
    background: #161b22;
    border: 1px solid #1b2332;
    color: #c9d1d9;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    font-size: 14px; line-height: 1.5;
    max-width: 72%; word-wrap: break-word;
}

/* ── Buttons ─────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 0.45rem 1.2rem !important;
    transition: all 0.15s ease !important;
}

/* ── Inputs ──────────────────────── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #0d1117 !important;
    border: 1px solid #1b2332 !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
    font-size: 14px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31,111,235,0.12) !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label {
    color: #8b949e !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.stSelectbox > div > div {
    background: #0d1117 !important;
    border: 1px solid #1b2332 !important;
    border-radius: 8px !important;
}

/* ── Radio nav ───────────────────── */
.stRadio > div { gap: 2px !important; }
.stRadio label {
    color: #8b949e !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 6px 12px !important;
    border-radius: 6px !important;
}
.stRadio label:hover { background: rgba(31,111,235,0.06) !important; color: #c9d1d9 !important; }

/* ── Dividers / Chrome ───────────── */
hr { border-color: #1b2332 !important; opacity: 0.5 !important; }
#MainMenu, footer, header { visibility: hidden !important; }

/* ── Scrollbar ───────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e17; }
::-webkit-scrollbar-thumb { background: #1b2332; border-radius: 3px; }

/* ── Sidebar brand ───────────────── */
.sx-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 4px 0 20px;
    border-bottom: 1px solid #1b2332;
    margin-bottom: 12px;
}
.sx-brand-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 13px; font-weight: 800;
}
.sx-brand-name {
    font-size: 17px; font-weight: 700; color: #e6edf3;
    letter-spacing: -0.02em;
}
.sx-live {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; color: #636e7b; font-weight: 500;
    margin-top: 2px;
}
.sx-live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #3fb950;
    animation: sx-blink 2s ease-in-out infinite;
}
@keyframes sx-blink { 0%,100%{opacity:1;} 50%{opacity:0.2;} }

/* ── Empty state ─────────────────── */
.sx-empty {
    text-align: center; padding: 80px 20px; color: #636e7b;
}
.sx-empty-icon { font-size: 48px; opacity: 0.08; margin-bottom: 16px; }
.sx-empty-title { font-size: 16px; font-weight: 600; color: #8b949e; margin-bottom: 6px; }
.sx-empty-sub { font-size: 13px; color: #4b5563; }

/* ── Risk badge ──────────────────── */
.sx-risk-badge {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 14px; font-weight: 600;
    padding: 6px 14px; border-radius: 8px;
}

/* ── About items ─────────────────── */
.sx-about-item {
    padding: 12px 0;
    border-bottom: 1px solid #1b2332;
}
.sx-about-item:last-child { border-bottom: none; }
.sx-about-label {
    font-size: 11px; font-weight: 600; color: #636e7b;
    text-transform: uppercase; letter-spacing: 0.06em;
    margin-bottom: 4px;
}
.sx-about-value {
    font-size: 13px; color: #c9d1d9; line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sx-brand">
        <div class="sx-brand-icon">SX</div>
        <div>
            <div class="sx-brand-name">SentXStock</div>
            <div class="sx-live"><div class="sx-live-dot"></div> Real-time</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "Chat", "Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("""
    <div style="font-size:11px; color:#3d4752; line-height:1.6; padding:4px 0;">
        FinBERT + Gemini 2.0-flash + VADER<br>
        Finnhub · NewsAPI · Reddit
    </div>
    """, unsafe_allow_html=True)


# ─── Page Router ──────────────────────────────────────
if page == "Dashboard":
    from st_pages.dashboard import render_dashboard
    render_dashboard()
elif page == "Chat":
    from st_pages.chat import render_chat
    render_chat()
elif page == "Settings":
    from st_pages.settings import render_settings
    render_settings()
