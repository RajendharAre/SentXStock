"""
Order Drafter — generates buy/sell orders based on risk adjustment and sentiment.
Deterministic, rule-based order generation with clear reasoning.
"""

from config.config import EQUITY_ASSETS, BOND_ASSETS


class OrderDrafter:
    """
    Drafts buy/sell orders based on sentiment analysis and portfolio rebalancing needs.
    All decisions are rule-based and deterministic.
    """

    def draft_orders(
        self,
        risk_result: dict,
        rebalance_actions: dict,
        portfolio_details: dict,
        sentiment_results: list[dict],
    ) -> list[dict]:
        """
        Draft buy/sell orders based on risk adjustment and individual sentiments.
        
        Logic:
        1. If risk increased (→ High): BUY equities with best sentiment, SELL bonds
        2. If risk decreased (→ Low): SELL equities with worst sentiment, BUY bonds/hold cash
        3. If risk unchanged (Medium): Rebalance based on individual stock sentiments
        
        Args:
            risk_result: Output from RiskEngine.determine_risk_level()
            rebalance_actions: Output from RiskEngine.get_rebalance_actions()
            portfolio_details: Current holdings detail from PortfolioManager
            sentiment_results: Individual sentiment analysis results
        
        Returns:
            List of order dicts with action, asset, and reason
        """
        orders = []
        new_risk = risk_result["new_risk"]
        risk_changed = risk_result["risk_changed"]
        holdings = portfolio_details.get("holdings", {})

        # Build ticker sentiment map from social/news results
        ticker_sentiment = self._build_ticker_sentiment(sentiment_results)

        if new_risk == "High":
            orders.extend(self._aggressive_orders(holdings, ticker_sentiment, risk_changed))
        elif new_risk == "Low":
            orders.extend(self._defensive_orders(holdings, ticker_sentiment, risk_changed))
        else:
            orders.extend(self._balanced_orders(holdings, ticker_sentiment, rebalance_actions))

        # Deduplicate and limit orders
        orders = self._deduplicate_orders(orders)
        return orders[:8]  # Cap at 8 orders max

    def _aggressive_orders(
        self, holdings: dict, ticker_sentiment: dict, risk_changed: bool
    ) -> list[dict]:
        """Generate orders for High risk (bullish) scenario."""
        orders = []

        # Sell bonds / defensive assets
        for ticker, info in holdings.items():
            if info.get("type") in ("bonds", "defensive"):
                orders.append({
                    "action": "SELL",
                    "asset": ticker,
                    "reason": f"Reducing defensive position in {ticker} — strong bullish sentiment, shifting to equities",
                })

        # Buy equities with strongest sentiment
        best_tickers = sorted(
            ticker_sentiment.items(), key=lambda x: x[1], reverse=True
        )
        for ticker, score in best_tickers[:3]:
            if ticker in EQUITY_ASSETS and score > 0.2:
                if ticker in holdings:
                    orders.append({
                        "action": "BUY",
                        "asset": ticker,
                        "reason": f"Adding to {ticker} position — positive sentiment (score: {score:.2f}), increasing equity exposure",
                    })
                else:
                    orders.append({
                        "action": "BUY",
                        "asset": ticker,
                        "reason": f"Opening new position in {ticker} — bullish sentiment (score: {score:.2f}), market outlook favorable",
                    })

        # If no strong individual picks, buy broad market
        if not any(o["action"] == "BUY" for o in orders):
            orders.append({
                "action": "BUY",
                "asset": "SPY",
                "reason": "Increasing broad market equity exposure — overall bullish sentiment",
            })

        return orders

    def _defensive_orders(
        self, holdings: dict, ticker_sentiment: dict, risk_changed: bool
    ) -> list[dict]:
        """Generate orders for Low risk (bearish) scenario."""
        orders = []

        # Sell equities with worst sentiment
        worst_tickers = sorted(ticker_sentiment.items(), key=lambda x: x[1])
        for ticker, score in worst_tickers[:3]:
            if ticker in holdings and holdings[ticker].get("type") == "equity" and score < -0.1:
                orders.append({
                    "action": "SELL",
                    "asset": ticker,
                    "reason": f"Reducing {ticker} exposure — bearish sentiment (score: {score:.2f}), cutting risk",
                })

        # Sell equities that are in portfolio (general risk reduction)
        for ticker, info in holdings.items():
            if info.get("type") == "equity" and ticker not in [o["asset"] for o in orders]:
                orders.append({
                    "action": "SELL",
                    "asset": ticker,
                    "reason": f"Reducing equity exposure in {ticker} — shifting to defensive allocation",
                })

        # Buy bonds / defensive assets
        if "TLT" in holdings:
            orders.append({
                "action": "BUY",
                "asset": "TLT",
                "reason": "Increasing bond allocation — bearish sentiment, seeking safety",
            })
        else:
            orders.append({
                "action": "BUY",
                "asset": "TLT",
                "reason": "Opening bond position (TLT) — bearish outlook, defensive positioning",
            })

        return orders

    def _balanced_orders(
        self, holdings: dict, ticker_sentiment: dict, rebalance_actions: dict
    ) -> list[dict]:
        """Generate orders for Medium risk (neutral) scenario."""
        orders = []
        equity_diff = rebalance_actions.get("equity_diff", 0)

        # If we need more equity
        if equity_diff > 2:
            best = sorted(ticker_sentiment.items(), key=lambda x: x[1], reverse=True)
            for ticker, score in best[:2]:
                if ticker in EQUITY_ASSETS and score > 0:
                    orders.append({
                        "action": "BUY",
                        "asset": ticker,
                        "reason": f"Rebalancing: adding {ticker} — moderate positive sentiment (score: {score:.2f})",
                    })

        # If we need less equity
        elif equity_diff < -2:
            worst = sorted(ticker_sentiment.items(), key=lambda x: x[1])
            for ticker, score in worst[:2]:
                if ticker in holdings and holdings[ticker].get("type") == "equity":
                    orders.append({
                        "action": "SELL",
                        "asset": ticker,
                        "reason": f"Rebalancing: trimming {ticker} — weaker sentiment (score: {score:.2f})",
                    })

        # If balanced, make sentiment-driven adjustments on individual stocks
        if not orders:
            for ticker, score in ticker_sentiment.items():
                if score > 0.5 and ticker in EQUITY_ASSETS:
                    orders.append({
                        "action": "BUY",
                        "asset": ticker,
                        "reason": f"Opportunistic buy on {ticker} — strong positive sentiment (score: {score:.2f})",
                    })
                elif score < -0.5 and ticker in holdings:
                    orders.append({
                        "action": "SELL",
                        "asset": ticker,
                        "reason": f"Risk trim on {ticker} — strong negative sentiment (score: {score:.2f})",
                    })

        if not orders:
            orders.append({
                "action": "HOLD",
                "asset": "ALL",
                "reason": "Portfolio within target allocation, sentiment neutral — no action needed",
            })

        return orders

    def _build_ticker_sentiment(self, sentiment_results: list[dict]) -> dict:
        """
        Build a map of ticker -> average sentiment score from analysis results.
        """
        ticker_scores = {}
        for result in sentiment_results:
            ticker = result.get("ticker", "")
            if ticker:
                if ticker not in ticker_scores:
                    ticker_scores[ticker] = []
                ticker_scores[ticker].append(result.get("score", 0.0))

        # Also extract tickers from text for news without explicit ticker tags
        for result in sentiment_results:
            text = result.get("text", "") or result.get("headline", "")
            score = result.get("score", 0.0)
            for t in EQUITY_ASSETS:
                if t in text or f"${t}" in text:
                    if t not in ticker_scores:
                        ticker_scores[t] = []
                    ticker_scores[t].append(score)

        # Average the scores
        return {
            ticker: round(sum(scores) / len(scores), 4)
            for ticker, scores in ticker_scores.items()
            if scores
        }

    def _deduplicate_orders(self, orders: list[dict]) -> list[dict]:
        """Remove duplicate orders for the same asset."""
        seen = set()
        unique = []
        for order in orders:
            key = f"{order['action']}_{order['asset']}"
            if key not in seen:
                seen.add(key)
                unique.append(order)
        return unique
