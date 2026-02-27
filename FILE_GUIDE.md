# SentXStock — File Guide
> ~100-character description of every source file in the project.  
> Intended for team members to quickly understand the codebase at a glance.

---

## Root

| File | Description |
|------|-------------|
| `.env` | Secret API keys (Finnhub, NewsAPI, Gemini, NewsData.io). **Never commit.** |
| `.env.example` | Template listing all required env variables. Copy → `.env` and fill in values. |
| `.gitignore` | Tells Git to ignore `.env`, `node_modules`, `dist`, `__pycache__`, `.venv`, etc. |
| `api.py` | Unified Python API layer bridging the React frontend to the backend analysis engine. |
| `main.py` | Standalone CLI entry point — runs a full analysis without needing the Flask server. |
| `output.json` | Cached JSON of the last completed full-market analysis (used for quick page reload). |
| `output_realtime.json` | Cached JSON of the last real-time analysis run saved for fast state restoration. |
| `PLAN.md` | Internal dev roadmap: feature ideas, technical decisions, and sprint planning notes. |
| `README.md` | Project overview, environment setup steps, and usage guide for new developers. |
| `requirements.txt` | Python package list: Flask, transformers, yfinance, google-genai, torch, etc. |
| `server.py` | Flask REST API server — exposes all endpoints consumed by the React frontend. |
| `streamlit_app.py` | Legacy Streamlit UI entry point; superseded by the React + Flask frontend. |
| `test_api.py` | Dev script to smoke-test Flask API endpoints and verify correct JSON responses. |
| `test_gemini.py` | Dev script to check Gemini API key validity, quota, and model availability. |
| `test_mock.json` | Sample mock payload used in API tests to simulate backend analysis output. |

---

## `agent/`
> Core AI engine components

| File | Description |
|------|-------------|
| `agent.py` | Main orchestrator: fetch data → sentiment → risk adjustment → draft orders pipeline. |
| `chatbot.py` | AI trading chatbot: answers questions using Dashboard cache + yfinance live fallback. |
| `__init__.py` | Package init for the `agent` module. |

---

## `backtest/`
> Historical strategy simulation engine

| File | Description |
|------|-------------|
| `data_loader.py` | Downloads and caches historical OHLCV price data from Yahoo Finance (Parquet format). |
| `engine.py` | Core backtest loop: iterates over trading days, applies strategy, tracks open positions. |
| `metrics.py` | Computes performance stats: Sharpe ratio, CAGR, max drawdown, win-rate, volatility. |
| `report.py` | Serialises completed backtest results to timestamped JSON in `backtest/results/`. |
| `runner.py` | Public API entry point: wires data_loader + engine + metrics + report into one call. |
| `strategy.py` | Trading strategy definitions: sentiment-threshold, momentum, RSI, and hybrid signals. |
| `universe.py` | Global stock universe — S&P 500 ticker list used for US-focused backtesting. |
| `universe_india.py` | Indian stock universe — NSE 200+ tickers used for India-focused backtesting. |
| `__init__.py` | Package init for the `backtest` module. |

---

## `config/`
> Centralised configuration

| File | Description |
|------|-------------|
| `config.py` | Loads `.env` keys, sets defaults, defines model names, risk allocations, and constants. |
| `__init__.py` | Package init for the `config` module. |

---

## `data/`
> Data ingestion layer — live APIs and mock fallbacks

| File | Description |
|------|-------------|
| `mock_news.py` | Generates sector-tagged dummy news articles when live news APIs are unavailable. |
| `mock_social.py` | Generates fake Reddit-style social posts for offline testing without API calls. |
| `realtime_news.py` | Fetches live headlines from Finnhub, NewsAPI, and NewsData.io REST APIs. |
| `realtime_social.py` | Fetches live social sentiment via Finnhub API and Reddit public JSON endpoints. |
| `scraper.py` | Legacy HTML scraper for Reddit (dead code — replaced by `realtime_social.py`). |
| `__init__.py` | Package init for the `data` module. |

---

## `portfolio/`
> Portfolio management and risk logic

| File | Description |
|------|-------------|
| `orders.py` | Drafts BUY/SELL orders from sentiment signals using risk-adjusted position sizing. |
| `portfolio.py` | Portfolio manager — tracks holdings, cash balance, allocations, and P&L snapshot. |
| `risk.py` | Risk engine: maps sentiment scores to Low/Medium/High risk levels and position sizes. |
| `__init__.py` | Package init for the `portfolio` module. |

---

## `sentiment/`
> NLP/ML sentiment analysis pipeline

| File | Description |
|------|-------------|
| `analyzer.py` | Core analyser: Gemini LLM primary with VADER fallback + multi-key rotation on quota. |
| `finbert.py` | Local FinBERT model (ProsusAI/finbert) for offline financial-text classification. |
| `prompts.py` | Prompt templates for single-headline and batch sentiment Gemini LLM requests. |
| `scorer.py` | Aggregates per-headline sentiment scores into composite bullish/bearish signals. |
| `__init__.py` | Package init for the `sentiment` module. |

---

## `scripts/`
> Utility and maintenance scripts

| File | Description |
|------|-------------|
| `download_datasets.py` | Bulk-downloads global stock price histories from Yahoo Finance for backtesting. |
| `download_india_datasets.py` | Bulk-downloads NSE India stock price histories from Yahoo Finance. |
| `_bt_audit.py` | Audit script that validates backtest result files for correctness and data quality. |

---

## `st_pages/` *(Legacy — superseded by React frontend)*

| File | Description |
|------|-------------|
| `chat.py` | Legacy Streamlit chat page — replaced by `frontend/src/pages/Chat.jsx`. |
| `dashboard.py` | Legacy Streamlit dashboard — replaced by `frontend/src/pages/Dashboard.jsx`. |
| `settings.py` | Legacy Streamlit settings page — replaced by `frontend/src/pages/Settings.jsx`. |
| `__init__.py` | Package init for the `st_pages` module. |

---

## `frontend/` — React + Vite + Tailwind UI

### Root Config

| File | Description |
|------|-------------|
| `index.html` | HTML shell with logo favicon and Vite script tag that bootstraps the React app. |
| `package.json` | Node project manifest listing React, Tailwind, Recharts, Lucide, and Vite deps. |
| `vite.config.js` | Vite config: React plugin + dev-server proxy forwarding `/api` to Flask on port 5000. |
| `eslint.config.js` | ESLint rules for code quality and style consistency across React JSX files. |

### `frontend/src/`

| File | Description |
|------|-------------|
| `App.jsx` | Root component: wraps Router + ThemeProvider and declares all seven page routes. |
| `main.jsx` | React entry point — mounts `<App />` into the `#root` div in `index.html`. |
| `index.css` | Global styles: Tailwind base imports + CSS custom properties for dark/light themes. |

### `frontend/src/components/`

| File | Description |
|------|-------------|
| `Navbar.jsx` | Sticky top nav with SentXStock logo, page links, and dark/light mode toggle button. |
| `OrderCards.jsx` | Renders BUY/SELL signal cards with ticker, strength, confidence, and reasoning text. |
| `PDFReport.jsx` | Generates and downloads a formatted PDF analysis report for the selected stock. |
| `PortfolioChart.jsx` | Recharts pie/bar chart showing equity, bonds, and cash allocation percentages. |
| `RiskLevel.jsx` | Coloured badge/meter displaying current risk level: Low (green), Medium, High (red). |
| `SentimentGauge.jsx` | Animated arc gauge that visually shows the overall market bullish/bearish score. |

### `frontend/src/context/`

| File | Description |
|------|-------------|
| `ThemeContext.jsx` | React context that provides dark/light mode state and `toggleTheme()` to all pages. |

### `frontend/src/pages/`

| File | Description |
|------|-------------|
| `Home.jsx` | Landing page: platform overview, feature highlights, market stats, and quick-start CTAs. |
| `Dashboard.jsx` | Core analysis page: search a stock, trigger real-time sentiment analysis, view results. |
| `Portfolio.jsx` | Portfolio overview: allocation charts, risk metrics, and per-stock rebalancing signals. |
| `Chat.jsx` | AI advisor chat page: live conversation interface with the SentX trading chatbot. |
| `Consult.jsx` | 4-step SEBI expert booking: choose advisor → session & time → details → payment. |
| `Backtest.jsx` | Backtest UI: select strategy + date range, run simulation, view equity-curve charts. |
| `Settings.jsx` | Settings page: configure tickers, risk tolerance, API keys, and theme preferences. |

### `frontend/src/services/`

| File | Description |
|------|-------------|
| `api.js` | Axios client — defines all functions that call Flask REST endpoints from the UI. |

### `frontend/public/`

| File | Description |
|------|-------------|
| `logo.png` | SentXStock brand logo displayed in Navbar header and used as the browser favicon. |
| `hero-chart.png` | Decorative chart image shown in the Home page hero/banner section. |

---

## `backtest/results/`
> Auto-generated JSON reports from each backtest run. Named by timestamp + short UUID.  
> Not hand-edited. Consumed by `Backtest.jsx` to display historical run comparisons.

## `backtest/cache/prices/`
> Parquet files of cached OHLCV price data downloaded by `data_loader.py`.  
> Speeds up repeated backtests — avoids re-downloading the same ticker history.

## `datasets/`
> Empty placeholder directories for bulk-downloaded price and sentiment CSV datasets.  
> Populated by `scripts/download_datasets.py` and `scripts/download_india_datasets.py`.
