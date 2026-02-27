"""
India Dataset Downloader
========================
Downloads 5-year OHLCV data for all 500 NSE-listed companies and saves
as CSV files in:

    datasets/prices/<TICKER>.csv    (e.g. TCS.NS.csv)

Also optionally pre-computes synthetic sentiment CSVs in:

    datasets/sentiment/<TICKER>.csv

Usage
-----
  # Full NSE 500 universe (default: 5 years to today)
  python scripts/download_india_datasets.py

  # Custom date range
  python scripts/download_india_datasets.py --start 2021-01-01 --end 2026-01-31

  # Specific tickers
  python scripts/download_india_datasets.py --tickers TCS.NS,INFY.NS,RELIANCE.NS

  # Specific sector
  python scripts/download_india_datasets.py --sector Technology

  # Include sentiment CSV generation
  python scripts/download_india_datasets.py --with-sentiment

  # Skip already-downloaded tickers (resume)
  python scripts/download_india_datasets.py --skip-existing

  # Also download benchmark (Nifty 50)
  python scripts/download_india_datasets.py --with-benchmark

Notes
-----
- NSE tickers use .NS suffix (e.g. TCS.NS)
- yfinance `auto_adjust=True` is used (adjusts for splits/dividends)
- Requires: pip install yfinance pandas
"""

import argparse
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import yfinance as yf

PRICES_DIR    = ROOT / "datasets" / "prices"
SENTIMENT_DIR = ROOT / "datasets" / "sentiment"
PRICES_DIR.mkdir(parents=True, exist_ok=True)
SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 25   # smaller batches for NSE (yfinance can be slow for Indian stocks)
MIN_ROWS   = 30


# ── Ticker resolution ─────────────────────────────────────────────────────────

def get_tickers(args) -> list[str]:
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        # Ensure .NS suffix
        result = []
        for t in tickers:
            if not t.endswith(".NS") and not t.endswith(".BO") and not t.startswith("^"):
                t = t + ".NS"
            result.append(t)
        return result

    from backtest.universe_india import IndiaUniverse
    u = IndiaUniverse()

    if args.sector:
        tickers = u.tickers_by_sector().get(args.sector)
        if not tickers:
            print(f"[ERROR] Unknown sector '{args.sector}'")
            print(f"  Valid sectors: {', '.join(u.sectors())}")
            sys.exit(1)
        print(f"[INFO] Sector '{args.sector}': {len(tickers)} tickers")
    else:
        tickers = u.tickers
        print(f"[INFO] Full NSE universe: {len(tickers)} tickers")

    return tickers


# ── Download ──────────────────────────────────────────────────────────────────

def download_prices(
    tickers: list[str],
    start: str,
    end: str,
    skip_existing: bool = False,
    verbose: bool = True,
) -> dict[str, pd.DataFrame]:
    """Download and save OHLCV CSVs for all tickers."""
    results: dict[str, pd.DataFrame] = {}

    if skip_existing:
        remaining = []
        for t in tickers:
            csv_path = PRICES_DIR / f"{t}.csv"
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                    results[t] = df
                except Exception:
                    remaining.append(t)
            else:
                remaining.append(t)
        if verbose and len(results):
            print(f"[INFO] Loaded {len(results)} existing CSVs. Downloading {len(remaining)} missing tickers.")
    else:
        remaining = list(tickers)

    total_batches = max(1, (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE)

    for batch_idx, i in enumerate(range(0, len(remaining), BATCH_SIZE), 1):
        batch = remaining[i : i + BATCH_SIZE]
        if verbose:
            print(f"\n[BATCH {batch_idx}/{total_batches}] {len(batch)} tickers: "
                  f"{', '.join(batch[:5])}{'...' if len(batch) > 5 else ''}")

        try:
            raw = yf.download(
                batch,
                start=start,
                end=end,
                progress=False,
                auto_adjust=True,
                threads=True,
                group_by="ticker",
            )
        except Exception as e:
            print(f"  [ERROR] Batch {batch_idx} download failed: {e}")
            continue

        if raw is None or raw.empty:
            print(f"  [WARN] No data returned for batch {batch_idx}")
            continue

        if len(batch) == 1:
            # Single ticker — flat columns
            ticker = batch[0]
            try:
                df = _extract_single(raw, ticker)
                if df is not None:
                    results[ticker] = df
                    _save_csv(ticker, df, verbose)
            except Exception as e:
                print(f"  [SKIP] {ticker}: {e}")
        else:
            # Multi-ticker — MultiIndex(field, ticker) OR (ticker, field)
            for ticker in batch:
                try:
                    df = _extract_multi(raw, ticker)
                    if df is not None:
                        results[ticker] = df
                        _save_csv(ticker, df, verbose)
                    else:
                        if verbose:
                            print(f"  [SKIP] {ticker}: no data")
                except Exception as e:
                    if verbose:
                        print(f"  [SKIP] {ticker}: {e}")

    return results


def _extract_single(raw: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    cols_needed = ["Open", "High", "Low", "Close", "Volume"]
    # Normalise column names
    raw.columns = [str(c).strip().title() for c in raw.columns]
    missing = [c for c in cols_needed if c not in raw.columns]
    if missing:
        return None
    df = raw[cols_needed].dropna(how="all")
    return df if len(df) >= MIN_ROWS else None


def _extract_multi(raw: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    cols_needed = ["Open", "High", "Low", "Close", "Volume"]
    if isinstance(raw.columns, pd.MultiIndex):
        # Try (field, ticker) layout
        try:
            df = raw.xs(ticker, axis=1, level=1)
            df.columns = [str(c).strip().title() for c in df.columns]
            missing = [c for c in cols_needed if c not in df.columns]
            if missing:
                # Try (ticker, field) layout
                df = raw.xs(ticker, axis=1, level=0)
                df.columns = [str(c).strip().title() for c in df.columns]
            df = df[cols_needed].dropna(how="all")
            return df if len(df) >= MIN_ROWS else None
        except (KeyError, TypeError):
            return None
    return None


def _save_csv(ticker: str, df: pd.DataFrame, verbose: bool):
    df.index.name = "Date"
    path = PRICES_DIR / f"{ticker}.csv"
    df.to_csv(path)
    if verbose:
        print(f"  [OK] {ticker}: {len(df)} rows ({df.index[0].date()} to {df.index[-1].date()}) "
              f"→ datasets/prices/{ticker}.csv")


# ── Sentiment ─────────────────────────────────────────────────────────────────

def compute_and_save_sentiment(ticker: str, price_df: pd.DataFrame, verbose: bool = True):
    """Derive price-momentum sentiment and save as CSV."""
    try:
        from backtest.data_loader import _sentiment_from_price_momentum
        sentiment = _sentiment_from_price_momentum(price_df)
        out = pd.DataFrame({"sentiment_score": sentiment})
        out.index.name = "Date"
        path = SENTIMENT_DIR / f"{ticker}.csv"
        out.to_csv(path)
        if verbose:
            print(f"  [SENTIMENT] {ticker} → datasets/sentiment/{ticker}.csv")
    except Exception as e:
        if verbose:
            print(f"  [WARN] Sentiment for {ticker} failed: {e}")


# ── Benchmark ─────────────────────────────────────────────────────────────────

def download_benchmark(start: str, end: str, verbose: bool = True):
    """Download Nifty 50 index (^NSEI) as benchmark."""
    try:
        raw = yf.download("^NSEI", start=start, end=end, progress=False, auto_adjust=True)
        if raw.empty:
            print("[WARN] Nifty 50 benchmark data empty")
            return
        df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna(how="all")
        df.index.name = "Date"
        path = PRICES_DIR / "^NSEI.csv"
        df.to_csv(path)
        if verbose:
            print(f"[BENCHMARK] Nifty 50 (^NSEI): {len(df)} rows → datasets/prices/^NSEI.csv")
    except Exception as e:
        print(f"[ERROR] Benchmark download failed: {e}")


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(results: dict):
    print("\n" + "=" * 65)
    print("  INDIA DATASET DOWNLOAD COMPLETE")
    print(f"  {len(results)} price CSVs saved → datasets/prices/")
    if results:
        rows = [len(df) for df in results.values()]
        print(f"  Rows/ticker: min={min(rows)}  max={max(rows)}  avg={int(sum(rows)/len(rows))}")
        total_mb = sum(
            (PRICES_DIR / f"{t}.csv").stat().st_size
            for t in results if (PRICES_DIR / f"{t}.csv").exists()
        ) / 1_048_576
        print(f"  Total size: {total_mb:.1f} MB")
    print("=" * 65)
    print("\nQuick start:")
    print("  from backtest.runner import run_backtest")
    print("  result = run_backtest(start='2022-01-01', end='2026-01-31')")
    print()


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():
    today       = "2026-01-31"      # fixed end date as per requirements
    five_ago    = "2021-01-01"

    p = argparse.ArgumentParser(
        description="Download NSE 500 OHLCV data as CSV files for SentXStock"
    )
    p.add_argument("--tickers",        type=str, default="",
                   help="Comma-separated tickers (e.g. TCS.NS,INFY.NS). Default: full NSE 500.")
    p.add_argument("--sector",         type=str, default="",
                   help="Filter by sector. E.g. 'Technology', 'Healthcare'")
    p.add_argument("--start",          type=str, default=five_ago,
                   help="Start date YYYY-MM-DD (default 5 years ago)")
    p.add_argument("--end",            type=str, default=today,
                   help="End date YYYY-MM-DD (default 2026-01-31)")
    p.add_argument("--with-sentiment", action="store_true",
                   help="Also save sentiment CSVs in datasets/sentiment/")
    p.add_argument("--with-benchmark", action="store_true",
                   help="Also download Nifty 50 benchmark (^NSEI)")
    p.add_argument("--skip-existing",  action="store_true", default=True,
                   help="Skip tickers that already have CSVs (default: True)")
    p.add_argument("--no-skip",        action="store_true",
                   help="Re-download all tickers, overwriting existing CSVs")
    p.add_argument("--quiet",          action="store_true",
                   help="Suppress per-ticker output")
    return p.parse_args()


def main():
    args    = parse_args()
    verbose = not args.quiet
    skip    = args.skip_existing and not args.no_skip

    print("=" * 65)
    print("  SentXStock — Indian NSE Dataset Downloader")
    print(f"  Range  : {args.start} to {args.end}")
    print(f"  Output : datasets/prices/   (sentiment: datasets/sentiment/)")
    print("=" * 65)

    tickers = get_tickers(args)

    if args.with_benchmark:
        download_benchmark(args.start, args.end, verbose=verbose)

    results = download_prices(
        tickers=tickers,
        start=args.start,
        end=args.end,
        skip_existing=skip,
        verbose=verbose,
    )

    if args.with_sentiment:
        print(f"\n[SENTIMENT] Computing for {len(results)} tickers…")
        for ticker, df in results.items():
            compute_and_save_sentiment(ticker, df, verbose=verbose)

    print_summary(results)


if __name__ == "__main__":
    main()
