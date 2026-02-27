"""
Backtest Report Storage & Comparison
=====================================
Persist results as JSON, load them back, and compare runs side-by-side.
"""

from __future__ import annotations
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ── Save / Load ──────────────────────────────────────────────────────────────

def save_result(result_dict: dict, run_id: Optional[str] = None) -> str:
    """
    Persist a backtest result to `backtest/results/<run_id>.json`.

    Parameters
    ----------
    result_dict : serialisable dict from BacktestResult.to_dict()
    run_id      : custom identifier, e.g. "spy_2022_blend". Auto-generated if None.

    Returns
    -------
    run_id (str)
    """
    if run_id is None:
        ts     = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        suffix = uuid.uuid4().hex[:6]
        run_id = f"run_{ts}_{suffix}"

    path = RESULTS_DIR / f"{run_id}.json"
    result_dict["_run_id"]  = run_id
    result_dict["_saved_at"] = datetime.utcnow().isoformat()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, default=str)

    return run_id


def load_result(run_id: str) -> dict:
    """Load a previously-saved result by run_id."""
    path = RESULTS_DIR / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No saved result for run_id='{run_id}'")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Listing ───────────────────────────────────────────────────────────────────

def list_runs() -> list[dict]:
    """
    Return summary metadata for all saved runs (sorted newest first).

    Each entry contains: run_id, start, end, strategy, saved_at, cum_return, sharpe_ratio
    """
    runs = []
    for p in sorted(RESULTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            summary = d.get("summary", {})
            runs.append({
                "run_id":      d.get("_run_id", p.stem),
                "strategy":    d.get("strategy", ""),
                "start":       d.get("start", ""),
                "end":         d.get("end", ""),
                "n_tickers":   len(d.get("tickers", [])),
                "cum_return":  summary.get("cum_return"),
                "sharpe":      summary.get("sharpe_ratio"),
                "max_dd":      summary.get("max_drawdown"),
                "saved_at":    d.get("_saved_at", ""),
            })
        except Exception:
            pass
    return runs


# ── Comparison ────────────────────────────────────────────────────────────────

_COMPARE_KEYS = [
    ("Cumulative Return",  "cum_return",    "{:+.2%}"),
    ("Annualised Return",  "ann_return",    "{:+.2%}"),
    ("Annualised Vol",     "ann_volatility","{:.2%}"),
    ("Sharpe",             "sharpe_ratio",  "{:.3f}"),
    ("Sortino",            "sortino_ratio", "{:.3f}"),
    ("Max Drawdown",       "max_drawdown",  "{:.2%}"),
    ("Calmar",             "calmar_ratio",  "{:.3f}"),
    ("Win Rate",           "win_rate",      "{:.1%}"),
    ("Profit Factor",      "profit_factor", "{:.3f}"),
    ("VaR (95%)",          "var_95",        "{:.2%}"),
    ("Alpha (ann.)",       "alpha_ann",     "{:+.2%}"),
    ("Beta",               "beta",          "{:.3f}"),
    ("Info Ratio",         "info_ratio",    "{:.3f}"),
]


def compare_runs(run_ids: list[str]) -> dict:
    """
    Return a side-by-side metrics comparison.

    Returns
    -------
    {
      "columns": ["metric", <run_id1>, <run_id2>, ...],
      "rows":    [["Sharpe", "1.23", "0.87", ...], ...],
    }
    """
    results = []
    for rid in run_ids:
        try:
            results.append((rid, load_result(rid)))
        except FileNotFoundError:
            results.append((rid, {}))

    columns = ["Metric"] + [rid for rid, _ in results]
    rows = []

    for label, key, fmt in _COMPARE_KEYS:
        row = [label]
        for rid, d in results:
            v = d.get("summary", {}).get(key)
            if v is None:
                row.append("—")
            else:
                try:
                    row.append(fmt.format(v))
                except Exception:
                    row.append(str(v))
        rows.append(row)

    return {"columns": columns, "rows": rows}


def delete_result(run_id: str) -> bool:
    """Delete a saved run. Returns True if deleted, False if not found."""
    path = RESULTS_DIR / f"{run_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
