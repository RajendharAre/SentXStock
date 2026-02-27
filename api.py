"""
Unified API layer for the Streamlit frontend.
Provides all the functions needed for both automated dashboard and user interactions.

Usage in Streamlit:
    from api import TradingAPI
    api = TradingAPI()
    
    # Auto mode
    result = api.run_analysis()
    
    # User interaction
    api.set_user_tickers(["AAPL", "TSLA", "NVDA"])
    api.set_user_portfolio(cash=50000, risk="Moderate")
    result = api.run_analysis()
    
    # Chatbot
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
        return {
            "tickers": self._tickers,
            "cash": self._cash,
            "risk_preference": self._risk_preference,
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
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
        
        Returns:
            Detailed sentiment breakdown for the ticker
        """
        from data.realtime_news import fetch_company_news, fetch_newsapi_for_ticker
        from sentiment.analyzer import SentimentAnalyzer

        ticker = ticker.strip().upper()

        # Fetch ticker-specific news
        news = fetch_company_news(ticker, days_back=3)
        newsapi_news = fetch_newsapi_for_ticker(ticker, days_back=3, max_items=15)
        news.extend(newsapi_news)

        if not news:
            return {
                "ticker": ticker,
                "error": f"No recent news found for {ticker}",
                "recommendation": "HOLD — insufficient data for analysis",
            }

        # Analyze sentiment
        analyzer = SentimentAnalyzer()
        results = analyzer.analyze_news(news)
        aggregate = analyzer.get_aggregate(results, [])

        # Generate recommendation
        score = aggregate["sentiment_score"]
        if score >= 0.3:
            recommendation = f"BUY — Bullish sentiment ({score:.2f}) based on {len(results)} articles"
        elif score <= -0.3:
            recommendation = f"SELL — Bearish sentiment ({score:.2f}) based on {len(results)} articles"
        else:
            recommendation = f"HOLD — Neutral sentiment ({score:.2f}) based on {len(results)} articles"

        # Get live price
        import yfinance as yf
        try:
            stock = yf.Ticker(ticker)
            price_data = stock.history(period="1d")
            current_price = round(float(price_data["Close"].iloc[-1]), 2) if not price_data.empty else None
        except Exception:
            current_price = None

        return {
            "ticker": ticker,
            "current_price": current_price,
            "sentiment": aggregate["overall_sentiment"],
            "sentiment_score": aggregate["sentiment_score"],
            "recommendation": recommendation,
            "articles_analyzed": len(results),
            "bullish_count": aggregate["bullish_count"],
            "bearish_count": aggregate["bearish_count"],
            "neutral_count": aggregate["neutral_count"],
            "top_headlines": [
                {"headline": n.get("headline", ""), "source": n.get("source", "")}
                for n in news[:5]
            ],
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
        Combines latest analysis + settings + chat history.
        """
        result = self._latest_result or {}

        return {
            "has_data": self._initialized,
            "settings": self.get_settings(),
            "sentiment": {
                "overall": result.get("overall_sentiment", "N/A"),
                "score": result.get("sentiment_score", 0),
                "level": self._score_to_label(result.get("sentiment_score", 0)),
            },
            "risk_level": result.get("new_risk_level", self._risk_preference),
            "portfolio": result.get("portfolio_snapshot", {}),
            "orders": result.get("orders", []),
            "analysis": result.get("analysis_details", {}),
            "timestamp": result.get("timestamp", "Never"),
            "chat_history": self.get_chat_history(),
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
