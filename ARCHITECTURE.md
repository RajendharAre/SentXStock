# SentXStock — System Architecture
> Architecture overview for PPT / presentation slides.  
> Use this document to build architecture diagrams (flowcharts, layer diagrams, component maps).

---

## 1. Project Summary

**SentXStock** is an AI-powered stock market sentiment analysis and advisory platform targeting NSE Indian and US markets.  
It combines real-time financial news, social media sentiment, NLP/ML models, and an interactive React dashboard to give retail investors actionable BUY / SELL / HOLD signals backed by live data.

---

## 2. High-Level Architecture (3-Tier)

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│              React + Vite + Tailwind CSS                     │
│   Home · Dashboard · Portfolio · Chat · Consult · Backtest  │
└──────────────────────┬──────────────────────────────────────┘
                       │  REST API (JSON)
                       │  http://localhost:5000/api/*
┌──────────────────────▼──────────────────────────────────────┐
│                     APPLICATION LAYER                        │
│                  Flask Python Server                         │
│   TradingAPI · TradingAgent · TradingChatbot · BacktestRunner│
└──────────────────────┬──────────────────────────────────────┘
                       │  External API calls + local ML
┌──────────────────────▼──────────────────────────────────────┐
│                       DATA & ML LAYER                        │
│  News APIs · Social APIs · FinBERT · Gemini · yfinance       │
│  Portfolio Engine · Risk Engine · Order Drafter              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 Frontend (React SPA)

```
App.jsx
│
├── ThemeContext          → Dark / Light mode across all pages
├── Navbar               → Logo, nav links, theme toggle
│
├── /               →  Home.jsx          (Landing page, feature cards)
├── /dashboard      →  Dashboard.jsx     (Stock search + live analysis)
├── /portfolio      →  Portfolio.jsx     (Allocation charts + signals)
├── /chat           →  Chat.jsx          (AI chatbot interface)
├── /consult        →  Consult.jsx       (SEBI expert booking – 4 steps)
├── /backtest       →  Backtest.jsx      (Strategy simulator + charts)
└── /settings       →  Settings.jsx      (API keys, tickers, risk)

Shared Components:
  SentimentGauge · RiskLevel · OrderCards
  PortfolioChart · PDFReport · Navbar

Services:
  api.js  →  Axios calls to Flask /api/* endpoints
```

### 3.2 Backend (Flask + Python)

```
server.py  (Flask app, CORS, routes)
    │
    └──► TradingAPI  (api.py)
            │
            ├──► TradingAgent  (agent/agent.py)
            │       ├── Data Layer  (data/)
            │       │     ├── realtime_news.py    (Finnhub / NewsAPI / NewsData.io)
            │       │     ├── realtime_social.py  (Finnhub social / Reddit JSON)
            │       │     ├── mock_news.py        (Offline fallback)
            │       │     └── mock_social.py      (Offline fallback)
            │       │
            │       ├── Sentiment Layer  (sentiment/)
            │       │     ├── finbert.py      (FinBERT local model — primary)
            │       │     ├── analyzer.py     (Gemini LLM — ambiguous cases)
            │       │     ├── scorer.py       (Score aggregation)
            │       │     └── prompts.py      (LLM prompt templates)
            │       │
            │       └── Portfolio Layer  (portfolio/)
            │             ├── portfolio.py    (Holdings + allocations)
            │             ├── risk.py         (Risk level engine)
            │             └── orders.py       (BUY/SELL order drafter)
            │
            ├──► TradingChatbot  (agent/chatbot.py)
            │       ├── _detect_ticker()          (Parse ticker from question)
            │       ├── _fetch_live_stock_info()  (yfinance fallback)
            │       ├── _build_ticker_context()   (Dashboard cache → Gemini prompt)
            │       └── Gemini LLM / Template fallback
            │
            └──► BacktestRunner  (backtest/)
                    ├── data_loader.py   (yfinance OHLCV → Parquet cache)
                    ├── engine.py        (Day-by-day simulation loop)
                    ├── strategy.py      (Sentiment / RSI / Momentum logic)
                    ├── metrics.py       (Sharpe, CAGR, drawdown)
                    └── report.py        (JSON result files)
```

---

## 4. Data Flow — Stock Analysis Pipeline

```
User types ticker in Dashboard
        │
        ▼
[1] POST /api/analyze-ticker  (server.py)
        │
        ▼
[2] TradingAPI.analyze_ticker(ticker)
        │
        ├──[2a] realtime_news.py
        │         Finnhub News API ──────────┐
        │         NewsAPI (Everything) ──────┤──► Raw headlines []
        │         NewsData.io ───────────────┘
        │
        ├──[2b] realtime_social.py
        │         Finnhub Social API ────────┐
        │         Reddit JSON API ───────────┤──► Social posts []
        │         └── No scraping, public API
        │
        ├──[2c] sentiment/finbert.py
        │         ProsusAI/finbert model ────► Positive / Negative / Neutral per headline
        │         (runs locally, no API cost)
        │
        ├──[2d] sentiment/analyzer.py
        │         Gemini 2.0 Flash ──────────► Re-scores ambiguous headlines
        │         (API key rotation on quota)
        │
        ├──[2e] sentiment/scorer.py
        │         Weighted aggregation ───────► composite_score [-1.0 … +1.0]
        │
        ├──[2f] portfolio/risk.py
        │         Score → Risk Level ──────────► Low / Medium / High
        │
        └──[2g] portfolio/orders.py
                  Risk + Score → Orders ────────► [{ BUY/SELL, ticker, qty, reason }]

        ▼
[3] JSON response → React Dashboard.jsx
      • sentiment score + confidence
      • recommendation: BUY / SELL / HOLD
      • bullish / bearish headline counts
      • orders, risk level, news sources
```

---

## 5. Data Flow — AI Chatbot Pipeline

```
User types message in Chat.jsx
        │
        ▼
POST /api/chat  →  TradingChatbot.ask(question, ticker_cache, recently_viewed)
        │
        ├──[1] _detect_ticker(question)
        │         Cache name match ──► return cached analysis data
        │         Ticker base match ──► return cached analysis data
        │         All-caps regex ────► treat as unknown ticker
        │
        ├──[2a] If ticker found in cache (Dashboard data)
        │         Return formatted BUY/SELL/HOLD response from cache
        │
        ├──[2b] If ticker NOT in cache
        │         yfinance.Ticker(symbol).info ──► live price, sector, P/E, MCap
        │         Return live price + "Go analyse on Dashboard" prompt
        │
        ├──[3] If Gemini quota available
        │         Build prompt (market_context + ticker_context)
        │         Gemini 2.0 Flash ──► natural language answer
        │         Key rotation on RESOURCE_EXHAUSTED
        │
        └──[4] Template fallback (no Gemini)
                  10+ pattern matching rules
                  Structured response with real data
```

---

## 6. Data Flow — Backtesting Pipeline

```
User selects: Strategy + Ticker universe + Date range + Initial capital
        │
        ▼
POST /api/backtest  →  BacktestRunner.run()
        │
        ├──[1] data_loader.py
        │         yfinance.download(tickers, start, end)
        │         ──► Parquet cache (backtest/cache/prices/)
        │
        ├──[2] engine.py
        │         For each trading day:
        │           strategy.generate_signals(prices, sentiment_score)
        │           ──► BUY / SELL triggers
        │           Track: cash, positions, equity curve
        │
        ├──[3] metrics.py
        │         Total return · CAGR · Sharpe ratio
        │         Max drawdown · Win rate · Avg gain/loss
        │
        └──[4] report.py
                  Save JSON to backtest/results/run_YYYYMMDD_*.json
                  ──► React Backtest.jsx displays equity curve + stats table
```

---

## 7. External API Dependencies

| Service | Purpose | Fallback |
|---------|---------|---------|
| **Finnhub** | Live stock news + social sentiment | Mock news/social data |
| **NewsAPI** | Broad financial headline search | Mock news data |
| **NewsData.io** | Additional news source + ticker search | Mock news data |
| **Gemini 2.0 Flash** | LLM sentiment scoring + chatbot responses | FinBERT + template responses |
| **ProsusAI/FinBERT** | Local BERT model for financial NLP | VADER lexicon scorer |
| **Yahoo Finance (yfinance)** | Historical prices + live stock info | N/A (required for backtest) |

---

## 8. Technology Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Web Framework | Flask 3.x (Python) |
| NLP Model | FinBERT (HuggingFace Transformers, PyTorch) |
| LLM | Google Gemini 2.0 Flash (google-genai SDK) |
| Market Data | yfinance, Finnhub REST, NewsAPI, NewsData.io |
| Backtest Storage | Parquet (pyarrow / pandas) |
| Threading | Python `threading` (async analysis jobs) |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React 18 (JSX) |
| Build Tool | Vite 6 |
| Styling | Tailwind CSS 4 |
| Charts | Recharts |
| Icons | Lucide React |
| HTTP Client | Axios |
| PDF Export | jsPDF |
| Routing | React Router v6 |

---

## 9. Deployment Architecture

```
Development (Local):
┌─────────────────────┐    proxy /api/*    ┌────────────────────┐
│  Vite Dev Server    │ ──────────────────► │  Flask Server      │
│  localhost:5173     │                    │  localhost:5000     │
│  (React Hot Reload) │                    │  (Python Backend)  │
└─────────────────────┘                    └────────────────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    │               │               │
                             Finnhub API    Gemini API    yfinance
                             NewsAPI        FinBERT       NewsData.io
                             (External)     (Local)       (External)

Production (Recommended):
  Frontend  →  Vercel / Netlify (static React build)
  Backend   →  Render / Railway / EC2 (Python Flask server)
  Model     →  Bundled with backend (FinBERT loaded on startup)
```

---

## 10. Key Design Decisions

| Decision | Reason |
|----------|--------|
| **FinBERT as primary, Gemini as secondary** | FinBERT is free, local, no rate limits. Gemini adds accuracy for ambiguous text only when quota allows. |
| **Multi-key rotation for Gemini** | Free tier has low quotas. Rotating across keys gives ~3x the free capacity. |
| **Parquet cache for backtest prices** | Avoids repeated API calls for the same historical data. Parquet is 10x smaller than CSV. |
| **Flask with threading** | Analysis jobs take 5–30s. Background threads let the UI poll for progress without blocking. |
| **React SPA over Streamlit** | Streamlit was the prototype. React gives full UI control, routing, animations, PDF export. |
| **Template chatbot fallback** | When Gemini quota is exhausted, 10+ pattern rules still give data-rich, useful responses. |
| **Per-ticker analysis cache** | Dashboard results stored in-memory in Flask session so Chatbot can answer ticker questions instantly. |

---

## 11. Suggested PPT Slide Breakdown

1. **Title Slide** — SentXStock: AI-Powered Sentiment Trading Platform
2. **Problem Statement** — Information overload in markets; retail investors lack real-time signal tools
3. **Solution Overview** — What SentXStock does (3 bullet points)
4. **High-Level Architecture** — 3-tier diagram (Section 2 above)
5. **Data Sources** — Finnhub / NewsAPI / NewsData / Reddit badges
6. **Sentiment Pipeline** — Section 4 flowchart (News → FinBERT → Gemini → Score → Signal)
7. **AI Chatbot** — Section 5 flowchart (Question → Ticker detect → Cache/yfinance → Gemini/Template)
8. **Backtesting Engine** — Section 6 flowchart
9. **Technology Stack** — Table from Section 8 (Backend + Frontend)
10. **UI Screenshots** — Dashboard, Chat, Backtest, Consult pages
11. **Key Design Decisions** — Table from Section 10
12. **Deployment** — Section 9 diagram
13. **Future Scope** — Live Demat integration, mobile app, portfolio tracking, alerts
14. **Team & Conclusion**
