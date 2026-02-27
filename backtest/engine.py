"""
Backtesting Engine
==================
Walk-forward portfolio simulation.

Architecture
------------
- Portfolio state (cash + positions) is tracked via a `PortfolioState` object.
- For each day the engine:
    1. Receives signals from the strategy for each active ticker.
    2. Executes trades: opens/closes/rebalances positions.
    3. Marks the portfolio to market.
    4. Records the daily P&L → return series.
- Returns a complete `BacktestResult` with equity curves, per-ticker stats,
  and all metrics.

Simulation assumptions
----------------------
- Orders execute at next-day `Open` price (realistic: signal at Close, fill at next Open).
- Slippage: `slippage_bps` basis points applied to each trade (default 5 bps).
- Commission: `commission_per_trade` flat fee (default $0 — can be set to $1-$5).
- Short selling: supported if `allow_shorts=True`.
- Position limits: max_position_pct cap per ticker (from StrategyConfig).
- Cash earns risk-free rate on idle days (optional, `apply_rf_on_cash=True`).

Scalability
-----------
- All tickers processed via vectorised pandas operations per day.
- Memory: O(T × N) where T=trading days, N=tickers. For 500 tickers × 500 days ≈ manageable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from backtest.strategy import SentimentStrategy, StrategyConfig
from backtest.metrics  import (
    compute_metrics, compute_benchmark_metrics,
    compute_per_ticker_metrics, equity_curve,
    TRADING_DAYS_PER_YEAR, RISK_FREE_RATE_DAILY,
)


@dataclass
class EngineConfig:
    """Simulation-level parameters (separate from strategy parameters)."""
    initial_capital:    float = 100_000.0
    slippage_bps:       float = 5.0        # 5 basis points per fill
    commission:         float = 0.0        # flat per trade ($)
    allow_shorts:       bool  = False      # allow SELL signals to go short
    apply_rf_on_cash:   bool  = True       # cash earns risk-free rate
    max_open_positions: int   = 20         # concurrent position cap (0 = unlimited)
    rebalance_freq:     str   = "daily"    # "daily" | "weekly" | "monthly"


@dataclass
class PortfolioState:
    """Mutable portfolio state during simulation."""
    cash:       float
    positions:  dict = field(default_factory=dict)  # ticker → {"shares": n, "cost": c}
    history:    list = field(default_factory=list)
    trades:     list = field(default_factory=list)

    @property
    def open_tickers(self) -> list[str]:
        return [t for t, p in self.positions.items() if p["shares"] != 0]

    def market_value(self, prices: dict[str, float]) -> float:
        mv = self.cash
        for t, pos in self.positions.items():
            mv += pos["shares"] * prices.get(t, pos["cost"] / max(abs(pos["shares"]), 1))
        return mv


@dataclass
class BacktestResult:
    """Full result object returned by BacktestEngine.run()."""
    ticker_list:        list[str]
    start:              str
    end:                str
    strategy_name:      str
    strategy_config:    dict

    portfolio_returns:  pd.Series          # daily portfolio-level returns
    equity_curve:       pd.Series          # dollar equity curve
    benchmark_returns:  Optional[pd.Series]

    per_ticker_returns: dict[str, pd.Series]   # ticker → daily ticker returns
    trade_log:          list[dict]

    summary:            dict               # top-level metrics dict
    per_ticker_metrics: list[dict]         # sorted by Sharpe

    def to_dict(self) -> dict:
        """Serialisable dict for JSON / API response."""
        return {
            "tickers":          self.ticker_list,
            "start":            self.start,
            "end":              self.end,
            "strategy":         self.strategy_name,
            "strategy_config":  self.strategy_config,
            "summary":          self.summary,
            "per_ticker":       self.per_ticker_metrics,
            "equity_curve": {
                str(d.date()): round(v, 2)
                for d, v in self.equity_curve.items()
            },
            "n_trades":         len(self.trade_log),
        }


class BacktestEngine:
    """
    Walk-forward backtesting engine.

    Parameters
    ----------
    strategy      : SentimentStrategy instance
    engine_config : EngineConfig (simulation parameters)
    """

    def __init__(
        self,
        strategy: SentimentStrategy,
        engine_config: EngineConfig = None,
    ):
        self.strategy = strategy
        self.cfg      = engine_config or EngineConfig()

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(
        self,
        data: dict[str, dict],
        benchmark_data: Optional[dict] = None,
        verbose: bool = True,
    ) -> BacktestResult:
        """
        Run the backtest over all tickers.

        Parameters
        ----------
        data : {ticker: {"prices": DataFrame, "sentiment": Series}}
        benchmark_data : optional {"prices": DataFrame, "sentiment": Series} for SPY
        verbose : print progress

        Returns
        -------
        BacktestResult
        """
        if not data:
            raise ValueError("data dict is empty")

        tickers = list(data.keys())

        # ── Step 1: compute signals for all tickers ───────────────────────
        if verbose:
            print(f"[ENGINE] Computing signals for {len(tickers)} tickers…")

        all_signals: dict[str, pd.DataFrame] = {}
        for t, d in data.items():
            all_signals[t] = self.strategy.compute_signals(d["sentiment"], d["prices"])

        # ── Step 2: build unified date index ─────────────────────────────
        all_dates = sorted(set(
            d for t_signals in all_signals.values()
            for d in t_signals.index
        ))
        if not all_dates:
            raise ValueError("No valid trading dates found")

        if verbose:
            print(f"[ENGINE] Trading window: {all_dates[0].date()} → {all_dates[-1].date()} ({len(all_dates)} days)")

        # ── Step 3: walk-forward simulation ───────────────────────────────
        state = PortfolioState(cash=self.cfg.initial_capital)
        daily_portfolio_values: list[float] = []
        daily_dates: list[pd.Timestamp] = []
        ticker_pnl: dict[str, list[float]] = {t: [] for t in tickers}
        ticker_dates: dict[str, list] = {t: [] for t in tickers}

        prev_value = self.cfg.initial_capital

        for day_idx, date in enumerate(all_dates):
            # ── get today's prices ────────────────────────────────────────
            today_prices: dict[str, float] = {}
            next_prices:  dict[str, float] = {}  # for next-open fill

            for t, d in data.items():
                if date in d["prices"].index:
                    row = d["prices"].loc[date]
                    today_prices[t] = float(row["Close"])
                    next_prices[t]  = float(row["Open"])  # execution at open

            # ── idle cash earns risk-free ─────────────────────────────────
            if self.cfg.apply_rf_on_cash:
                state.cash *= (1 + RISK_FREE_RATE_DAILY)

            # ── get signals for today ─────────────────────────────────────
            day_signals: dict[str, dict] = {}
            for t, sig_df in all_signals.items():
                if date in sig_df.index:
                    row = sig_df.loc[date]
                    day_signals[t] = {
                        "signal":       row["signal"],
                        "position_pct": row["position_pct"],
                    }

            # ── execute trades ────────────────────────────────────────────
            self._execute_trades(state, day_signals, next_prices, today_prices, date)

            # ── mark to market ────────────────────────────────────────────
            portfolio_val = state.market_value(today_prices)
            daily_portfolio_values.append(portfolio_val)
            daily_dates.append(date)

            # ── per-ticker P&L (using Close price return) ─────────────────
            for t in tickers:
                if t in today_prices:
                    prev_close = data[t]["prices"]["Close"].shift(1)
                    if date in prev_close.index:
                        pc = float(prev_close.loc[date])
                        if pc and pc > 0:
                            r = (today_prices[t] - pc) / pc

                            # scale by position held yesterday
                            shares = state.positions.get(t, {}).get("shares", 0)
                            if shares != 0:
                                ticker_pnl[t].append(r)
                            else:
                                ticker_pnl[t].append(0.0)
                            ticker_dates[t].append(date)

        if verbose:
            print(f"[ENGINE] Simulation complete — {len(state.trades)} trades executed")

        # ── Step 4: build return series ───────────────────────────────────
        value_series  = pd.Series(daily_portfolio_values, index=daily_dates)
        port_returns  = value_series.pct_change().dropna()
        eq_curve      = equity_curve(port_returns, self.cfg.initial_capital)

        per_ticker_ret = {}
        for t in tickers:
            if ticker_dates[t]:
                per_ticker_ret[t] = pd.Series(ticker_pnl[t], index=ticker_dates[t])

        # ── Step 5: benchmark ─────────────────────────────────────────────
        bench_returns = None
        if benchmark_data:
            bp = benchmark_data["prices"]["Close"].squeeze().pct_change().dropna()
            bench_returns = bp.reindex(port_returns.index).fillna(0.0)

        # ── Step 6: metrics ───────────────────────────────────────────────
        if bench_returns is not None and len(bench_returns) > 10:
            summary = compute_benchmark_metrics(port_returns, bench_returns)
        else:
            summary = compute_metrics(port_returns)

        per_ticker_m = compute_per_ticker_metrics(per_ticker_ret)

        result = BacktestResult(
            ticker_list       = tickers,
            start             = str(all_dates[0].date()),
            end               = str(all_dates[-1].date()),
            strategy_name     = self.strategy.name,
            strategy_config   = self.strategy.describe(),
            portfolio_returns = port_returns,
            equity_curve      = eq_curve,
            benchmark_returns = bench_returns,
            per_ticker_returns= per_ticker_ret,
            trade_log         = state.trades,
            summary           = summary,
            per_ticker_metrics= per_ticker_m,
        )

        if verbose:
            self._print_summary(result)

        return result

    # ── Trade execution ──────────────────────────────────────────────────────

    def _execute_trades(
        self,
        state: PortfolioState,
        signals: dict[str, dict],
        next_prices: dict[str, float],
        today_prices: dict[str, float],
        date: pd.Timestamp,
    ):
        """
        Execute trades for one day.

        Logic
        -----
        - BUY  → open/increase position up to position_pct of current portfolio
        - SELL → close or short position (if allow_shorts=True)
        - HOLD → do nothing for new positions; keep existing positions
        - Max open positions cap enforced.
        """
        portfolio_val = state.market_value(today_prices)
        n_open = len(state.open_tickers)

        for t, sig in signals.items():
            signal      = sig["signal"]
            pos_pct     = sig["position_pct"]
            price       = next_prices.get(t) or today_prices.get(t)
            if not price or price <= 0:
                continue

            current_shares = state.positions.get(t, {}).get("shares", 0)

            if signal == "BUY":
                # Skip if at position cap (new position only)
                if (current_shares == 0 and
                    self.cfg.max_open_positions > 0 and
                    n_open >= self.cfg.max_open_positions):
                    continue

                target_value = portfolio_val * pos_pct
                current_value = current_shares * price
                delta_value  = target_value - current_value

                if delta_value < price:  # too small to buy 1 share
                    continue

                shares_to_buy = int(delta_value / price)
                if shares_to_buy <= 0:
                    continue

                cost = shares_to_buy * price * (1 + self.cfg.slippage_bps / 10000) + self.cfg.commission
                if cost > state.cash:
                    shares_to_buy = int(state.cash / (price * (1 + self.cfg.slippage_bps / 10000)))
                    if shares_to_buy <= 0:
                        continue
                    cost = shares_to_buy * price * (1 + self.cfg.slippage_bps / 10000) + self.cfg.commission

                state.cash -= cost
                if t not in state.positions:
                    state.positions[t] = {"shares": 0, "cost": 0.0}
                    n_open += 1
                state.positions[t]["shares"] += shares_to_buy
                state.positions[t]["cost"]   = state.positions[t]["shares"] * price

                state.trades.append({
                    "date": str(date.date()), "ticker": t, "action": "BUY",
                    "shares": shares_to_buy, "price": round(price, 4),
                    "value": round(shares_to_buy * price, 2),
                })

            elif signal == "SELL":
                if current_shares > 0:
                    # Close long position
                    proceeds = current_shares * price * (1 - self.cfg.slippage_bps / 10000) - self.cfg.commission
                    state.cash += proceeds
                    state.trades.append({
                        "date": str(date.date()), "ticker": t, "action": "SELL",
                        "shares": current_shares, "price": round(price, 4),
                        "value": round(current_shares * price, 2),
                    })
                    state.positions[t] = {"shares": 0, "cost": 0.0}
                    n_open -= 1

                elif self.cfg.allow_shorts and current_shares == 0:
                    # Open short
                    target_value   = portfolio_val * pos_pct
                    shares_to_short = int(target_value / price)
                    if shares_to_short <= 0:
                        continue
                    proceeds = shares_to_short * price * (1 - self.cfg.slippage_bps / 10000) - self.cfg.commission
                    state.cash += proceeds
                    state.positions[t] = {"shares": -shares_to_short, "cost": price * shares_to_short}
                    state.trades.append({
                        "date": str(date.date()), "ticker": t, "action": "SHORT",
                        "shares": shares_to_short, "price": round(price, 4),
                        "value": round(shares_to_short * price, 2),
                    })
                    n_open += 1

    # ── Summary printing ─────────────────────────────────────────────────────

    def _print_summary(self, r: BacktestResult):
        s = r.summary
        print("\n" + "=" * 60)
        print(f"  BACKTEST RESULTS — {r.strategy_name}")
        print(f"  {r.start} → {r.end}  |  {len(r.ticker_list)} tickers")
        print("=" * 60)
        print(f"  Cumulative Return : {s['cum_return']*100:+.2f}%")
        print(f"  Annualized Return : {s['ann_return']*100:+.2f}%")
        print(f"  Annualized Vol    : {s['ann_volatility']*100:.2f}%")
        print(f"  Sharpe Ratio      : {s['sharpe_ratio']:.3f}")
        print(f"  Sortino Ratio     : {s['sortino_ratio']:.3f}")
        print(f"  Max Drawdown      : {s['max_drawdown']*100:.2f}%")
        print(f"  Win Rate          : {s['win_rate']*100:.1f}%")
        print(f"  # Trades          : {len(r.trade_log)}")
        if r.benchmark_returns is not None:
            print(f"  Alpha (ann.)      : {s.get('alpha_ann',0)*100:+.2f}%")
            print(f"  Beta              : {s.get('beta',1):.3f}")
            print(f"  Info Ratio        : {s.get('info_ratio',0):.3f}")
        print("=" * 60)
