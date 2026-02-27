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
    /* Dark pro theme overrides */
    .stApp { background: #080c14; }
    
    section[data-testid="stSidebar"] {
        background: #0b1018;
        border-right: 1px solid #151d2e;
    }
    
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: #94a3b8;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: #0d1320;
        border: 1px solid #151d2e;
        border-radius: 8px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] p { color: #4b5563 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.05em; }
    [data-testid="stMetricValue"] { color: #e2e8f0 !important; font-family: 'JetBrains Mono', monospace !important; }
    [data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; }
    
    /* Card containers */
    .card-box {
        background: #0d1320;
        border: 1px solid #151d2e;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 8px;
    }
    .card-title {
        font-size: 11px;
        color: #4b5563;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    /* Sentiment score big number */
    .big-score {
        font-family: 'JetBrains Mono', monospace;
        font-size: 36px;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 4px;
    }
    .score-label {
        font-size: 13px;
        font-weight: 500;
    }
    
    /* Gauge bar */
    .gauge-container {
        position: relative;
        height: 6px;
        border-radius: 3px;
        background: linear-gradient(90deg, #ef4444 0%, #4b5563 50%, #22c55e 100%);
        opacity: 0.3;
        margin-top: 16px;
    }
    .gauge-dot {
        position: absolute;
        top: -5px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 3px solid #080c14;
        transform: translateX(-50%);
    }
    .gauge-labels {
        display: flex;
        justify-content: space-between;
        margin-top: 6px;
        font-size: 10px;
        color: #374151;
    }
    
    /* Order pills */
    .pill-buy  { color: #22c55e; background: rgba(34,197,94,0.1); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; }
    .pill-sell { color: #ef4444; background: rgba(239,68,68,0.1); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; }
    .pill-hold { color: #64748b; background: rgba(100,116,139,0.1); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; }
    
    /* Chat bubbles */
    .chat-user {
        background: #2563eb;
        color: white;
        padding: 10px 14px;
        border-radius: 14px 14px 4px 14px;
        font-size: 13px;
        max-width: 75%;
        margin-left: auto;
        margin-bottom: 8px;
    }
    .chat-bot {
        background: #0d1320;
        border: 1px solid #151d2e;
        color: #c8d1dc;
        padding: 10px 14px;
        border-radius: 14px 14px 14px 4px;
        font-size: 13px;
        max-width: 75%;
        margin-bottom: 8px;
    }
    
    /* Ticker chip */
    .ticker-chip {
        display: inline-flex;
        align-items: center;
        justify-content: space-between;
        background: #080c14;
        border: 1px solid #151d2e;
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 120px;
    }
    .ticker-name { font-size: 13px; font-weight: 600; color: white; }
    .ticker-score { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; }
    
    /* Buttons */
    .stButton > button {
        background: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 20px !important;
    }
    .stButton > button:hover {
        background: #1d4ed8 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid #151d2e; }
    .stTabs [data-baseweb="tab"] {
        color: #64748b;
        font-size: 13px;
        font-weight: 500;
        padding: 8px 20px;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: white !important;
        border-bottom-color: #2563eb !important;
        background: transparent !important;
    }
    
    /* Text input */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background: #080c14 !important;
        border: 1px solid #151d2e !important;
        color: white !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37,99,235,0.15) !important;
    }
    
    /* Select box / Radio */
    .stSelectbox > div > div { background: #080c14 !important; border: 1px solid #151d2e !important; color: white !important; }
    .stRadio label { color: #94a3b8 !important; }
    
    /* Dividers */
    hr { border-color: #151d2e !important; }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* Sidebar nav styling */
    .sidebar-nav {
        padding: 4px 0;
    }
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0 20px 0;
        border-bottom: 1px solid #151d2e;
        margin-bottom: 16px;
    }
    .sidebar-logo-box {
        width: 32px; height: 32px;
        background: #2563eb;
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 13px; font-weight: 800;
    }
    .sidebar-logo-text {
        font-size: 16px;
        font-weight: 600;
        color: white;
        letter-spacing: -0.02em;
    }
    .live-badge {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 11px; color: #4b5563; font-weight: 500;
    }
    .live-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #22c55e;
        animation: blink 2.4s ease-in-out infinite;
    }
    @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-nav">
        <div class="sidebar-logo">
            <div class="sidebar-logo-box">SX</div>
            <span class="sidebar-logo-text">SentXStock</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["Dashboard", "Chat", "Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<div class="live-badge"><div class="live-dot"></div> LIVE</div>', unsafe_allow_html=True)


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
