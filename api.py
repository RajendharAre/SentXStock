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
        self._risk_preference = "Medium"  # Conservative, Moderate, Aggressive
        self._custom_portfolio = None
        self._agent = None
        self._chatbot = TradingChatbot()
        self._latest_result = None
        self._initialized = False

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
        from data.realtime_news import fetch_company_news, fetch_newsapi_for_ticker
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
        all_news_raw = news_raw + newsapi_raw

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

    # ─── Chatbot ─────────────────────────────────────────────

    def chat(self, question: str) -> dict:
        """
        Ask the AI trading advisor a question.
        
        Args:
            question: User's question (e.g., "Should I buy AAPL?")
        
        Returns:
            dict with 'answer', 'timestamp', 'method'
        """
        return self._chatbot.ask(question, self._latest_result)

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
          allocation_pct = confidence × risk_multiplier × (1 / n_positions)
          capped at 20% max single position.
        If no analysis has run, confidence defaults to 0.5 (neutral).
        """
        risk_mult_map = {"Low": 0.5, "Medium": 1.0, "High": 1.5}
        rk = risk_mult_map.get(self._risk_preference, 1.0)
        n = max(len(self._tickers), 1)

        # Pull last known per-ticker sentiment from latest result (if any)
        ticker_data_map = {}
        if self._latest_result:
            for order in self._latest_result.get("orders", []):
                t = order.get("ticker", "")
                if t:
                    ticker_data_map[t] = order

        allocations = []
        for ticker in self._tickers:
            tdata = ticker_data_map.get(ticker, {})
            # confidence: 0–1; default 0.5 if no analysis
            confidence = abs(tdata.get("confidence", 0.5))
            sentiment_label = tdata.get("sentiment", "Neutral")
            score = tdata.get("score", 0.0)
            recommendation = tdata.get("action", "HOLD")

            raw_pct = confidence * rk * (1.0 / n)
            capped_pct = min(raw_pct, 0.20)
            amount = self._cash * capped_pct

            allocations.append({
                "ticker": ticker,
                "confidence": round(confidence, 4),
                "sentiment": sentiment_label,
                "score": round(score, 4),
                "recommendation": recommendation,
                "allocation_pct": round(capped_pct * 100, 2),
                "allocation_inr": round(amount, 2),
                "capped": raw_pct > 0.20,
            })

        total_allocated = sum(a["allocation_inr"] for a in allocations)
        return {
            "capital": self._cash,
            "risk": self._risk_preference.lower(),
            "risk_multiplier": rk,
            "n_positions": n,
            "allocations": allocations,
            "total_allocated": round(total_allocated, 2),
            "available_cash": round(self._cash - total_allocated, 2),
            "has_analysis": self._initialized,
            "timestamp": self._latest_result.get("timestamp", None) if self._latest_result else None,
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
