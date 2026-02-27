"""
Configuration for the Sentiment Trading Agent.
Loads API keys from .env and defines all tunable parameters.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ───────────────────────────────────────────────
# Multiple Gemini keys: comma-separated in .env for auto-rotation
_raw_gemini_keys = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS = [k.strip() for k in _raw_gemini_keys.split(",") if k.strip()]
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")

# ─── LLM Settings ───────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
LLM_TEMPERATURE = 0.1  # Low temp = deterministic output
LLM_MAX_TOKENS = 1024

# ─── Sentiment Thresholds ───────────────────────────────────
STRONG_BULLISH_THRESHOLD = 0.5
STRONG_BEARISH_THRESHOLD = -0.3
NEUTRAL_LOWER = -0.3
NEUTRAL_UPPER = 0.3

# ─── Risk Level Allocation Targets (%) ──────────────────────
RISK_ALLOCATIONS = {
    "High": {"equity": 70, "bonds": 15, "cash": 15},
    "Medium": {"equity": 50, "bonds": 30, "cash": 20},
    "Low": {"equity": 25, "bonds": 35, "cash": 40},
}

# ─── Asset Classification ───────────────────────────────────
EQUITY_ASSETS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META"]
BOND_ASSETS = ["TLT", "BND", "AGG", "IEF"]
DEFENSIVE_ASSETS = ["GLD", "SHY", "TIP"]

# ─── Data Refresh Interval (seconds) ────────────────────────
REFRESH_INTERVAL = 300  # 5 minutes

# ─── Finnhub Endpoints ──────────────────────────────────────
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_NEWS_URL = f"{FINNHUB_BASE_URL}/news?category=general&token={FINNHUB_API_KEY}"
FINNHUB_COMPANY_NEWS_URL = f"{FINNHUB_BASE_URL}/company-news"

# ─── NewsAPI Endpoints ───────────────────────────────────────
NEWSAPI_BASE_URL = "https://newsapi.org/v2"
NEWSAPI_HEADLINES_URL = f"{NEWSAPI_BASE_URL}/top-headlines"
NEWSAPI_EVERYTHING_URL = f"{NEWSAPI_BASE_URL}/everything"

# ─── NewsData.io Endpoints ───────────────────────────────────
NEWSDATA_BASE_URL = "https://newsdata.io/api/1"
NEWSDATA_LATEST_URL = f"{NEWSDATA_BASE_URL}/latest"
NEWSDATA_NEWS_URL = f"{NEWSDATA_BASE_URL}/news"

# ─── StockTwits (No key needed) ─────────────────────────────
STOCKTWITS_BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol"

# ─── Tracked Tickers ────────────────────────────────────────
# Default watchlist — NSE blue chips for the Indian market
DEFAULT_TICKERS = [
    "TCS.NS",       # Tata Consultancy Services
    "HDFCBANK.NS",  # HDFC Bank
    "RELIANCE.NS",  # Reliance Industries
    "INFY.NS",      # Infosys
    "ICICIBANK.NS", # ICICI Bank
]
