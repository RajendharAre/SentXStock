"""
Backtesting Runner
==================
High-level entry point:  call `run_backtest()` with minimal config and get
a complete `BacktestResult` back.

Quick-start examples
--------------------
  # Full S&P 500 universe, last 2 years:
  from backtest.runner import run_backtest
  result = run_backtest(start="2022-01-01", end="2024-01-01")
  print(result.summary)

  # Custom tickers + aggressive strategy:
  result = run_backtest(
      tickers=["AAPL", "TSLA", "NVDA", "MSFT"],
      start="2023-01-01",
      end="2024-06-30",
      strategy_variant="blend",
      risk_level="High",
      initial_capital=50_000,
  )
"""

from __future__ import annotations

import warnings
from typing import Optional

from backtest.data_loader import load_backtest_data
from backtest.engine      import BacktestEngine, EngineConfig, BacktestResult
from backtest.metrics     import compute_metrics
from backtest.report      import save_result
from backtest.strategy    import StrategyConfig, build_strategy
from backtest.universe    import Universe

warnings.filterwarnings("ignore", category=FutureWarning)


def run_backtest(
    *,
    tickers:           Optional[list[str]] = None,
    sector:            Optional[str]       = None,
    start:             str                 = "2022-01-01",
    end:               str                 = "2024-01-01",
    strategy_variant:  str                 = "threshold",   # "threshold" | "blend" | "adaptive"
    risk_level:        str                 = "Medium",       # "Low" | "Medium" | "High"
    sentiment_mode:    str                 = "price_momentum",
    model_variant:     str                 = "FinBERT",
    buy_threshold:     float               = 0.10,
    sell_threshold:    float               = -0.10,
    max_position_pct:  float               = 0.05,
    initial_capital:   float               = 100_000.0,
    benchmark_ticker:  str                 = "SPY",
    slippage_bps:      float               = 5.0,
    allow_shorts:      bool                = False,
    max_open_positions:int                 = 20,
    save_results:      bool                = True,
    run_id:            Optional[str]       = None,
    verbose:           bool                = True,
) -> BacktestResult:
    """
    Run a complete backtest and return a BacktestResult.

    Parameters (all keyword-only)
    ------------------------------
    tickers             : list of ticker symbols. None → full universe (or sector filter).
    sector              : optional sector name to filter universe (e.g. "Technology").
    start / end         : ISO date strings.
    strategy_variant    : "threshold" | "blend" | "adaptive"
    risk_level          : "Low" | "Medium" | "High"
    sentiment_mode      : "price_momentum" | "cached_news"
    buy_threshold       : sentiment score threshold for BUY
    sell_threshold      : sentiment score threshold for SELL
    max_position_pct    : max portfolio % per ticker
    initial_capital     : starting cash
    benchmark_ticker    : ticker used as benchmark (default SPY)
    slippage_bps        : slippage in basis points per trade
    allow_shorts        : allow short selling on SELL signals
    max_open_positions  : cap on concurrent open positions (0 = no cap)
    save_results        : persist results to backtest/results/
    run_id              : custom name for saved result (auto-generated if None)
    verbose             : print progress and summary
    """

    # ── 1. Resolve ticker list ────────────────────────────────────────────
    if tickers is None:
        universe = Universe()
        if sector:
            tickers = universe.tickers_by_sector().get(sector, [])
            if not tickers:
                raise ValueError(f"Unknown sector '{sector}'. Valid: {list(universe.tickers_by_sector().keys())}")
        else:
            tickers = universe.tickers
    else:
        tickers = list(dict.fromkeys(t.upper() for t in tickers))  # dedup, preserve order

    if verbose:
        print(f"[RUNNER] Universe: {len(tickers)} tickers  |  {start} → {end}")

    # ── 2. Build strategy ─────────────────────────────────────────────────
    s_cfg = StrategyConfig(
        buy_threshold    = buy_threshold,
        sell_threshold   = sell_threshold,
        max_position_pct = max_position_pct,
        risk_level       = risk_level,
        model_variant    = model_variant,
    )
    strategy = build_strategy(strategy_variant, s_cfg)

    if verbose:
        print(f"[RUNNER] Strategy: {strategy.name}  |  risk={risk_level}  |  sentiment={sentiment_mode}")

    # ── 3. Load price + sentiment data ────────────────────────────────────
    load_tickers = list(set(tickers + [benchmark_ticker]))
    raw = load_backtest_data(
        tickers        = load_tickers,
        start          = start,
        end            = end,
        sentiment_mode = sentiment_mode,
        verbose        = verbose,
    )

    # Separate benchmark from strategy data
    bench_data   = raw.pop(benchmark_ticker, None)
    backtest_data = {t: raw[t] for t in tickers if t in raw}

    if not backtest_data:
        raise RuntimeError("No price data loaded. Check dates and ticker list.")

    actual_tickers = list(backtest_data.keys())
    if len(actual_tickers) < len(tickers) and verbose:
        missing = set(tickers) - set(actual_tickers)
        print(f"[RUNNER] {len(missing)} tickers skipped (no data): {sorted(missing)[:10]}{'...' if len(missing)>10 else ''}")

    # ── 4. Run engine ─────────────────────────────────────────────────────
    e_cfg = EngineConfig(
        initial_capital    = initial_capital,
        slippage_bps       = slippage_bps,
        allow_shorts       = allow_shorts,
        max_open_positions = max_open_positions,
    )
    engine = BacktestEngine(strategy=strategy, engine_config=e_cfg)

    result = engine.run(
        data           = backtest_data,
        benchmark_data = bench_data,
        verbose        = verbose,
    )

    # ── 5. Persist result ─────────────────────────────────────────────────
    if save_results:
        rid = save_result(result.to_dict(), run_id=run_id)
        if verbose:
            print(f"[RUNNER] Result saved → backtest/results/{rid}.json")

    return result
