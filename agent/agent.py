"""
Autonomous Sentiment Trading Agent — the main orchestrator.
Ties together data fetching, sentiment analysis, risk adjustment, and order drafting.
"""

import json
from datetime import datetime

from data.mock_news import get_mock_news
from data.mock_social import get_mock_social_posts
from data.realtime_news import fetch_finnhub_news, fetch_company_news, fetch_newsapi_headlines, fetch_newsapi_for_ticker
from data.realtime_social import fetch_social_multiple
from data.scraper import scrape_reddit_titles

from sentiment.analyzer import SentimentAnalyzer
from portfolio.portfolio import PortfolioManager
from portfolio.risk import RiskEngine
from portfolio.orders import OrderDrafter
from config.config import DEFAULT_TICKERS


class TradingAgent:
    """
    Autonomous sentiment-driven trading agent.
    
    Pipeline:
    1. Fetch data (news + social) — real-time or mock
    2. Analyze sentiment (LLM + VADER)
    3. Compute aggregate market mood
    4. Adjust portfolio risk level
    5. Draft buy/sell orders
    6. Return strict JSON output
    """

    def __init__(self, portfolio: dict = None, use_realtime: bool = True):
        """
        Initialize the trading agent.
        
        Args:
            portfolio: Custom portfolio dict (or None for default)
            use_realtime: Whether to attempt real-time data fetching
        """
        self.portfolio_manager = PortfolioManager(portfolio)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_engine = RiskEngine()
        self.order_drafter = OrderDrafter()
        self.use_realtime = use_realtime

        print(f"[AGENT] Initialized | Risk: {self.portfolio_manager.risk_level} | Real-time: {use_realtime}")

    def run(self, tickers: list[str] = None) -> dict:
        """
        Execute the full trading agent pipeline.
        
        Args:
            tickers: List of tickers to monitor (default: DEFAULT_TICKERS)
        
        Returns:
            Strict JSON-serializable dict with trading decisions
        """
        if tickers is None:
            tickers = DEFAULT_TICKERS

        print("\n" + "=" * 60)
        print("  SENTIMENT TRADING AGENT — ANALYSIS RUN")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # ─── Step 1: Fetch Data ──────────────────────────────
        print("\n[1/5] Fetching market data...")
        news_data, social_data = self._fetch_data(tickers)
        print(f"       News items: {len(news_data)} | Social posts: {len(social_data)}")

        # ─── Step 2: Sentiment Analysis ──────────────────────
        print("\n[2/5] Running sentiment analysis...")
        news_sentiments = self.sentiment_analyzer.analyze_news(news_data)
        social_sentiments = self.sentiment_analyzer.analyze_social(social_data)
        aggregate = self.sentiment_analyzer.get_aggregate(news_sentiments, social_sentiments)
        print(f"       Overall: {aggregate['overall_sentiment']} (score: {aggregate['sentiment_score']})")

        # ─── Step 3: Fetch Live Prices ───────────────────────
        print("\n[3/5] Fetching portfolio prices...")
        self.portfolio_manager.fetch_live_prices()
        portfolio_summary = self.portfolio_manager.get_portfolio_summary()
        print(f"       Portfolio value: ${portfolio_summary['total_value']:,.2f}")

        # ─── Step 4: Risk Adjustment ─────────────────────────
        print("\n[4/5] Adjusting risk level...")
        risk_result = self.risk_engine.determine_risk_level(
            aggregate["sentiment_score"],
            self.portfolio_manager.risk_level,
        )
        rebalance = self.risk_engine.get_rebalance_actions(
            self.portfolio_manager.get_allocation(),
            risk_result["target_allocation"],
        )
        print(f"       Risk: {risk_result['adjustment']}")

        # ─── Step 5: Draft Orders ────────────────────────────
        print("\n[5/5] Drafting trading orders...")
        all_sentiments = news_sentiments + social_sentiments
        orders = self.order_drafter.draft_orders(
            risk_result, rebalance, portfolio_summary, all_sentiments
        )
        print(f"       Orders drafted: {len(orders)}")

        # ─── Build Output ────────────────────────────────────
        output = self._build_output(aggregate, risk_result, rebalance, orders, portfolio_summary)

        print("\n" + "=" * 60)
        print("  ANALYSIS COMPLETE")
        print("=" * 60)

        return output

    def _fetch_data(self, tickers: list[str]) -> tuple[list, list]:
        """Fetch news and social data — real-time with mock fallback."""
        news_data = []
        social_data = []

        if self.use_realtime:
            # Try real-time news from Finnhub
            news_data = fetch_finnhub_news()
            for ticker in tickers[:3]:  # Limit company news fetches
                news_data.extend(fetch_company_news(ticker, days_back=3))

            # Also fetch from NewsAPI (top headlines + ticker-specific)
            news_data.extend(fetch_newsapi_headlines(category="business"))
            news_data.extend(fetch_newsapi_headlines(category="technology", max_items=10))
            for ticker in tickers[:3]:
                news_data.extend(fetch_newsapi_for_ticker(ticker, days_back=3))

            # Deduplicate by headline (same headline from different sources)
            seen_headlines = set()
            unique_news = []
            for item in news_data:
                headline_key = item["headline"].strip().lower()[:80]
                if headline_key not in seen_headlines:
                    seen_headlines.add(headline_key)
                    unique_news.append(item)
            news_data = unique_news

            # Try real-time social (Reddit)
            social_data = fetch_social_multiple(tickers)

        # Fallback to mock if real-time returned nothing
        if not news_data:
            print("       [Fallback] Using mock news data")
            news_data = get_mock_news()
        if not social_data:
            print("       [Fallback] Using mock social data")
            social_data = get_mock_social_posts()

        return news_data, social_data

    def _build_output(
        self,
        aggregate: dict,
        risk_result: dict,
        rebalance: dict,
        orders: list[dict],
        portfolio_summary: dict,
    ) -> dict:
        """Build the strict JSON output format."""
        # Portfolio action summary
        if risk_result["new_risk"] == "High":
            action = "Increase equity exposure, reduce defensive assets"
        elif risk_result["new_risk"] == "Low":
            action = "Increase cash and bonds, reduce equity exposure"
        else:
            action = "Maintain balanced allocation with selective adjustments"

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_sentiment": aggregate["overall_sentiment"],
            "sentiment_score": aggregate["sentiment_score"],
            "risk_adjustment": risk_result["adjustment"],
            "new_risk_level": risk_result["new_risk"],
            "portfolio_action": action,
            "orders": orders,
            "analysis_details": {
                "total_items_analyzed": aggregate["total_analyzed"],
                "bullish_count": aggregate["bullish_count"],
                "bearish_count": aggregate["bearish_count"],
                "neutral_count": aggregate["neutral_count"],
                "rebalance_actions": rebalance["actions"],
            },
            "portfolio_snapshot": {
                "total_value": portfolio_summary["total_value"],
                "cash": portfolio_summary["cash"],
                "equity_pct": portfolio_summary["equity_pct"],
                "bonds_pct": portfolio_summary["bonds_pct"],
                "cash_pct": portfolio_summary["cash_pct"],
                "risk_level": risk_result["new_risk"],
            },
        }

    def get_output_json(self, tickers: list[str] = None) -> str:
        """Run agent and return formatted JSON string."""
        result = self.run(tickers)
        return json.dumps(result, indent=2)
