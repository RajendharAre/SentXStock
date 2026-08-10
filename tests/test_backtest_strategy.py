from __future__ import annotations

import unittest

try:
    import pandas as pd
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(f"Python test dependency missing: {exc.name}") from exc

from backtest.strategy import StrategyConfig, build_strategy


class BacktestStrategyTests(unittest.TestCase):
    def test_threshold_strategy_classifies_buy_sell_and_hold(self) -> None:
        dates = pd.date_range("2026-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"Close": [100, 101, 102]}, index=dates)
        sentiment = pd.Series([0.2, -0.2, 0.0], index=dates)
        strategy = build_strategy("threshold", StrategyConfig(
            buy_threshold=0.1,
            sell_threshold=-0.1,
            max_position_pct=0.05,
            min_position_pct=0.01,
            size_by_conviction=False,
        ))

        signals = strategy.compute_signals(sentiment, prices)

        self.assertEqual(signals["signal"].tolist(), ["BUY", "SELL", "HOLD"])
        self.assertEqual(signals["position_pct"].tolist(), [0.05, 0.05, 0.0])

    def test_adaptive_strategy_uses_risk_specific_thresholds(self) -> None:
        low = build_strategy("adaptive", StrategyConfig(risk_level="Low"))
        high = build_strategy("adaptive", StrategyConfig(risk_level="High"))

        self.assertEqual(low.cfg.buy_threshold, 0.25)
        self.assertEqual(low.cfg.sell_threshold, -0.25)
        self.assertEqual(high.cfg.buy_threshold, 0.05)
        self.assertEqual(high.cfg.sell_threshold, -0.05)


if __name__ == "__main__":
    unittest.main()
