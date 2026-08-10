# SentXStock — Indian Market Sentiment Trading Platform
## Development Progress Tracker

> **Project:** NAAC Hackathon 2026 — SentXStock Indian Edition
> **Stack:** Python Flask + React Vite + Tailwind + FinBERT + Gemini
> **Market:** Indian equities (NSE — `.NS` tickers via yfinance)
> **Currency:** INR only
> **Last Updated:** 2026-02-27

---

## Module Progress

| # | Module | Status | Notes |
|---|--------|--------|-------|
| 1 | Indian Universe + Data Foundation | Complete | 500 NSE companies, 11 sectors |
| 2 | Home Page | **Complete** | Home.jsx — 8 sections, no emojis, Lucide icons |
| 3 | Navbar + Routing | **Complete** | Home, Dashboard, AI Advisor, Consult Expert, Settings |
| 4 | Dashboard Overhaul | **Complete** | Company search, per-company analysis panel, sector filter |
| 5 | Hidden Auto-Backtest | Pending | Auto-triggered on company select |
| 6 | Settings Page + Admin | Pending | Dark/light/system, admin credentials |
| 7 | Chat Enhancement | Pending | Gemini → fallback structured output |
| 8 | PDF Report | Pending | Full portfolio download |
| 9 | Risk + Portfolio Engine | Pending | INR-denominated, dynamic allocation |

**Rule:** One module at a time. Mark complete. Do NOT push to GitHub. Wait for confirmation.

---

## Module 1 — Indian Universe + Data Foundation

### Completed
- [x] `backtest/universe_india.py` — 500 Indian NSE companies across 11 sectors
- [x] `scripts/download_india_datasets.py` — Download 5-year OHLCV CSVs for all NSE tickers
- [x] Updated PLAN.md

### Data Architecture
```
datasets/
  prices/
    TCS.NS.csv          # OHLCV, yfinance auto_adjust=True
    INFY.NS.csv
    ...
  sentiment/
    TCS.NS.csv          # Date, sentiment_score (derived)
    ...
backtest/
  cache/prices/         # Parquet cache (fast re-runs)
  results/              # Saved backtest JSON files
```

### Loading Priority (data_loader.py)
```
1. datasets/prices/<TICKER>.csv   ← local CSV (offline, fast)
2. backtest/cache/prices/*.parquet ← parquet cache
3. yfinance live download          ← fallback
```

### Ticker Format
- All NSE tickers: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`
- Benchmark: `^NSEI` (Nifty 50)
- Currency: INR throughout

### Sector Map
| Sector | Count | Example Tickers |
|--------|-------|-----------------|
| Technology | 45 | TCS.NS, INFY.NS, WIPRO.NS |
| Banking & Finance | 80 | HDFCBANK.NS, ICICIBANK.NS, SBIN.NS |
| FMCG | 40 | HINDUNILVR.NS, ITC.NS, NESTLEIND.NS |
| Healthcare | 45 | SUNPHARMA.NS, DRREDDY.NS, CIPLA.NS |
| Energy & Oil | 35 | RELIANCE.NS, ONGC.NS, NTPC.NS |
| Infrastructure | 30 | LT.NS, ULTRACEMCO.NS, DLF.NS |
| Automobile | 40 | MARUTI.NS, TATAMOTORS.NS, M&M.NS |
| Metals & Mining | 30 | TATASTEEL.NS, JSWSTEEL.NS, HINDALCO.NS |
| Telecom & Media | 20 | BHARTIARTL.NS, IDEA.NS |
| Consumer Discretionary | 35 | TITAN.NS, ASIANPAINT.NS |
| Conglomerates | 20 | ADANIENT.NS, ADANIPORTS.NS |

---

## Module 2 — Home Page (Complete)

### Completed
- [x] Hero section — platform name, tagline, 2 CTAs, disclaimer ribbon
- [x] How It Works — 5-step process with Lucide icons
- [x] Platform Capabilities — 6 feature cards (2-col/3-col grid)
- [x] Strategy Explanation — signal weights, thresholds, risk multipliers, backtest params
- [x] Performance Statistics — 6 platform coverage stats
- [x] Supported Sectors — all 11 NSE sectors with company counts
- [x] FAQ Accordion — 8 expandable Q&A items (no emojis, Lucide icons)
- [x] CTA Footer Strip

---

## Module 3 — Navbar + Routing (Complete)

### Completed
- [x] `/` → Home (new landing page)
- [x] `/dashboard` → Dashboard (company select + analysis)
- [x] `/settings` → Settings
- [x] `/chat` → AI Advisor (Gemini AI chat, labelled correctly)
- [x] `/consult` → Consult Expert (NEW — real human SEBI-registered advisor booking page)
- [x] `/backtest` → Backtest (route kept, hidden from nav)
- [x] Navbar links: Home, Dashboard, AI Advisor, Consult Expert, Settings
- [x] Removed Backtest from nav — runs silently in background
- [x] Brand logo still links to `/`

---

## Module 4 — Dashboard Overhaul (Complete)

### Completed
- [x] Sector dropdown filter (11 NSE sectors from API)
- [x] Company search box with 250ms debounced autocomplete (500 NSE companies)
- [x] Live results dropdown — shows name, ticker, sector
- [x] On company select → `analyzeTicker()` fires with loading state
- [x] Company header — name, ticker badge, exchange badge, sector badge
- [x] Sentiment score gauge bar (-1 to +1 visual with marker)
- [x] Sentiment breakdown bars (Bullish / Bearish / Neutral with % and count)
- [x] Recommendation badge (Strong Buy / Buy / Hold / Sell / Strong Sell)
- [x] Confidence percentage display
- [x] AI-generated explanation text field
- [x] Risk level panel (Low / Medium / High — active state highlighted)
- [x] Portfolio allocation panel (suggested amount in INR, position size %)
- [x] Order signals table (BUY/SELL/HOLD per order)
- [x] Key Financial Metrics grid (P/E, P/B, Market Cap, 52W High/Low, Volume)
- [x] News table with per-article sentiment badge and score
- [x] Legacy portfolio overview preserved for global getDashboard() data
- [x] Empty state with "Run Portfolio Analysis" button

---

## Module 5 — Hidden Auto-Backtest (Complete)

### Behavior
- [ ] Company selected → `POST /api/backtest/run` fires silently
- [ ] Background polling — user never sees raw backtest UI
- [ ] Result injected into dashboard as "Performance Summary"
- [ ] Date range: 3 years ending January 2026
- [ ] Exported metrics only: Strategy Return, Max Drawdown, Risk-Adjusted Return, Win Rate

---

## Module 6 — Settings Page + Admin (Complete)

### Settings Sections
- [ ] Appearance: Dark / Light / System mode selector
- [ ] Portfolio: Cash (INR default 50000), Risk preference
- [ ] Data: Mock Mode toggle, Update Data button
- [ ] Admin login section

### Admin Credentials (demo only)
- Username: `admin_sentxstock`
- Password: `Admin@33*`
- [ ] Admin features: CSV dataset upload, company list management
- [ ] Non-admin users cannot access admin area regardless of attempts

---

## Module 7 — Chat Enhancement (Complete)

### Response Priority Flow
1. Gemini API (primary)
2. If quota exceeded: FinBERT sentiment + structured metrics table
3. If no data: curated article links + financial source references

### UI Formatting Requirements
- [ ] Markdown rendering inside chat bubbles
- [ ] Tables for metrics comparison
- [ ] Clickable external links
- [ ] Clear headings / subheadings

---

## Module 8 — PDF Report (Complete)

### PDF Contents
- [ ] Company summary header
- [ ] Sentiment score + trend visualization
- [ ] 3-year backtest performance summary
- [ ] Recommendation + confidence
- [ ] Risk allocation table
- [ ] Timestamp + disclaimer footer

### Implementation
- [ ] `jsPDF` + `html2canvas` (client-side generation)
- [ ] Triggered from "Download Report" button on Dashboard

---

## Module 9 — Risk + Portfolio Engine (Complete)

### INR-Denominated Logic
- [x] Default capital: 50000 INR
- [x] Per-stock allocation: `confidence × risk_multiplier × (1 / n_positions)`
- [x] Maximum single position: 20% of total portfolio
- [x] Dynamic rebalancing when sentiment shifts > threshold

### Implementation
- `api.py` → `get_portfolio_allocations()` — server-side allocation engine
- `server.py` → `GET /api/portfolio/allocations` — new Flask route
- `frontend/src/services/api.js` → `getPortfolioAllocations()`
- `frontend/src/pages/Portfolio.jsx` — full portfolio page with PieChart + allocation cards
- `frontend/src/components/Navbar.jsx` — Portfolio nav item (PieChart icon)
- `frontend/src/App.jsx` → `/portfolio` route added

---

## Technical Architecture

```
server.py (Flask)
├── /api/analyze         ← sentiment pipeline
├── /api/analyze/status  ← polling
├── /api/dashboard       ← all dashboard data
├── /api/backtest/run    ← hidden auto-backtest
├── /api/backtest/status ← background polling
├── /api/company/search  ← company search (Module 4)
├── /api/company/info    ← company metadata
└── /api/settings        ← user settings

backtest/
├── universe_india.py    ← 500 NSE tickers (Module 1)
├── universe.py          ← S&P 500 (kept for reference)
├── data_loader.py       ← CSV → parquet → yfinance
├── engine.py            ← walk-forward simulation
├── strategy.py          ← signal generation
├── metrics.py           ← Sharpe, drawdown, etc.
├── report.py            ← JSON persistence
└── runner.py            ← single entry point

frontend/src/
├── pages/
│   ├── Home.jsx         ← Module 2
│   ├── Dashboard.jsx    ← Module 4 (overhaul)
│   ├── Settings.jsx     ← Module 6 (overhaul)
│   ├── Consult.jsx      ← Module 3
│   └── Chat.jsx
├── components/
│   ├── Navbar.jsx       ← Module 3
│   ├── CompanySearch.jsx
│   ├── SentimentGauge.jsx
│   ├── RecommendationBadge.jsx
│   └── PdfReportButton.jsx  ← Module 8
└── services/api.js
```

---

## Development Rules

1. Implement one module at a time
2. Update this file with completed checkboxes after each task
3. **Do NOT push to GitHub without user confirmation**
4. No hardcoded ticker logic anywhere
5. No emojis in UI — Lucide React icons only
6. All monetary values in INR


---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                     REACT FRONTEND                  │
│            (Portfolio Dashboard + Orders)            │
│              [Your friend handles this]              │
└──────────────────────┬──────────────────────────────┘
                       │ API / Function Calls
┌──────────────────────▼──────────────────────────────┐
│                    BACKEND (Python)                  │
│                                                      │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Sentiment   │  │  Portfolio   │  │   Agent    │ │
│  │  Analyzer    │  │  Manager     │  │   Engine   │ │
│  │  (LLM +     │  │  (Mock)      │  │  (Rules +  │ │
│  │  BeautifulSoup)│ │             │  │   Logic)   │ │
│  └──────┬───────┘  └──────┬──────┘  └─────┬──────┘ │
│         │                 │                │         │
│  ┌──────▼─────────────────▼────────────────▼──────┐ │
│  │              Data Layer (JSON/Mock DB)          │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Backend Modules (Our Responsibility)

### Module 1: `data/` — Mock Data & Scraping

| File | Purpose |
|------|---------|
| `mock_news.py` | Mock news headlines (finance-related) |
| `mock_social.py` | Mock social media posts (Twitter/Reddit style) |
| `scraper.py` | BeautifulSoup scraper to pull real headlines (bonus) |

**Mock data format:**
```python
news_headlines = [
    {"source": "Reuters", "headline": "Tech stocks surge on strong earnings", "timestamp": "2026-02-27 09:00"},
    {"source": "Bloomberg", "headline": "Fed signals rate hike concerns", "timestamp": "2026-02-27 09:30"},
]

social_posts = [
    {"platform": "Twitter", "post": "$AAPL to the moon! 🚀", "timestamp": "2026-02-27 10:00"},
    {"platform": "Reddit", "post": "Market crash incoming, selling everything", "timestamp": "2026-02-27 10:15"},
]
```

---

### Module 2: `sentiment/` — Sentiment Analysis Engine

| File | Purpose |
|------|---------|
| `analyzer.py` | Core sentiment analysis (LLM-based + rule-based fallback) |
| `prompts.py` | LLM prompt templates for sentiment extraction |
| `scorer.py` | Scoring logic: maps sentiments to -1 to +1 scale |

**Sentiment Pipeline:**
```
Raw Text → LLM Prompt → Bullish/Bearish/Neutral → Score (-1 to +1) → Aggregate
```

**Scoring Rules:**
| Sentiment | Score Range |
|-----------|-------------|
| Strong Bullish | +0.7 to +1.0 |
| Bullish | +0.3 to +0.7 |
| Neutral | -0.3 to +0.3 |
| Bearish | -0.7 to -0.3 |
| Strong Bearish | -1.0 to -0.7 |

---

### Module 3: `portfolio/` — Mock Portfolio Manager

| File | Purpose |
|------|---------|
| `portfolio.py` | Portfolio state management (holdings, cash, allocation %) |
| `risk.py` | Risk level adjustment algorithm |
| `orders.py` | Buy/sell order drafting logic |

**Default Mock Portfolio:**
```python
portfolio = {
    "cash": 50000,
    "holdings": {
        "AAPL": {"shares": 50, "avg_price": 180},
        "GOOGL": {"shares": 20, "avg_price": 140},
        "MSFT": {"shares": 30, "avg_price": 380},
        "SPY": {"shares": 40, "avg_price": 450},
        "TLT": {"shares": 60, "avg_price": 95},  # Bonds (defensive)
    },
    "risk_level": "Medium"
}
```

**Risk Adjustment Rules (Deterministic):**
```
IF sentiment_score > +0.5  → risk_level = "High"   → Increase equity, reduce bonds/cash
IF sentiment_score -0.3 to +0.5 → risk_level = "Medium" → Balanced allocation
IF sentiment_score < -0.3 → risk_level = "Low"    → Increase cash/bonds, reduce equity
```

**Allocation Targets by Risk Level:**
| Risk Level | Equity % | Bonds % | Cash % |
|------------|----------|---------|--------|
| High       | 70       | 15      | 15     |
| Medium     | 50       | 30      | 20     |
| Low        | 25       | 35      | 40     |

---

### Module 4: `agent/` — Autonomous Trading Agent

| File | Purpose |
|------|---------|
| `agent.py` | Main agent orchestrator — ties everything together |
| `rules.py` | Rule engine for buy/sell decision making |

**Agent Loop:**
```
1. Fetch mock news + social data
2. Run sentiment analysis on each item
3. Compute aggregate sentiment score
4. Determine risk level adjustment
5. Compare current allocation vs target allocation
6. Draft buy/sell orders to rebalance
7. Return strict JSON output
```

---

### Module 5: `config/` — Configuration

| File | Purpose |
|------|---------|
| `config.py` | API keys, model settings, thresholds |
| `constants.py` | Asset categories, risk thresholds |

---

## Output JSON (Strict Format)

```json
{
  "overall_sentiment": "Bullish",
  "sentiment_score": 0.65,
  "risk_adjustment": "Medium → High",
  "portfolio_action": "Increase equity exposure, reduce defensive assets",
  "orders": [
    {
      "action": "BUY",
      "asset": "AAPL",
      "reason": "Strong bullish sentiment on tech sector earnings"
    },
    {
      "action": "SELL",
      "asset": "TLT",
      "reason": "Reducing bond exposure due to positive market outlook"
    }
  ]
}
```

---

## File Structure (Final)

```
StockMarket/
├── PLAN.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── config.py
│   └── constants.py
├── data/
│   ├── __init__.py
│   ├── mock_news.py
│   ├── mock_social.py
│   └── scraper.py
├── sentiment/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── prompts.py
│   └── scorer.py
├── portfolio/
│   ├── __init__.py
│   ├── portfolio.py
│   ├── risk.py
│   └── orders.py
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   └── rules.py
├── app.py              ← Frontend entry point (frontend team)
└── main.py             ← Backend CLI entry point (us)
```

---

## Execution Order (Backend)

| Phase | Time | Task | Files |
|-------|------|------|-------|
| **1** | 1 hr | Config + Constants + Mock Data | `config/`, `data/mock_news.py`, `data/mock_social.py` |
| **2** | 2 hr | Sentiment Analyzer (LLM + scoring) | `sentiment/analyzer.py`, `prompts.py`, `scorer.py` |
| **3** | 2 hr | Portfolio Manager + Risk Engine | `portfolio/portfolio.py`, `risk.py`, `orders.py` |
| **4** | 1.5 hr | Agent Orchestrator + Rules | `agent/agent.py`, `rules.py` |
| **5** | 1 hr | `main.py` CLI + JSON output + testing | `main.py` |
| **6** | 0.5 hr | BeautifulSoup scraper (bonus) | `data/scraper.py` |
| **7** | — | Hand off to frontend team | `app.py` (frontend) |

**Total backend time: ~8 hours** (leaves 4 hours for frontend + integration + demo)

---

## Dependencies

```
beautifulsoup4
requests
google-generativeai   # or openai — whichever LLM we use
python-dotenv
```

---

## LLM Choice Decision

| Option | Pros | Cons |
|--------|------|------|
| **Gemini (Free tier)** | Free, fast, good for text | Rate limits |
| **OpenAI GPT** | Best quality | Costs money |
| **Local (TextBlob/VADER)** | No API needed, fast | Less accurate for finance |

**Recommendation:** Use Gemini free tier as primary + VADER/TextBlob as fallback (no API dependency).

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM API rate limits | Rule-based fallback with VADER |
| Time crunch | Mock data first, real scraping later |
| Integration issues | `main.py` returns clean JSON — frontend just consumes it |
| Scope creep | Stick to mock data, no real trading |

---

## What Frontend Team Needs From Us

1. `main.py` that returns the strict JSON output
2. Function: `run_agent(news, social_posts, portfolio, risk_level) → JSON`
3. Mock data generators they can call
4. Clear API contract (the JSON format above)

---

## Ready to Execute?

Once you confirm this plan, we start with **Phase 1: Config + Mock Data**.
