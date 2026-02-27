"""
SentXStock Backtesting Framework
=================================
Modular, production-grade backtesting system for sentiment-driven trading.

Layers
------
  universe    — S&P 500 list + dynamic ticker registration
  data_loader — Historical OHLCV + synthetic sentiment via yfinance
  strategy    — Sentiment → signal → position sizing (fully configurable)
  engine      — Walk-forward backtesting loop
  metrics     — Cumulative returns, Sharpe, max drawdown, win rate
  report      — JSON result storage + multi-run comparison
  runner      — Entry point: programmatic & CLI usage

Usage
-----
  from backtest.runner import run_backtest

  result = run_backtest(
      tickers=["AAPL", "TSLA"],      # or None → full S&P 500
      start="2022-01-01",
      end="2024-01-01",
      strategy_config={"sentiment_threshold": 0.1},
  )
  print(result["summary"])
"""

from backtest.runner import run_backtest

__all__ = ["run_backtest"]
