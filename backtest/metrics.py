"""
Performance Metrics
===================
Pure-function, numpy-only metrics — no external dependencies beyond pandas.

All functions accept a pd.Series of daily portfolio returns.

Metrics computed
----------------
- Cumulative return
- Annualized return
- Annualized volatility (std dev of returns × √252)
- Sharpe ratio (assuming risk-free rate r_f = 5% annualized ≈ US T-bill 2025)
- Sortino ratio (downside deviation only)
- Maximum drawdown
- Calmar ratio (annualized return / max drawdown)
- Win rate (fraction of days with positive return)
- Avg win / avg loss
- Profit factor
- Best / worst single-day return

Benchmark comparison
--------------------
compute_benchmark_metrics() accepts SPY returns alongside strategy returns
and adds Information Ratio + Alpha + Beta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE_ANNUAL = 0.05          # ~5% US T-bill (2025)
RISK_FREE_RATE_DAILY  = RISK_FREE_RATE_ANNUAL / TRADING_DAYS_PER_YEAR


def compute_metrics(returns: pd.Series, label: str = "Strategy") -> dict:
    """
    Compute the full set of backtest performance metrics.

    Parameters
    ----------
    returns : pd.Series  daily returns (fractional, e.g. 0.01 = 1%)
    label   : str        label for display

    Returns
    -------
    dict with all metrics (floats, already rounded to 4 dp)
    """
    returns = returns.dropna()
    if len(returns) < 2:
        return _empty_metrics(label)

    n = len(returns)

    # ── Cumulative / annualized return ────────────────────────────────────
    cum_return   = float((1 + returns).prod() - 1)
    years        = n / TRADING_DAYS_PER_YEAR
    ann_return   = float((1 + cum_return) ** (1 / max(years, 1e-9)) - 1)

    # ── Volatility ────────────────────────────────────────────────────────
    ann_vol = float(returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))

    # ── Sharpe ratio ──────────────────────────────────────────────────────
    excess     = returns - RISK_FREE_RATE_DAILY
    sharpe     = float((excess.mean() / excess.std()) * np.sqrt(TRADING_DAYS_PER_YEAR)) \
                 if excess.std() > 0 else 0.0

    # ── Sortino ratio (downside std only) ─────────────────────────────────
    downside   = returns[returns < RISK_FREE_RATE_DAILY]
    down_std   = float(downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)) if len(downside) > 1 else 1e-9
    sortino    = float(ann_return - RISK_FREE_RATE_ANNUAL) / down_std if down_std > 0 else 0.0

    # ── Max drawdown ──────────────────────────────────────────────────────
    cum_curve  = (1 + returns).cumprod()
    rolling_max = cum_curve.cummax()
    drawdowns  = (cum_curve - rolling_max) / rolling_max
    max_dd     = float(drawdowns.min())  # negative number

    # ── Calmar ratio ──────────────────────────────────────────────────────
    calmar     = ann_return / abs(max_dd) if max_dd != 0 else 0.0

    # ── Win / loss analysis ───────────────────────────────────────────────
    wins       = returns[returns > 0]
    losses     = returns[returns < 0]
    win_rate   = float(len(wins) / n)
    avg_win    = float(wins.mean())    if len(wins)   > 0 else 0.0
    avg_loss   = float(losses.mean())  if len(losses) > 0 else 0.0
    profit_fac = float(wins.sum() / abs(losses.sum())) if losses.sum() != 0 else np.inf

    # ── Extremes ──────────────────────────────────────────────────────────
    best_day   = float(returns.max())
    worst_day  = float(returns.min())

    # ── Value at Risk (95%) ───────────────────────────────────────────────
    var_95     = float(np.percentile(returns, 5))

    return {
        "label":            label,
        "n_days":           n,
        "cum_return":       round(cum_return,  4),
        "ann_return":       round(ann_return,  4),
        "ann_volatility":   round(ann_vol,     4),
        "sharpe_ratio":     round(sharpe,      4),
        "sortino_ratio":    round(sortino,     4),
        "max_drawdown":     round(max_dd,      4),
        "calmar_ratio":     round(calmar,      4),
        "win_rate":         round(win_rate,    4),
        "avg_win":          round(avg_win,     6),
        "avg_loss":         round(avg_loss,    6),
        "profit_factor":    round(profit_fac,  4) if np.isfinite(profit_fac) else 999.9,
        "best_day":         round(best_day,    6),
        "worst_day":        round(worst_day,   6),
        "var_95":           round(var_95,      6),
    }


def compute_benchmark_metrics(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    label: str = "Strategy",
) -> dict:
    """
    Extend metrics with benchmark-relative statistics.

    Adds: alpha, beta, information_ratio, tracking_error, up_capture, down_capture
    """
    base = compute_metrics(strategy_returns, label)

    # Align
    both = pd.DataFrame({"s": strategy_returns, "b": benchmark_returns}).dropna()
    if len(both) < 10:
        return base

    s, b = both["s"], both["b"]

    # Beta / Alpha via OLS
    cov_matrix = np.cov(s, b)
    beta       = float(cov_matrix[0, 1] / cov_matrix[1, 1]) if cov_matrix[1, 1] > 0 else 1.0
    alpha_ann  = float((s.mean() - beta * b.mean()) * TRADING_DAYS_PER_YEAR)

    # Information Ratio
    active_ret    = s - b
    tracking_err  = float(active_ret.std() * np.sqrt(TRADING_DAYS_PER_YEAR))
    info_ratio    = float(active_ret.mean() * TRADING_DAYS_PER_YEAR / tracking_err) \
                    if tracking_err > 0 else 0.0

    # Up/down capture
    up_periods   = b[b > 0]
    down_periods = b[b < 0]
    up_capture   = float(s[b > 0].mean() / up_periods.mean()) if len(up_periods) > 5 else 1.0
    down_capture = float(s[b < 0].mean() / down_periods.mean()) if len(down_periods) > 5 else 1.0

    base.update({
        "alpha_ann":      round(alpha_ann,   4),
        "beta":           round(beta,        4),
        "info_ratio":     round(info_ratio,  4),
        "tracking_error": round(tracking_err,4),
        "up_capture":     round(up_capture,  4),
        "down_capture":   round(down_capture,4),
    })
    return base


def compute_per_ticker_metrics(
    ticker_returns: dict[str, pd.Series],
) -> list[dict]:
    """
    Compute metrics for each ticker independently.

    Returns
    -------
    list of dicts, sorted by Sharpe descending
    """
    results = [compute_metrics(ret, ticker) for ticker, ret in ticker_returns.items()]
    return sorted(results, key=lambda x: x["sharpe_ratio"], reverse=True)


def equity_curve(returns: pd.Series, initial_capital: float = 100_000.0) -> pd.Series:
    """Convert daily returns → cumulative equity curve in dollars."""
    return initial_capital * (1 + returns).cumprod()


def _empty_metrics(label: str) -> dict:
    zero_keys = [
        "cum_return", "ann_return", "ann_volatility", "sharpe_ratio",
        "sortino_ratio", "max_drawdown", "calmar_ratio", "win_rate",
        "avg_win", "avg_loss", "profit_factor", "best_day", "worst_day", "var_95",
    ]
    return {"label": label, "n_days": 0, **{k: 0.0 for k in zero_keys}}
