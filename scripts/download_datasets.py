"""
Dataset Downloader
==================
Downloads historical OHLCV price data for all tickers in the S&P 500 universe
(or a custom list) and saves them as CSV files in:

    datasets/prices/<TICKER>.csv

Optionally also generates synthetic sentiment CSVs in:

    datasets/sentiment/<TICKER>.csv

Usage
-----
  # Full S&P 500 universe (default: 2020-01-01 to today)
  python scripts/download_datasets.py

  # Custom date range
  python scripts/download_datasets.py --start 2021-01-01 --end 2025-01-01

  # Specific tickers only
  python scripts/download_datasets.py --tickers AAPL,MSFT,NVDA,TSLA,SPY

  # Full universe + sentiment CSVs
  python scripts/download_datasets.py --with-sentiment

  # Specific sector
  python scripts/download_datasets.py --sector Technology

  # Resume interrupted download (skip already-present CSVs)
  python scripts/download_datasets.py --skip-existing

CSV format
----------
  Date, Open, High, Low, Close, Volume
  2020-01-02, 75.09, 75.15, 73.80, 75.09, 135480400
"""

import argparse
import sys
import os
import warnings
from datetime import date, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

# ── make sure project root is importable ──────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
import yfinance as yf

PRICES_DIR    = ROOT / "datasets" / "prices"
SENTIMENT_DIR = ROOT / "datasets" / "sentiment"
PRICES_DIR.mkdir(parents=True, exist_ok=True)
SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE     = 50
MIN_ROWS       = 20


# ── ticker resolution ─────────────────────────────────────────────────────────

def get_tickers(args) -> list[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    from backtest.universe import Universe
    u = Universe()
    if args.sector:
        tickers = u.tickers_by_sector().get(args.sector)
        if not tickers:
            print(f"[ERROR] Unknown sector '{args.sector}'")
            print(f"  Valid sectors: {list(u.tickers_by_sector().keys())}")
            sys.exit(1)
        print(f"[INFO] Sector '{args.sector}': {len(tickers)} tickers")
    else:
        tickers = u.tickers
        print(f"[INFO] Full universe: {len(tickers)} tickers")
    # always include benchmark
    if "SPY" not in tickers:
        tickers = ["SPY"] + list(tickers)
    return tickers


# ── price download ─────────────────────────────────────────────────────────────

def download_prices(
    tickers: list[str],
    start: str,
    end: str,
    skip_existing: bool = False,
) -> dict[str, pd.DataFrame]:
    """Download and save price CSVs. Returns {ticker: DataFrame}."""
    results: dict[str, pd.DataFrame] = {}

    # check which are already present
    if skip_existing:
        remaining = [t for t in tickers if not (PRICES_DIR / f"{t}.csv").exists()]
        skipped   = len(tickers) - len(remaining)
        if skipped:
            print(f"[INFO] Skipping {skipped} tickers (CSV already exists). Use --no-skip to re-download.")
        # load already-saved ones into results
        for t in tickers:
            p = PRICES_DIR / f"{t}.csv"
            if p.exists():
                try:
                    df = pd.read_csv(p, index_col=0, parse_dates=True)
                    results[t] = df
                except Exception:
                    pass
    else:
        remaining = list(tickers)

    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx, i in enumerate(range(0, len(remaining), BATCH_SIZE), 1):
        batch = remaining[i : i + BATCH_SIZE]
        print(f"[DOWNLOAD] Batch {batch_idx}/{total_batches}: "
              f"{batch[:5]}{'…' if len(batch) > 5 else ''} ({len(batch)} tickers)")

        try:
            raw = yf.download(
                batch,
                start=start,
                end=end,
                progress=False,
                auto_adjust=True,
                threads=True,
            )
        except Exception as e:
            print(f"  [ERROR] Batch failed: {e}")
            continue

        if raw.empty:
            print(f"  [WARN] No data returned for batch {batch_idx}")
            continue

        if isinstance(raw.columns, pd.MultiIndex):
            for ticker in batch:
                try:
                    df = raw.xs(ticker, axis=1, level=1)[["Open", "High", "Low", "Close", "Volume"]]
                    df = df.dropna(how="all")
                    if len(df) < MIN_ROWS:
                        print(f"  [SKIP] {ticker}: only {len(df)} rows (< {MIN_ROWS})")
                        continue
                    df.index.name = "Date"
                    df.to_csv(PRICES_DIR / f"{ticker}.csv")
                    results[ticker] = df
                    print(f"  [OK] {ticker}: {len(df)} rows saved → datasets/prices/{ticker}.csv")
                except (KeyError, TypeError) as e:
                    print(f"  [SKIP] {ticker}: {e}")
        else:
            # single ticker batch
            if len(batch) == 1:
                ticker = batch[0]
                df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
                if len(df) >= MIN_ROWS:
                    df.index.name = "Date"
                    df.to_csv(PRICES_DIR / f"{ticker}.csv")
                    results[ticker] = df
                    print(f"  [OK] {ticker}: {len(df)} rows saved → datasets/prices/{ticker}.csv")

    return results


# ── sentiment derivation ──────────────────────────────────────────────────────

def compute_and_save_sentiment(ticker: str, price_df: pd.DataFrame):
    """Derive synthetic sentiment from price_momentum and save as CSV."""
    try:
        from backtest.data_loader import _sentiment_from_price_momentum
        sentiment = _sentiment_from_price_momentum(price_df)
        out = pd.DataFrame({"sentiment_score": sentiment})
        out.index.name = "Date"
        out.to_csv(SENTIMENT_DIR / f"{ticker}.csv")
    except Exception as e:
        print(f"  [WARN] Sentiment for {ticker} failed: {e}")


# ── summary ───────────────────────────────────────────────────────────────────

def print_summary(results: dict[str, pd.DataFrame]):
    print("\n" + "=" * 60)
    print(f"  DATASET DOWNLOAD COMPLETE")
    print(f"  Saved {len(results)} price CSVs → datasets/prices/")
    if results:
        rows = [len(df) for df in results.values()]
        print(f"  Date rows/ticker: min={min(rows)}  max={max(rows)}  avg={int(sum(rows)/len(rows))}")
        total_mb = sum(
            (PRICES_DIR / f"{t}.csv").stat().st_size
            for t in results if (PRICES_DIR / f"{t}.csv").exists()
        ) / 1_048_576
        print(f"  Total size: {total_mb:.1f} MB")
    print("=" * 60)
    print("\nTo run a backtest using local CSV data:")
    print("  from backtest.runner import run_backtest")
    print("  result = run_backtest(start='2022-01-01', end='2024-01-01')")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    today = date.today().isoformat()
    two_years_ago = (date.today() - timedelta(days=365 * 5)).isoformat()

    p = argparse.ArgumentParser(
        description="Download S&P 500 OHLCV data as CSV files for SentXStock backtesting"
    )
    p.add_argument("--tickers",        type=str,  default="",          help="Comma-separated tickers (default: full universe)")
    p.add_argument("--sector",         type=str,  default="",          help="Filter by sector name")
    p.add_argument("--start",          type=str,  default=two_years_ago, help="Start date YYYY-MM-DD")
    p.add_argument("--end",            type=str,  default=today,         help="End date YYYY-MM-DD")
    p.add_argument("--with-sentiment", action="store_true",             help="Also save sentiment CSVs")
    p.add_argument("--skip-existing",  action="store_true", default=True, help="Skip tickers that already have CSVs (default: True)")
    p.add_argument("--no-skip",        action="store_true",             help="Re-download all, overwriting existing CSVs")
    return p.parse_args()


def main():
    args = parse_args()
    skip = args.skip_existing and not args.no_skip

    print("=" * 60)
    print("  SentXStock Dataset Downloader")
    print(f"  Range: {args.start} → {args.end}")
    print(f"  Output: datasets/prices/ (+ datasets/sentiment/ if --with-sentiment)")
    print("=" * 60)

    tickers = get_tickers(args)
    results = download_prices(tickers, args.start, args.end, skip_existing=skip)

    if args.with_sentiment:
        print(f"\n[SENTIMENT] Computing sentiment for {len(results)} tickers…")
        for ticker, df in results.items():
            compute_and_save_sentiment(ticker, df)
        print(f"[SENTIMENT] Saved → datasets/sentiment/")

    print_summary(results)


if __name__ == "__main__":
    main()
