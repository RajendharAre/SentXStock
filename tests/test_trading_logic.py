from __future__ import annotations

import unittest

try:
    import yfinance  # noqa: F401
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # noqa: F401
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(f"Python test dependency missing: {exc.name}") from exc

from portfolio.orders import OrderDrafter
from portfolio.portfolio import PortfolioManager
from portfolio.risk import RiskEngine
from sentiment.scorer import SentimentScorer


class SentimentScorerTests(unittest.TestCase):
    def test_aggregate_scores_counts_and_labels_market_mood(self) -> None:
        scorer = SentimentScorer()

        result = scorer.aggregate_scores([
            {"sentiment": "Bullish", "score": 0.8},
            {"sentiment": "Bullish", "score": 0.4},
            {"sentiment": "Neutral", "score": 0.0},
        ])

        self.assertEqual(result["overall_sentiment"], "Bullish")
        self.assertEqual(result["sentiment_score"], 0.4)
        self.assertEqual(result["total_analyzed"], 3)
        self.assertEqual(result["bullish_count"], 2)
        self.assertEqual(result["bearish_count"], 0)
        self.assertEqual(result["neutral_count"], 1)

    def test_empty_aggregate_is_neutral(self) -> None:
        result = SentimentScorer().aggregate_scores([])

        self.assertEqual(result["overall_sentiment"], "Neutral")
        self.assertEqual(result["sentiment_score"], 0.0)
        self.assertEqual(result["total_analyzed"], 0)


class RiskAndPortfolioTests(unittest.TestCase):
    def test_risk_engine_maps_sentiment_to_allocations(self) -> None:
        engine = RiskEngine()

        bullish = engine.determine_risk_level(0.75, "Medium")
        bearish = engine.determine_risk_level(-0.5, "Medium")
        neutral = engine.determine_risk_level(0.1, "Medium")

        self.assertEqual(bullish["new_risk"], "High")
        self.assertEqual(bullish["target_allocation"]["equity"], 70)
        self.assertEqual(bearish["new_risk"], "Low")
        self.assertEqual(bearish["target_allocation"]["cash"], 40)
        self.assertEqual(neutral["new_risk"], "Medium")
        self.assertFalse(neutral["risk_changed"])

    def test_rebalance_actions_capture_material_allocation_gaps(self) -> None:
        actions = RiskEngine().get_rebalance_actions(
            {"equity_pct": 30, "bonds_pct": 50, "cash_pct": 20},
            {"equity": 50, "bonds": 30, "cash": 20},
        )

        self.assertEqual(actions["equity_diff"], 20)
        self.assertEqual(actions["bonds_diff"], -20)
        self.assertIn("Increase equity by 20.0%", actions["actions"])
        self.assertIn("Decrease bonds by 20.0%", actions["actions"])

    def test_portfolio_summary_uses_average_prices_without_live_fetch(self) -> None:
        portfolio = PortfolioManager({
            "cash": 1000,
            "risk_level": "Medium",
            "holdings": {
                "AAPL": {"shares": 2, "avg_price": 100},
                "TLT": {"shares": 4, "avg_price": 50},
            },
        })

        summary = portfolio.get_portfolio_summary()

        self.assertEqual(summary["total_value"], 1400)
        self.assertAlmostEqual(summary["equity_pct"], 14.29)
        self.assertAlmostEqual(summary["bonds_pct"], 14.29)
        self.assertAlmostEqual(summary["cash_pct"], 71.43)
        self.assertEqual(summary["holdings"]["AAPL"]["type"], "equity")
        self.assertEqual(summary["holdings"]["TLT"]["type"], "bonds")


class OrderDrafterTests(unittest.TestCase):
    def test_defensive_orders_sell_equities_and_buy_bonds(self) -> None:
        orders = OrderDrafter().draft_orders(
            risk_result={"new_risk": "Low", "risk_changed": True},
            rebalance_actions={},
            portfolio_details={
                "holdings": {
                    "AAPL": {"type": "equity"},
                    "MSFT": {"type": "equity"},
                }
            },
            sentiment_results=[
                {"ticker": "AAPL", "score": -0.7},
                {"ticker": "MSFT", "score": -0.2},
            ],
        )

        order_pairs = {(order["action"], order["asset"]) for order in orders}
        self.assertIn(("SELL", "AAPL"), order_pairs)
        self.assertIn(("SELL", "MSFT"), order_pairs)
        self.assertIn(("BUY", "TLT"), order_pairs)

    def test_balanced_orders_hold_when_no_signal_or_rebalance_exists(self) -> None:
        orders = OrderDrafter().draft_orders(
            risk_result={"new_risk": "Medium", "risk_changed": False},
            rebalance_actions={"equity_diff": 0},
            portfolio_details={"holdings": {}},
            sentiment_results=[],
        )

        self.assertEqual(orders, [{
            "action": "HOLD",
            "asset": "ALL",
            "reason": "Portfolio within target allocation, sentiment neutral \u2014 no action needed",
        }])


if __name__ == "__main__":
    unittest.main()
