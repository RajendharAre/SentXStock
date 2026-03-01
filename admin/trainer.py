"""
Admin Trainer — Analyses an uploaded dataset using FinBERT sentiment + statistical
price analysis, then saves a structured result JSON for display to users.

Pipeline:
  1. Detect column types (text/headline, numeric/price, date)
  2. Run FinBERT sentiment on all text columns
  3. Run statistical price analysis on numeric columns (trend, volatility, returns)
  4. Combine into a unified result with BUY/SELL/HOLD signal
  5. Save to admin_results/<dataset_id>.json
"""

import json
import uuid
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS_DIR = Path(__file__).parent.parent / "admin_results"
RESULTS_DIR.mkdir(exist_ok=True)

# ─── Column-type heuristics ───────────────────────────────────────────────────

_TEXT_KEYWORDS  = {"headline", "title", "news", "text", "content", "summary",
                   "description", "article", "comment", "review", "message"}
_PRICE_KEYWORDS = {"close", "open", "high", "low", "price", "adj", "adjusted",
                   "value", "rate", "ltp", "amount", "cost"}
_DATE_KEYWORDS  = {"date", "time", "timestamp", "datetime", "day", "period"}


def _classify_columns(df: pd.DataFrame) -> dict:
    """Return {'text': [...], 'price': [...], 'date': [...], 'other': [...]}"""
    text_cols  = []
    price_cols = []
    date_cols  = []
    other_cols = []

    for col in df.columns:
        col_l = col.lower()
        if any(k in col_l for k in _DATE_KEYWORDS):
            date_cols.append(col)
        elif any(k in col_l for k in _TEXT_KEYWORDS) or df[col].dtype == object:
            text_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]) and any(k in col_l for k in _PRICE_KEYWORDS):
            price_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            price_cols.append(col)
        else:
            other_cols.append(col)

    return {"text": text_cols, "price": price_cols, "date": date_cols, "other": other_cols}


# ─── FinBERT sentiment over text column ───────────────────────────────────────

def _run_sentiment(texts: list[str]) -> list[dict]:
    """Run FinBERT on a list of strings, return per-item results."""
    try:
        from sentiment.finbert import get_finbert
        fb      = get_finbert()
        results = []
        for t in texts:
            if not t or not str(t).strip():
                results.append({"label": "Neutral", "score": 0.0, "confidence": 0.0})
                continue
            r = fb.analyze(str(t)[:512])        # FinBERT max 512 tokens
            results.append(r)
        return results
    except Exception as e:
        print(f"[Trainer] FinBERT unavailable: {e} — using VADER fallback")
        return _vader_fallback(texts)


def _vader_fallback(texts: list[str]) -> list[dict]:
    """VADER lexicon fallback when FinBERT is unavailable."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        results = []
        for t in texts:
            sc = sia.polarity_scores(str(t) if t else "")
            compound = sc["compound"]
            label    = "Positive" if compound > 0.05 else "Negative" if compound < -0.05 else "Neutral"
            results.append({"label": label, "score": round(compound, 4), "confidence": abs(compound)})
        return results
    except Exception:
        return [{"label": "Neutral", "score": 0.0, "confidence": 0.0}] * len(texts)


# ─── Price analysis ───────────────────────────────────────────────────────────

def _analyse_prices(series: pd.Series) -> dict:
    """Compute basic price statistics on a numeric series."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 2:
        return {}

    pct_changes = s.pct_change().dropna()
    returns     = float(((s.iloc[-1] - s.iloc[0]) / s.iloc[0]) * 100)
    volatility  = float(pct_changes.std() * 100)
    trend       = "Uptrend" if s.iloc[-1] > s.iloc[0] else "Downtrend"

    return {
        "first":      round(float(s.iloc[0]),  4),
        "last":       round(float(s.iloc[-1]), 4),
        "min":        round(float(s.min()),    4),
        "max":        round(float(s.max()),    4),
        "mean":       round(float(s.mean()),   4),
        "total_return_pct": round(returns,     2),
        "volatility_pct":   round(volatility,  2),
        "trend":      trend,
        "data_points": len(s),
    }


# ─── Aggregate signal ─────────────────────────────────────────────────────────

def _derive_signal(composite_score: float, price_stats: list[dict]) -> str:
    strong_trend = any(p.get("total_return_pct", 0) > 5  for p in price_stats)
    weak_trend   = any(p.get("total_return_pct", 0) < -5 for p in price_stats)

    if composite_score > 0.2 or (composite_score > 0.05 and strong_trend):
        return "BUY"
    elif composite_score < -0.2 or (composite_score < -0.05 and weak_trend):
        return "SELL"
    else:
        return "HOLD"


# ─── Public entry point ───────────────────────────────────────────────────────

def train_dataset(dataset_id: str, company: str, df: pd.DataFrame) -> dict:
    """
    Run the full analysis pipeline on a DataFrame.
    Returns the result dict (also saved to admin_results/).
    """
    result_id  = uuid.uuid4().hex[:12]
    started_at = datetime.now().isoformat(timespec="seconds")
    col_types  = _classify_columns(df)

    errors: list[str] = []
    sentiment_rows:   list[dict] = []
    price_analyses:   list[dict] = []
    composite_score  = 0.0
    sentiment_summary = {}

    # ── 1. Sentiment analysis on text columns ────────────────────────────────
    for col in col_types["text"]:
        texts   = df[col].fillna("").astype(str).tolist()
        if not any(t.strip() for t in texts):
            continue
        try:
            sentiments = _run_sentiment(texts[:200])   # cap at 200 rows
            scores     = [s["score"] for s in sentiments]
            labels     = [s["label"] for s in sentiments]

            bull_count = labels.count("Positive")
            bear_count = labels.count("Negative")
            neut_count = labels.count("Neutral")
            avg_score  = float(np.mean(scores)) if scores else 0.0

            composite_score = avg_score   # last text column wins; could average

            sentiment_summary[col] = {
                "analyzed":  len(sentiments),
                "bullish":   bull_count,
                "bearish":   bear_count,
                "neutral":   neut_count,
                "avg_score": round(avg_score, 4),
            }
            # Sample rows — first 50 for preview
            for i, (txt, sent) in enumerate(zip(texts[:50], sentiments[:50])):
                sentiment_rows.append({
                    "row":       i + 1,
                    "column":    col,
                    "text":      str(txt)[:120],
                    "label":     sent["label"],
                    "score":     round(sent["score"], 4),
                    "confidence": round(sent.get("confidence", abs(sent["score"])), 4),
                })
        except Exception as e:
            errors.append(f"Sentiment on '{col}': {e}")

    # ── 2. Price analysis on numeric columns ─────────────────────────────────
    for col in col_types["price"]:
        try:
            stats = _analyse_prices(df[col])
            if stats:
                stats["column"] = col
                price_analyses.append(stats)
                # If no text → use price trend as proxy score
                if not col_types["text"]:
                    ret = stats.get("total_return_pct", 0)
                    composite_score = max(-1.0, min(1.0, ret / 20.0))
        except Exception as e:
            errors.append(f"Price analysis on '{col}': {e}")

    # ── 3. Overall signal ────────────────────────────────────────────────────
    signal     = _derive_signal(composite_score, price_analyses)
    confidence = min(99.9, abs(composite_score) * 100 * 2.5 + 40)

    result = {
        "result_id":         result_id,
        "dataset_id":        dataset_id,
        "company":           company,
        "trained_at":        started_at,
        "total_rows":        len(df),
        "total_columns":     len(df.columns),
        "column_types":      col_types,
        "composite_score":   round(composite_score, 4),
        "signal":            signal,
        "confidence":        round(confidence, 1),
        "sentiment_summary": sentiment_summary,
        "sentiment_rows":    sentiment_rows,
        "price_analyses":    price_analyses,
        "errors":            errors,
    }

    # Save result JSON
    out = RESULTS_DIR / f"{dataset_id}.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)

    return result


def load_result(dataset_id: str) -> dict | None:
    path = RESULTS_DIR / f"{dataset_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_results() -> list[dict]:
    """Return summary of all training results, newest first."""
    results = []
    for p in RESULTS_DIR.glob("*.json"):
        if p.name == ".gitkeep":
            continue
        try:
            with open(p) as f:
                d = json.load(f)
            results.append({
                "result_id":       d.get("result_id"),
                "dataset_id":      d.get("dataset_id"),
                "company":         d.get("company"),
                "trained_at":      d.get("trained_at"),
                "signal":          d.get("signal"),
                "confidence":      d.get("confidence"),
                "composite_score": d.get("composite_score"),
                "total_rows":      d.get("total_rows"),
            })
        except Exception:
            pass
    return sorted(results, key=lambda r: r.get("trained_at", ""), reverse=True)
