"""
Unified API layer — bridges the React frontend (via Flask) to the Python backend.

Usage:
    from api import TradingAPI
    api = TradingAPI()
    api.set_user_tickers(["AAPL", "TSLA", "NVDA"])
    api.set_user_portfolio(cash=50000, risk="Moderate")
    result = api.run_analysis()
    response = api.chat("Should I buy Tesla?")
"""

import json
from datetime import datetime
from agent.agent import TradingAgent
from agent.chatbot import TradingChatbot
from portfolio.portfolio import PortfolioManager
from config.config import DEFAULT_TICKERS, RISK_ALLOCATIONS


class TradingAPI:
    """
    Unified API for the Streamlit frontend.
    Manages state between auto-updates and user interactions.
    """

    def __init__(self):
        self._tickers = DEFAULT_TICKERS[:]
        self._cash = 50000.0
        self._risk_preference = "Medium"  # Low, Medium, High
        self._custom_portfolio = None
        self._agent = None
        self._chatbot = TradingChatbot()
        self._latest_result = None
        self._initialized = False
        # Per-ticker analysis cache — populated by analyze_ticker() calls
        # Shape: { "TCS.NS": { confidence: 76.9, recommendation: "BUY", ... } }
        self._ticker_analysis_cache: dict = {}
        # Ordered list of last 6 tickers analyzed on Dashboard (most recent first)
        self._recently_viewed: list = []

    # ─── Reset ────────────────────────────────────────────────

    def reset_results(self):
        """Clear cached analysis result so the next run starts fresh."""
        self._latest_result = None
        self._initialized = False
        self._agent = None

    # ─── User Setup ──────────────────────────────────────────

    def set_user_tickers(self, tickers: list[str]) -> dict:
        """
        Set which tickers the user wants to track.
        
        Args:
            tickers: List of stock symbols (e.g., ["AAPL", "TSLA", "NVDA"])
        
        Returns:
            Confirmation dict
        """
        # Clean and validate
        cleaned = [t.strip().upper() for t in tickers if t.strip()]
        if not cleaned:
            return {"success": False, "error": "Please provide at least one ticker"}
        if len(cleaned) > 10:
            return {"success": False, "error": "Maximum 10 tickers allowed"}

        self._tickers = cleaned
        self._agent = None  # Reset agent to pick up new tickers
        return {
            "success": True,
            "tickers": self._tickers,
            "message": f"Tracking {len(self._tickers)} stocks: {', '.join(self._tickers)}",
        }

    def set_user_portfolio(self, cash: float = 50000, risk: str = "Moderate") -> dict:
        """
        Set user's investment amount and risk preference.
        
        Args:
            cash: Starting cash amount
            risk: 'Conservative', 'Moderate', or 'Aggressive'
        
        Returns:
            Portfolio setup confirmation
        """
        # Validate
        if cash < 1000:
            return {"success": False, "error": "Minimum investment is $1,000"}
        if cash > 10_000_000:
            return {"success": False, "error": "Maximum investment is $10,000,000"}

        risk_map = {
            "conservative": "Low",
            "moderate": "Medium",
            "aggressive": "High",
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }
        risk_level = risk_map.get(risk.lower(), "Medium")

        self._cash = cash
        self._risk_preference = risk_level
        self._custom_portfolio = {
            "cash": cash,
            "holdings": {},  # Start fresh with just cash
        }
        self._agent = None  # Reset agent
        return {
            "success": True,
            "cash": cash,
            "risk_preference": risk,
            "risk_level": risk_level,
            "message": f"Portfolio set: ${cash:,.0f} with {risk} risk strategy",
        }

    def get_settings(self) -> dict:
        """Get current user settings."""
        # Map internal risk level back to lowercase for frontend
        risk_map = {"Low": "low", "Medium": "medium", "High": "high"}
        return {
            "tickers": self._tickers,
            "cash": self._cash,
            "risk_preference": risk_map.get(self._risk_preference, "medium"),
        }

    # ─── Analysis ────────────────────────────────────────────

    def run_analysis(self, use_mock: bool = False) -> dict:
        """
        Run the full sentiment analysis pipeline.
        
        Args:
            use_mock: Use mock data instead of real-time
        
        Returns:
            Complete analysis result dict
        """
        # Create agent with current settings
        agent = TradingAgent(
            portfolio=self._custom_portfolio,
            use_realtime=not use_mock,
        )

        # Override risk level if user set a preference
        if self._risk_preference:
            agent.portfolio_manager.risk_level = self._risk_preference

        # Run analysis
        result = agent.run(tickers=self._tickers)
        self._latest_result = result
        self._initialized = True
        return result

    def get_latest_result(self) -> dict:
        """Get the most recent analysis result (cached)."""
        if self._latest_result:
            return self._latest_result
        return {"error": "No analysis has been run yet. Call run_analysis() first."}

    # ─── Ticker-Specific Analysis ────────────────────────────

    def analyze_ticker(self, ticker: str) -> dict:
        """
        Get detailed sentiment analysis for a specific ticker.
        Returns a shape that exactly matches what the React AnalysisPanel expects.
        """
        from data.realtime_news import fetch_company_news, fetch_newsapi_for_ticker, fetch_newsdata_for_ticker
        from sentiment.analyzer import SentimentAnalyzer
        from backtest.universe_india import IndiaUniverse, normalise_ticker

        ticker = normalise_ticker(ticker.strip().upper())

        # ── 1. Look up company metadata from universe ──────────────────────
        u = IndiaUniverse()
        company_info = u.info(ticker) or {}
        company_name = company_info.get("name", ticker.replace(".NS", "").replace(".BO", ""))
        sector       = company_info.get("sector", "Unknown")
        exchange     = "NSE" if ticker.endswith(".NS") else "BSE" if ticker.endswith(".BO") else "NSE"

        # ── 2. Fetch news (pass company name for better NewsAPI search) ────
        news_raw = fetch_company_news(ticker, days_back=5)
        newsapi_raw = fetch_newsapi_for_ticker(
            ticker, days_back=5, max_items=20, company_name=company_name
        )
        newsdata_raw = fetch_newsdata_for_ticker(
            ticker, days_back=5, max_items=10, company_name=company_name
        )
        all_news_raw = news_raw + newsapi_raw + newsdata_raw

        # De-duplicate by headline text
        seen: set = set()
        unique_news: list = []
        for n in all_news_raw:
            h = (n.get("headline") or n.get("title") or "").strip().lower()
            if h and h not in seen:
                seen.add(h)
                unique_news.append(n)

        # ── Fallback to mock data if no real news found ────────────────────
        is_mock = False
        if not unique_news:
            from data.mock_news import get_mock_news_for_company
            unique_news = get_mock_news_for_company(ticker, company_name, sector, n=10)
            is_mock = True

        # ── 3. Sentiment analysis ──────────────────────────────────────────
        if unique_news:
            analyzer = SentimentAnalyzer()
            results  = analyzer.analyze_news(unique_news)
            agg      = analyzer.get_aggregate(results, [])
        else:
            # This branch is a safety net — normally mock data covers this
            results = []
            agg = {
                "overall_sentiment": "Neutral",
                "sentiment_score":   0.0,
                "total_analyzed":    0,
                "bullish_count":     0,
                "bearish_count":     0,
                "neutral_count":     0,
                "individual_results": [],
            }

        # ── 4. Build per-article news list for frontend ────────────────────
        indiv = agg.get("individual_results", results)

        news_out: list[dict] = []
        for i, item in enumerate(unique_news[:20]):
            art_result = indiv[i] if i < len(indiv) else {}
            art_score  = art_result.get("score", 0.0)
            art_sent   = art_result.get("sentiment",
                         "Bullish" if art_score > 0.05 else "Bearish" if art_score < -0.05 else "Neutral")
            news_out.append({
                "title":      item.get("headline") or item.get("title") or "Untitled",
                "source":     item.get("source", "Unknown"),
                "url":        item.get("url", ""),
                "score":      round(float(art_score), 4),
                "sentiment":  art_sent,
                "timestamp":  item.get("timestamp", ""),
            })

        # ── 5. Core metrics ────────────────────────────────────────────────
        score    = float(agg.get("sentiment_score", 0.0))
        label    = agg.get("overall_sentiment", "Neutral")
        bull     = int(agg.get("bullish_count", 0))
        bear     = int(agg.get("bearish_count", 0))
        flat     = int(agg.get("neutral_count", 0))
        total_hl = int(agg.get("total_analyzed", 0))

        # ── 6. Recommendation ──────────────────────────────────────────────
        if score >= 0.3:
            rec_str = "STRONG BUY"
        elif score >= 0.1:
            rec_str = "BUY"
        elif score <= -0.3:
            rec_str = "STRONG SELL"
        elif score <= -0.1:
            rec_str = "SELL"
        else:
            rec_str = "HOLD"

        # ── 7. Confidence ──────────────────────────────────────────────────
        # Confidence = abs(score) mapped to 50-95% range + bonus for article count
        base_conf      = min(abs(score) * 150, 45.0)       # 0.0→0%, 0.3→45%
        article_bonus  = min(total_hl * 1.5, 15.0)         # up to +15% for 10+ articles
        mock_penalty   = -20.0 if is_mock else 0.0          # penalty when showing simulated data
        confidence     = round(max(50.0 + base_conf + article_bonus + mock_penalty, 10.0), 1)

        # ── 8. Risk level from user settings ──────────────────────────────
        risk_level = self._risk_preference.capitalize() if hasattr(self, '_risk_preference') else "Medium"

        # ── 9. Portfolio allocation hint ───────────────────────────────────
        try:
            capital   = float(self._cash) if hasattr(self, '_cash') else 50000.0
            n         = max(len(self._tickers), 1) if hasattr(self, '_tickers') else 5
            risk_mult = {"Low": 0.5, "Medium": 1.0, "High": 1.5}.get(risk_level, 1.0)
            alloc_pct = min((confidence / 100.0) * risk_mult * (1.0 / n) * 100.0, 20.0)
            alloc_inr = round(capital * alloc_pct / 100.0, 2)
        except Exception:
            alloc_pct = 0.0
            alloc_inr = 0.0

        # ── 10. Live price ─────────────────────────────────────────────────
        current_price = None
        try:
            import yfinance as yf
            stock      = yf.Ticker(ticker)
            price_data = stock.history(period="1d")
            if not price_data.empty:
                current_price = round(float(price_data["Close"].iloc[-1]), 2)
        except Exception:
            pass

        # ── 11. AI explanation (build a simple template one) ───────────────
        if is_mock:
            explained = (
                f"Analysis based on {total_hl} simulated news articles for {company_name} "
                f"(live news APIs returned no results). "
                f"Sentiment: {label} ({score:+.3f}). "
                f"{bull} bullish, {bear} bearish, {flat} neutral signals. "
                f"Note: Connect Finnhub/NewsAPI keys for live data."
            )
        else:
            explained = (
                f"Based on {total_hl} live articles, {company_name} shows "
                f"{label.lower()} sentiment (score: {score:+.3f}). "
                f"{bull} bullish, {bear} bearish, {flat} neutral headlines."
            )

        # ── Cache result for Portfolio engine (BEFORE returning) ──────────
        self._ticker_analysis_cache[ticker] = {
            "confidence":     confidence,          # 0-100 scale
            "recommendation": rec_str,
            "sentiment":      label,
            "score":          score,
            "name":           company_name,
            "sector":         sector,
            "bull":           bull,
            "bear":           bear,
            "neutral":        flat,
            "total":          total_hl,
            "is_mock":        is_mock,
            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # ── Track recently viewed (last 6, most recent first) ─────────────
        if ticker in self._recently_viewed:
            self._recently_viewed.remove(ticker)
        self._recently_viewed.insert(0, ticker)
        self._recently_viewed = self._recently_viewed[:6]

        # ── Return exactly what the React AnalysisPanel reads ─────────────
        return {
            # Company identity
            "ticker":       ticker,
            "name":         company_name,
            "sector":       sector,
            "exchange":     exchange,

            # Flat score fields (fallback reads)
            "score":        score,
            "label":        label,
            "bullish":      bull,
            "bearish":      bear,
            "neutral":      flat,

            # Structured sentiment object (primary reads)
            "sentiment": {
                "score":            score,
                "label":            label,
                "positive":         bull,
                "negative":         bear,
                "neutral":          flat,
                "total_headlines":  total_hl,
            },

            # Recommendation + confidence
            "recommendation": rec_str,
            "confidence":     confidence,
            "explanation":    explained,

            # Risk & allocation
            "risk_level":  risk_level,
            "allocation": {
                "suggested_pct":    round(alloc_pct, 1),
                "suggested_amount": alloc_inr,
            },

            # News articles
            "news": news_out,

            # Price
            "current_price":    current_price,
            "articles_analyzed": total_hl,
            "has_news":          len(unique_news) > 0,
            "is_mock_data":      is_mock,

            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def analyze_portfolio_tickers(self) -> dict:
        """
        Run analyze_ticker() on all tickers in the current watchlist.
        Results are saved to _ticker_analysis_cache.
        Returns a summary of results.
        """
        results = {}
        errors  = {}
        for ticker in self._tickers:
            try:
                r = self.analyze_ticker(ticker)
                results[ticker] = {
                    "ok":             True,
                    "recommendation": r.get("recommendation", "HOLD"),
                    "confidence":     r.get("confidence", 50.0),
                    "sentiment":      r.get("label", "Neutral"),
                    "score":          r.get("score", 0.0),
                    "is_mock":        r.get("is_mock_data", False),
                }
            except Exception as e:
                errors[ticker] = str(e)
        return {
            "analyzed":  list(results.keys()),
            "failed":    list(errors.keys()),
            "results":   results,
            "errors":    errors,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def clear_ticker_cache(self):
        """Clear the per-ticker analysis cache."""
        self._ticker_analysis_cache = {}

    # ─── Chatbot ─────────────────────────────────────────────

    def chat(self, question: str) -> dict:
        """
        Ask the AI trading advisor a question.
        Passes both global market data and per-ticker Dashboard cache so the
        chatbot can answer questions about any stock the user has analysed.
        """
        return self._chatbot.ask(
            question,
            market_data=self._latest_result,
            ticker_cache=self._ticker_analysis_cache,
            recently_viewed=self._recently_viewed,
        )

    def get_chat_history(self) -> list:
        """Get conversation history."""
        return self._chatbot.conversation_history

    def clear_chat(self):
        """Clear conversation history."""
        self._chatbot.clear_history()

    # ─── Summary for Display ─────────────────────────────────

    def get_dashboard_data(self) -> dict:
        """
        Get all data needed for the dashboard in one call.
        Returns a flat shape matching what the React Dashboard expects.
        """
        result = self._latest_result or {}
        details = result.get("analysis_details", {})
        snapshot = result.get("portfolio_snapshot", {})
        risk_map = {"Low": "low", "Medium": "medium", "High": "high"}

        return {
            "status": "ok" if self._initialized else "empty",
            "tickers": self._tickers,
            "cash": self._cash,
            "risk_preference": risk_map.get(
                result.get("new_risk_level", self._risk_preference), "medium"
            ),
            "sentiment": {
                "score": result.get("sentiment_score", 0),
                "label": result.get("overall_sentiment", "N/A"),
                "total_headlines": details.get("total_items_analyzed", 0),
                "positive": details.get("bullish_count", 0),
                "negative": details.get("bearish_count", 0),
                "neutral": details.get("neutral_count", 0),
            },
            "allocation": snapshot,
            "orders": result.get("orders", []),
            "ticker_sentiments": {},
            "timestamp": result.get("timestamp", "Never"),
        }

    def get_portfolio_allocations(self) -> dict:
        """
        Compute per-ticker INR allocations using:
          allocation_pct = (confidence/100) × risk_multiplier × (1 / n_positions)
          capped at 20% max single position.

        Data priority:
          1. _ticker_analysis_cache  (populated by analyze_ticker()  — most fresh)
          2. _latest_result orders   (populated by run_analysis() — full pipeline)
          3. Defaults: confidence=50%, sentiment=Neutral, rec=HOLD
        """
        risk_mult_map = {"Low": 0.5, "Medium": 1.0, "High": 1.5}
        rk = risk_mult_map.get(self._risk_preference, 1.0)
        n  = max(len(self._tickers), 1)

        # Secondary source: full pipeline orders
        pipeline_map: dict = {}
        if self._latest_result:
            for order in self._latest_result.get("orders", []):
                t = order.get("ticker", "")
                if t:
                    pipeline_map[t] = order

        allocations = []
        for ticker in self._tickers:
            # 1. Try per-ticker cache (most recent individual analysis)
            cached = self._ticker_analysis_cache.get(ticker)
            if cached:
                # confidence stored as 0-100 scale from analyze_ticker()
                confidence_01  = max(0.0, min(1.0, cached["confidence"] / 100.0))
                sentiment_label = cached.get("sentiment", "Neutral")
                score           = cached.get("score", 0.0)
                recommendation  = cached.get("recommendation", "HOLD")
                is_mock         = cached.get("is_mock", False)
                analyzed_at     = cached.get("timestamp", None)
                name            = cached.get("name", ticker.replace(".NS", ""))
                sector          = cached.get("sector", "")
            else:
                # 2. Fall back to pipeline orders
                pipe = pipeline_map.get(ticker, {})
                # pipeline stores confidence 0-1
                confidence_01  = abs(pipe.get("confidence", 0.5))
                sentiment_label = pipe.get("sentiment", "Neutral")
                score           = pipe.get("score", 0.0)
                recommendation  = pipe.get("action", "HOLD")
                is_mock         = False
                analyzed_at     = None
                # Try to get name from universe
                try:
                    from backtest.universe_india import IndiaUniverse
                    name   = IndiaUniverse().name(ticker) or ticker.replace(".NS", "")
                    sector = IndiaUniverse().sector(ticker)
                except Exception:
                    name   = ticker.replace(".NS", "")
                    sector = ""

            raw_pct    = confidence_01 * rk * (1.0 / n)
            capped_pct = min(raw_pct, 0.20)
            amount     = self._cash * capped_pct

            allocations.append({
                "ticker":         ticker,
                "name":           name,
                "sector":         sector,
                "confidence":     round(confidence_01, 4),    # 0-1 for ConfidenceBar
                "sentiment":      sentiment_label,
                "score":          round(score, 4),
                "recommendation": recommendation,
                "allocation_pct": round(capped_pct * 100, 2),
                "allocation_inr": round(amount, 2),
                "capped":         raw_pct > 0.20,
                "is_mock":        is_mock,
                "analyzed_at":    analyzed_at,
                "has_analysis":   cached is not None,
            })

        total_allocated = sum(a["allocation_inr"] for a in allocations)
        has_any_analysis = any(a["has_analysis"] for a in allocations)

        # ── Filter to recently viewed (last 6) for portfolio display ──────
        recent = self._recently_viewed  # ordered list, most recent first
        recent_allocations = [a for a in allocations if a["ticker"] in recent]
        # preserve recent-first order
        recent_allocations.sort(key=lambda a: recent.index(a["ticker"]) if a["ticker"] in recent else 99)
        recent_total = sum(a["allocation_inr"] for a in recent_allocations)

        return {
            "capital":        self._cash,
            "risk":           self._risk_preference.lower(),
            "risk_multiplier": rk,
            "n_positions":    n,
            "allocations":    allocations,
            "recent_allocations": recent_allocations,
            "recently_viewed":    recent,
            "recent_total":       round(recent_total, 2),
            "total_allocated": round(total_allocated, 2),
            "available_cash": round(self._cash - total_allocated, 2),
            "has_analysis":   has_any_analysis,
            "tickers":        list(self._tickers),
            "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cache_keys":     list(self._ticker_analysis_cache.keys()),
        }

    @staticmethod
    def _score_to_label(score: float) -> str:
        """Convert sentiment score to human label."""
        if score >= 0.5:
            return "Strong Bullish 🟢🟢"
        elif score >= 0.2:
            return "Bullish 🟢"
        elif score > -0.2:
            return "Neutral ⚪"
        elif score > -0.5:
            return "Bearish 🔴"
        else:
            return "Strong Bearish 🔴🔴"
