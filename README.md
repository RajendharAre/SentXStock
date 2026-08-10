<p align="center">
  <h1 align="center">📈 SentXStock — Sentiment Trading Agent</h1>
  <p align="center">
    <strong>AI-powered trading advisor that reads the market mood and tells you what to do with your money.</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/FinBERT-ML%20Model-green" alt="FinBERT">
    <img src="https://img.shields.io/badge/Gemini-LLM-orange?logo=google" alt="Gemini">
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  </p>
</p>

---

## 🧠 What is SentXStock?

SentXStock is an **autonomous sentiment-driven trading agent** that monitors real-time news and social media, analyzes market sentiment using a 3-tier AI pipeline, and generates actionable buy/sell/hold recommendations for a mock portfolio.

> **No manual stock picking.** The AI reads 100+ news articles & social posts, judges the market mood, adjusts risk, and tells you exactly what to trade.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **3-Tier AI Pipeline** | FinBERT (local ML) → Gemini (LLM) → VADER (fallback) |
| 📰 **Real-Time News** | Finnhub + NewsAPI (80,000+ sources) |
| 💬 **Social Media Analysis** | Reddit (r/wallstreetbets, r/stocks, r/investing) |
| 📊 **Mock Portfolio** | Virtual portfolio with live Yahoo Finance prices |
| ⚖️ **Dynamic Risk Engine** | Auto-adjusts risk level based on market sentiment |
| 📝 **Order Drafting** | BUY / SELL / HOLD recommendations with AI reasoning |
| 💬 **AI Chatbot** | Ask questions like "Should I buy Tesla?" — get data-backed answers |
| 🔄 **API Key Rotation** | Multiple Gemini keys with auto-rotation on quota limits |
| 🎯 **User Interaction** | Custom tickers, portfolio size, and risk preference |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────┐ ┌──────────────┐ ┌────────────────────────┐ │
│  │  Sentiment  │ │   Portfolio   │ │    AI Chatbot          │ │
│  │   Gauge     │ │   Pie Chart   │ │  "Should I buy TSLA?"  │ │
│  └──────┬──────┘ └──────┬───────┘ └──────────┬─────────────┘ │
└─────────┼───────────────┼────────────────────┼───────────────┘

   ┌─────────────┐ ┌───────────┐ ┌──────────────┐
   │  Data Layer  │ │ Sentiment │ │  Portfolio    │
   │  (Fetchers)  │ │ (3-Tier)  │ │  (Risk+Orders)│
   └─────────────┘ └───────────┘ └──────────────┘
```

### 3-Tier Sentiment Pipeline

```
News/Social Posts (100+ items)
        │
        ▼
  ┌─────────────┐
  │   FinBERT    │  ← Tier 1: Local ML model (FREE, unlimited)
  │  (Primary)   │     Handles ~90% of headlines with high confidence
  └──────┬──────┘
         │
    Confident? ──Yes──→ Use FinBERT result
         │
         No (ambiguous)
         │
         ▼
  ┌─────────────┐
  │   Gemini     │  ← Tier 2: LLM (nuanced understanding)
  │  (Premium)   │     Only called for ~10% of items
  └──────┬──────┘
         │
    Available? ──Yes──→ Use Gemini result
         │
         No (quota hit)
         │
         ▼
  ┌─────────────┐
  │    VADER     │  ← Tier 3: Rule-based fallback (always works)
  │  (Fallback)  │
  └─────────────┘
```

---

## 📁 Project Structure

```
SentXStock/
├── server.py                 # Flask API server (frontend backend bridge)
├── main.py                   # CLI entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── frontend/                 # React + Vite frontend (see frontend/README)
│
├── agent/                    # Core agent logic
│   ├── agent.py              # Trading agent orchestrator (5-step pipeline)
│   └── chatbot.py            # AI chatbot for user questions
│
├── config/                   # Configuration
│   └── config.py             # API keys, thresholds, model settings
│
├── data/                     # Data fetching layer
│   ├── realtime_news.py      # Finnhub + NewsAPI news fetchers
│   ├── realtime_social.py    # Reddit social media fetcher
│   ├── scraper.py            # BeautifulSoup web scraper
│   ├── mock_news.py          # Mock news data for demo
│   └── mock_social.py        # Mock social data for demo
│
├── sentiment/                # Sentiment analysis engine
│   ├── analyzer.py           # Main analyzer (3-tier pipeline)
│   ├── finbert.py            # FinBERT local ML model
│   ├── scorer.py             # VADER scoring + aggregation
│   └── prompts.py            # LLM prompt templates
│
├── portfolio/                # Portfolio management
│   ├── portfolio.py          # Portfolio manager (holdings, live prices)
│   ├── risk.py               # Risk engine (dynamic risk adjustment)
│   └── orders.py             # Order drafter (BUY/SELL/HOLD logic)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (LTS recommended)
- npm or yarn
- Git
- Free API keys (see below)

### 1. Clone the Repository

```bash
git clone https://github.com/RajendharAre/SentXStock.git
cd SentXStock
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** First run will download FinBERT model (~438MB). This is cached locally and loads instantly on subsequent runs. Consider pre-downloading the model in CI or developer machines to avoid long cold starts.

### 3. Install Node.js Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Set Up API Keys

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Multiple Gemini keys (comma-separated) for auto-rotation
GEMINI_API_KEYS=your_key_1,your_key_2

# Finnhub (financial news)
FINNHUB_API_KEY=your_finnhub_key

# NewsAPI (80,000+ news sources)
NEWSAPI_KEY=your_newsapi_key

# Admin authentication for /api/admin/* and the admin portal
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
ADMIN_SECRET=your_admin_secret
```

#### Where to Get Free API Keys

| API | Free Tier | Sign Up |
|---|---|---|
| **Gemini** | 1,500 req/day (2.0-flash) | [ai.google.dev](https://ai.google.dev/) |
| **Finnhub** | 60 req/min | [finnhub.io](https://finnhub.io/) |
| **NewsAPI** | 100 req/day | [newsapi.org](https://newsapi.org/) |

### 4. Run the backend API (development)

Start the Flask API server that the React frontend calls.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

Git Bash / macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

### 5. Run the Agent (CLI)
```bash
# Real-time mode (uses live news + social data)
python main.py --output results.json

# Mock mode (uses demo data — great for testing)
python main.py --mock --output results.json

# Custom tickers
python main.py --tickers AAPL,TSLA,NVDA --output results.json
```

### 6. Run Smoke Tests

The core smoke suite checks the env template, frontend build wiring, and repo helper scripts without needing live API calls.

```bash
python -m unittest discover -s tests -v
```

### 7. Continuous Integration

GitHub Actions runs the same smoke suite plus a production frontend build on every push and pull request.

Workflow file: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

---


The Vite dev server runs on `http://localhost:5173` by default. During development the frontend calls the Flask API at `http://localhost:5000` (CORS is enabled in `server.py`).


### Frontend API Usage

The React frontend communicates with the Flask backend via REST API calls in [frontend/src/services/api.js](frontend/src/services/api.js):

```javascript
import { api } from './api';

// ── User Setup ──
await api.setUserTickers(["AAPL", "TSLA", "NVDA"]);
await api.setUserPortfolio(50000, "Moderate");

// ── Run Analysis ──
const result = await api.runAnalysis();           // Real-time
const result = await api.runAnalysis(true);      // Mock data

// ── AI Chatbot ──
const response = await api.chat("Should I buy Tesla?");
console.log(response.answer);

// ── Ticker Deep Dive ──
const tickerData = await api.analyzeTicker("AAPL");

// ── Dashboard Data ──
const dashboard = await api.getDashboardData();
```

The backend `server.py` handles all these endpoints and uses `api.py` for the trading logic. The frontend UI that consumes this API lives in the `frontend/` folder and runs with Vite.

### Frontend quick start

```bash
cd frontend
npm install
npm run dev
```

By default, the Vite dev server proxies `/api` requests to `http://localhost:5000`.

---

## 📊 Sample Output

```json
{
  "timestamp": "2026-02-27 15:33:33",
  "overall_sentiment": "Neutral",
  "sentiment_score": -0.0838,
  "risk_adjustment": "Maintain Medium risk — sentiment supports current allocation",
  "new_risk_level": "Medium",
  "portfolio_action": "Maintain balanced allocation with selective adjustments",
  "orders": [
    {
      "action": "SELL",
      "asset": "AAPL",
      "reason": "Risk trim on AAPL — strong negative sentiment (score: -0.67)"
    },
    {
      "action": "BUY",
      "asset": "GOOGL",
      "reason": "Opportunistic buy on GOOGL — strong positive sentiment (score: 0.92)"
    }
  ],
  "analysis_details": {
    "total_items_analyzed": 122,
    "bullish_count": 28,
    "bearish_count": 46,
    "neutral_count": 48
  },
  "portfolio_snapshot": {
    "total_value": 114834.90,
    "equity_pct": 51.74,
    "bonds_pct": 4.72,
    "cash_pct": 43.54,
    "risk_level": "Medium"
  }
}
```

---

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| **Backend Language** | Python 3.11+ |
| **Backend Server** | Flask + Flask-CORS |
| **ML Model** | FinBERT (ProsusAI/finbert) — financial sentiment BERT |
| **LLM** | Google Gemini 2.0-flash |
| **NLP Fallback** | VADER Sentiment |
| **Web Scraping** | BeautifulSoup4 |
| **News APIs** | Finnhub, NewsAPI |
| **Social Data** | Reddit JSON API |
| **Stock Prices** | Yahoo Finance (yfinance) |
| **Frontend Framework** | React 19 + Vite |
| **Frontend Styling** | Tailwind CSS |
| **Frontend Build** | Vite (lightning-fast dev server) |
| **HTTP Client** | Axios |
| **Charts** | Recharts |
| **PDF Export** | jsPDF + html2canvas |
| **Deep Learning** | PyTorch + HuggingFace Transformers |

---

## ⚙️ How It Works

### 1. Data Collection
- Fetches **50+ news headlines** from Finnhub (general + company-specific)
- Fetches **35+ headlines** from NewsAPI (business + technology)
- Scrapes **24+ posts** from Reddit (wallstreetbets, stocks, investing)
- Deduplicates overlapping headlines across sources

### 2. Sentiment Analysis (3-Tier Pipeline)
- **FinBERT** (primary): Local BERT model fine-tuned on financial text. Processes all 100+ items in ~2 seconds. Handles ~90% with high confidence.
- **Gemini** (premium): Only called for ambiguous items (~10%). Provides nuanced understanding.
- **VADER** (fallback): Rule-based scorer. Always available, no API limits.

### 3. Risk Engine
| Sentiment Score | Risk Level | Allocation |
|---|---|---|
| > 0.5 | **High** (aggressive) | 70% equity, 15% bonds, 15% cash |
| -0.3 to 0.5 | **Medium** (balanced) | 50% equity, 30% bonds, 20% cash |
| < -0.3 | **Low** (defensive) | 25% equity, 35% bonds, 40% cash |

### 4. Order Drafting
The agent generates BUY/SELL/HOLD orders based on:
- Individual ticker sentiment scores
- Overall market mood
- Current portfolio allocation vs target
- Risk level recommendations

### 5. AI Chatbot
Users can ask natural language questions. The chatbot:
- Injects real-time sentiment data into the prompt
- Uses Gemini for conversational responses
- Falls back to template-based answers if Gemini is unavailable

---

## 🔑 API Key Rotation

SentXStock supports **multiple Gemini API keys** with automatic rotation:

```env
GEMINI_API_KEYS=key1,key2,key3,key4,key5
```

- When one key hits the daily quota → automatically rotates to the next
- All keys exhausted → falls back to FinBERT + VADER (no interruption)
- Each free-tier key provides 1,500 requests/day on gemini-2.0-flash

---

## 📜 License

This project is built for the **NAAC Hackathon 2026**.

---

## 👥 Team

- **Backend & AI Pipeline** — Sentiment analysis, portfolio engine, API layer
- **Frontend** — React dashboard, visualizations, user interface

---

<p align="center">
  <strong>Built with ❤️ for the NAAC Hackathon 2026</strong>
</p>
