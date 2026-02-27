# Sentiment Trading Agent - Project Plan

## Timeline: 12 Hours Hackathon

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   STREAMLIT FRONTEND                │
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
├── app.py              ← Streamlit entry point (frontend team)
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
| **7** | — | Hand off to frontend team | `app.py` (Streamlit) |

**Total backend time: ~8 hours** (leaves 4 hours for frontend + integration + demo)

---

## Dependencies

```
beautifulsoup4
requests
google-generativeai   # or openai — whichever LLM we use
streamlit
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
