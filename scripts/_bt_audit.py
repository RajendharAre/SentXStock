"""Step-by-step backtest audit."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.universe_india import IndiaUniverse
from backtest.universe import Universe
from backtest.runner import run_backtest

print("=" * 60)
print("STEP 1: UNIVERSE CHECK")
print("=" * 60)
default_u = Universe()
india_u   = IndiaUniverse()
print(f"runner.py default Universe()  : {len(default_u.tickers)} tickers — {default_u.tickers[:3]} (US S&P500!)")
print(f"IndiaUniverse tickers         : {len(india_u.tickers)} unique NSE tickers")
print(f"Sector breakdown:")
for s, ts in india_u.tickers_by_sector().items():
    print(f"  {s:<38} {len(ts):>3} tickers")

print()
print("=" * 60)
print("STEP 2: 20 NSE STOCKS BACKTEST (2 years, ^NSEI benchmark)")
print("=" * 60)
sample = india_u.tickers[:20]
print(f"Testing: {sample}")
print()

try:
    res = run_backtest(
        tickers          = sample,
        start            = "2024-01-01",
        end              = "2025-12-31",
        benchmark_ticker = "^NSEI",
        initial_capital  = 100_000,
        buy_threshold    = 0.05,
        sell_threshold   = -0.05,
        save_results     = False,
        verbose          = True,
    )
    m = res.summary
    print()
    print("--- RESULTS ---")
    print(f"Tickers loaded   : {len(res.ticker_list)}/{len(sample)}")
    print(f"Trades executed  : {m.get('total_trades', 0)}")
    print(f"Total return     : {m.get('total_return_pct', 0):.2f}%")
    print(f"Benchmark return : {m.get('benchmark_return_pct', 0):.2f}%")
    print(f"Sharpe ratio     : {m.get('sharpe_ratio', 0):.2f}")
    print(f"Max drawdown     : {m.get('max_drawdown_pct', 0):.2f}%")
    print(f"Win rate         : {m.get('win_rate_pct', 0):.1f}%")
    print()
    print("Top 5 tickers by return:")
    for t in res.per_ticker_metrics[:5]:
        print(f"  {t.get('ticker',''):<22} return={t.get('total_return_pct',0):+.2f}%  trades={t.get('trades',0)}  sharpe={t.get('sharpe',0):.2f}")

except Exception as e:
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("STEP 3: FULL 361 NSE UNIVERSE — DATA LOAD TEST (no trading)")
print("=" * 60)
from backtest.data_loader import load_backtest_data
print(f"Testing all {len(india_u.tickers)} tickers data download...")
try:
    raw = load_backtest_data(
        tickers        = india_u.tickers,
        start          = "2025-01-01",
        end            = "2025-12-31",
        sentiment_mode = "price_momentum",
    )
    ok_tickers     = [t for t,v in raw.items() if not v["prices"].empty]
    failed_tickers = [t for t in india_u.tickers if t not in raw]
    print(f"Successfully loaded : {len(ok_tickers)}/{len(india_u.tickers)} tickers")
    print(f"Failed/no data      : {len(failed_tickers)} tickers")
    if failed_tickers:
        print(f"Failed examples     : {failed_tickers[:10]}")
except Exception as e:
    import traceback
    traceback.print_exc()
