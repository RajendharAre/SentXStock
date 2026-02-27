/**
 * Backtest page — configure and run strategy simulations, visualise results.
 *
 * Flow:
 *   1. User fills form (tickers, dates, strategy, risk)
 *   2. POST /api/backtest/run  →  polling GET /api/backtest/status every 3s
 *   3. On complete: fetch /api/backtest/latest  →  render charts + tables
 *   4. Optional: compare multiple saved runs
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts';
import {
  startBacktest, backtestStatus, backtestLatestResult, listBacktestResults,
  loadBacktestResult, compareBacktestResults,
} from '../services/api';
import { useTheme } from '../context/ThemeContext';

// ── helpers ──────────────────────────────────────────────────────────────────

const fmt = (v, precision = 2) =>
  v === undefined || v === null || v === '—' ? '—' : `${(v * 100).toFixed(precision)}%`;
const fmtNum = (v, p = 3) =>
  v === undefined || v === null || v === '—' ? '—' : Number(v).toFixed(p);
const fmtDollar = (v) =>
  v === undefined || v === null ? '—' : `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
const SECTOR_OPTIONS = [
  '', 'Technology', 'Consumer Discretionary', 'Financials', 'Health Care',
  'Industrials', 'Energy', 'Materials', 'Utilities', 'Real Estate',
  'Consumer Staples', 'Communication Services',
];

// ── MetricCard ────────────────────────────────────────────────────────────────
function MetricCard({ label, value, positive, negative }) {
  const pos = positive ?? (typeof value === 'string' ? false : value > 0);
  const neg = negative ?? (typeof value === 'string' ? false : value < 0);
  const color = pos ? 'text-emerald-400' : neg ? 'text-rose-400' : 'text-[var(--c-text)]';
  return (
    <div className="rounded-xl bg-[var(--c-surface)] border border-[var(--c-border)] p-4 flex flex-col gap-1">
      <span className="text-xs text-[var(--c-muted)]">{label}</span>
      <span className={`text-lg font-semibold ${color}`}>{value ?? '—'}</span>
    </div>
  );
}

// ── EquityChart ───────────────────────────────────────────────────────────────
function EquityChart({ equityCurve, initialCapital }) {
  const { theme } = useTheme();
  if (!equityCurve) return null;

  const data = Object.entries(equityCurve).map(([date, val]) => ({
    date: date.slice(5),              // "MM-DD"
    value: val,
  }));
  const min = Math.min(...data.map(d => d.value));
  const max = Math.max(...data.map(d => d.value));

  const tooltipStyle = {
    background: theme === 'dark' ? '#1e293b' : '#f8fafc',
    border: '1px solid var(--c-border)',
    color: 'var(--c-text)',
    fontSize: 12,
    borderRadius: 8,
  };

  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold text-[var(--c-sub)] mb-3">Equity Curve</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--c-border)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--c-muted)', fontSize: 10 }}
            interval={Math.floor(data.length / 8)} />
          <YAxis domain={[min * 0.98, max * 1.02]}
            tick={{ fill: 'var(--c-muted)', fontSize: 10 }}
            tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip contentStyle={tooltipStyle}
            formatter={v => [fmtDollar(v), 'Portfolio']} />
          <ReferenceLine y={initialCapital || 100000} stroke="var(--c-muted)"
            strokeDasharray="4 2" label={{ value: 'Start', fill: 'var(--c-muted)', fontSize: 10 }} />
          <Legend wrapperStyle={{ color: 'var(--c-sub)', fontSize: 12 }} />
          <Line type="monotone" dataKey="value" name="Portfolio Value"
            stroke="#6366f1" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── PerTickerTable ────────────────────────────────────────────────────────────
function PerTickerTable({ rows }) {
  if (!rows?.length) return null;
  const cols = [
    { key: 'ticker',        label: 'Ticker' },
    { key: 'cum_return',    label: 'Return',    fn: fmt },
    { key: 'ann_return',    label: 'Ann. Return',fn: fmt },
    { key: 'sharpe_ratio',  label: 'Sharpe',    fn: fmtNum },
    { key: 'max_drawdown',  label: 'Max DD',    fn: v => fmt(v, 2) },
    { key: 'win_rate',      label: 'Win Rate',  fn: fmt },
  ];
  return (
    <div className="mt-6 overflow-x-auto">
      <h3 className="text-sm font-semibold text-[var(--c-sub)] mb-3">Per-Ticker Metrics (top {Math.min(rows.length, 20)})</h3>
      <table className="w-full text-xs text-[var(--c-text)]">
        <thead>
          <tr className="border-b border-[var(--c-border)]">
            {cols.map(c => (
              <th key={c.key} className="py-2 px-3 text-left text-[var(--c-muted)] font-medium">{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((row, i) => (
            <tr key={i} className="border-b border-[var(--c-border2)] hover:bg-[var(--c-ghost)]">
              {cols.map(c => (
                <td key={c.key} className="py-2 px-3">
                  {c.fn ? c.fn(row[c.key]) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── CompareTable ──────────────────────────────────────────────────────────────
function CompareTable({ comparison }) {
  if (!comparison) return null;
  const { columns, rows } = comparison;
  return (
    <div className="mt-6 overflow-x-auto">
      <h3 className="text-sm font-semibold text-[var(--c-sub)] mb-3">Comparison</h3>
      <table className="w-full text-xs text-[var(--c-text)]">
        <thead>
          <tr className="border-b border-[var(--c-border)]">
            {columns.map((c, i) => (
              <th key={i} className="py-2 px-3 text-left text-[var(--c-muted)] font-medium">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-[var(--c-border2)] hover:bg-[var(--c-ghost)]">
              {row.map((cell, j) => (
                <td key={j} className="py-2 px-3">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main Backtest page ────────────────────────────────────────────────────────
export default function Backtest() {
  // form state
  const [tickers,          setTickersInput ]   = useState('');
  const [sector,           setSector]           = useState('');
  const [startDate,        setStartDate]        = useState('2022-01-01');
  const [endDate,          setEndDate]          = useState('2024-01-01');
  const [strategyVariant,  setStrategyVariant]  = useState('threshold');
  const [riskLevel,        setRiskLevel]        = useState('Medium');
  const [sentimentMode,    setSentimentMode]    = useState('price_momentum');
  const [initialCapital,   setInitialCapital]   = useState(100000);
  const [maxPositions,     setMaxPositions]     = useState(20);
  const [buyThreshold,     setBuyThreshold]     = useState(0.10);
  const [sellThreshold,    setSellThreshold]    = useState(0.10);
  const [allowShorts,      setAllowShorts]      = useState(false);
  const [runIdInput,       setRunIdInput]       = useState('');

  // runtime state
  const [status,           setStatus]           = useState('idle'); // idle | running | complete | error
  const [progress,         setProgress]         = useState('');
  const [result,           setResult]           = useState(null);
  const [error,            setError]            = useState(null);
  const [savedRuns,        setSavedRuns]        = useState([]);
  const [selectedRuns,     setSelectedRuns]     = useState([]);
  const [comparison,       setComparison]       = useState(null);
  const pollRef = useRef(null);

  // load saved runs on mount
  useEffect(() => {
    listBacktestResults().then(r => setSavedRuns(r.data)).catch(() => {});
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const handleRun = async () => {
    if (status === 'running') return;
    setStatus('running');
    setProgress('Starting…');
    setResult(null);
    setError(null);

    const tickerList = tickers
      ? tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean)
      : [];

    try {
      await startBacktest({
        tickers:            tickerList.length ? tickerList : null,
        sector:             sector || null,
        start:              startDate,
        end:                endDate,
        strategy_variant:   strategyVariant,
        risk_level:         riskLevel,
        sentiment_mode:     sentimentMode,
        initial_capital:    Number(initialCapital),
        max_open_positions: Number(maxPositions),
        buy_threshold:      Number(buyThreshold),
        sell_threshold:     -Math.abs(Number(sellThreshold)),
        allow_shorts:       allowShorts,
        run_id:             runIdInput || null,
      });
    } catch (e) {
      setStatus('error');
      setError('Failed to start backtest: ' + e.message);
      return;
    }

    pollRef.current = setInterval(async () => {
      try {
        const { data } = await backtestStatus();
        setProgress(data.progress || '');
        if (data.status === 'complete') {
          stopPolling();
          setStatus('complete');
          const res = await backtestLatestResult();
          setResult(res.data);
          // refresh saved runs list
          listBacktestResults().then(r => setSavedRuns(r.data)).catch(() => {});
        } else if (data.status === 'error') {
          stopPolling();
          setStatus('error');
          setError(data.error || 'Unknown error during backtest');
        }
      } catch {
        // network hiccup — keep polling
      }
    }, 3000);
  };

  const handleLoadRun = async (runId) => {
    try {
      const { data } = await loadBacktestResult(runId);
      setResult(data);
      setStatus('complete');
    } catch (e) {
      setError('Could not load run: ' + runId);
    }
  };

  const handleCompare = async () => {
    if (selectedRuns.length < 2) return;
    try {
      const { data } = await compareBacktestResults(selectedRuns);
      setComparison(data);
    } catch (e) {
      setError('Compare failed: ' + e.message);
    }
  };

  const toggleSelectedRun = (rid) => {
    setSelectedRuns(prev =>
      prev.includes(rid) ? prev.filter(r => r !== rid) : [...prev, rid]
    );
  };

  // cleanup
  useEffect(() => () => stopPolling(), [stopPolling]);

  const s = result?.summary || {};

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--c-text)]">Backtesting</h1>
        <p className="text-sm text-[var(--c-muted)] mt-1">
          Simulate your sentiment strategy on historical data across 500+ tickers.
        </p>
      </div>

      {/* ── Form + Saved Runs (side by side on lg) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* ── Config form ── */}
        <div className="lg:col-span-2 rounded-xl bg-[var(--c-surface)] border border-[var(--c-border)] p-5 space-y-4">
          <h2 className="text-sm font-semibold text-[var(--c-sub)]">Configuration</h2>

          {/* Tickers / Sector */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Tickers (comma-separated, leave blank for full universe)</span>
              <input
                type="text" value={tickers}
                onChange={e => setTickersInput(e.target.value)}
                placeholder="AAPL, MSFT, NVDA, TSLA …"
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm placeholder-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500"
              />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Sector (overrides tickers if blank)</span>
              <select value={sector} onChange={e => setSector(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
                {SECTOR_OPTIONS.map(s => <option key={s} value={s}>{s || '— All (universe) —'}</option>)}
              </select>
            </label>
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Start Date</span>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500" />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">End Date</span>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500" />
            </label>
          </div>

          {/* Strategy + Risk + Sentiment mode */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Strategy</span>
              <select value={strategyVariant} onChange={e => setStrategyVariant(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
                <option value="threshold">Threshold</option>
                <option value="blend">Blend (Momentum)</option>
                <option value="adaptive">Adaptive Risk</option>
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Risk Level</span>
              <select value={riskLevel} onChange={e => setRiskLevel(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
                <option>Low</option><option>Medium</option><option>High</option>
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Sentiment Mode</span>
              <select value={sentimentMode} onChange={e => setSentimentMode(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
                <option value="price_momentum">Price Momentum</option>
                <option value="cached_news">Cached News</option>
              </select>
            </label>
          </div>

          {/* Thresholds + Capital + Max positions */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Buy Threshold</span>
              <input type="number" step="0.01" min="0" max="1" value={buyThreshold}
                onChange={e => setBuyThreshold(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500" />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Sell Threshold</span>
              <input type="number" step="0.01" min="0" max="1" value={sellThreshold}
                onChange={e => setSellThreshold(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500" />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Initial Capital ($)</span>
              <input type="number" step="1000" min="1000" value={initialCapital}
                onChange={e => setInitialCapital(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500" />
            </label>
            <label className="block">
              <span className="text-xs text-[var(--c-muted)]">Max Open Positions</span>
              <input type="number" step="1" min="1" max="100" value={maxPositions}
                onChange={e => setMaxPositions(e.target.value)}
                className="mt-1 w-full rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-3 py-2 text-sm focus:outline-none focus:border-indigo-500" />
            </label>
          </div>

          {/* Extras */}
          <div className="flex flex-wrap gap-4 items-center">
            <label className="flex items-center gap-2 text-xs text-[var(--c-muted)]">
              <input type="checkbox" checked={allowShorts} onChange={e => setAllowShorts(e.target.checked)}
                className="accent-indigo-500" />
              Allow Short Selling
            </label>
            <label className="flex items-center gap-2 text-xs text-[var(--c-muted)]">
              Run ID:
              <input type="text" value={runIdInput} onChange={e => setRunIdInput(e.target.value)}
                placeholder="auto"
                className="w-36 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] px-2 py-1 text-xs focus:outline-none focus:border-indigo-500" />
            </label>
          </div>

          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={status === 'running'}
            className="w-full py-2.5 rounded-lg font-semibold text-sm bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {status === 'running' ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                {progress || 'Running backtest…'}
              </span>
            ) : 'Run Backtest'}
          </button>

          {/* Error */}
          {error && status === 'error' && (
            <p className="text-xs text-rose-400 mt-1">{error}</p>
          )}
        </div>

        {/* ── Saved Runs list ── */}
        <div className="rounded-xl bg-[var(--c-surface)] border border-[var(--c-border)] p-4 space-y-2 overflow-y-auto max-h-[440px]">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-sm font-semibold text-[var(--c-sub)]">Saved Runs</h2>
            {selectedRuns.length >= 2 && (
              <button onClick={handleCompare}
                className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-2 py-1 rounded-lg transition-colors">
                Compare ({selectedRuns.length})
              </button>
            )}
          </div>
          {savedRuns.length === 0 && (
            <p className="text-xs text-[var(--c-muted)]">No saved runs yet. Run a backtest to save results.</p>
          )}
          {savedRuns.map(run => (
            <div key={run.run_id}
              className="rounded-lg border border-[var(--c-border2)] bg-[var(--c-bg)] p-3 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[var(--c-text)]">{run.run_id}</span>
                <input type="checkbox"
                  checked={selectedRuns.includes(run.run_id)}
                  onChange={() => toggleSelectedRun(run.run_id)}
                  className="accent-indigo-500" />
              </div>
              <div className="text-xs text-[var(--c-muted)]">
                {run.strategy}  ·  {run.start}→{run.end}
              </div>
              <div className="flex gap-3 text-xs">
                {run.cum_return != null && (
                  <span className={run.cum_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                    {fmt(run.cum_return)}
                  </span>
                )}
                {run.sharpe != null && (
                  <span className="text-[var(--c-muted)]">Sharpe {fmtNum(run.sharpe)}</span>
                )}
              </div>
              <button
                onClick={() => handleLoadRun(run.run_id)}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
                Load →
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Results ── */}
      {result && (
        <div className="rounded-xl bg-[var(--c-surface)] border border-[var(--c-border)] p-5">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <h2 className="text-sm font-semibold text-[var(--c-sub)]">
              Results — {result.strategy}
            </h2>
            <span className="text-xs text-[var(--c-muted)]">
              {result.start} → {result.end}  ·  {result.tickers?.length} tickers  ·  {result.n_trades} trades
            </span>
          </div>

          {/* Summary metric cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-7 gap-3">
            <MetricCard label="Cum. Return"   value={fmt(s.cum_return)}      positive={s.cum_return > 0} negative={s.cum_return < 0} />
            <MetricCard label="Ann. Return"   value={fmt(s.ann_return)}      positive={s.ann_return > 0} negative={s.ann_return < 0} />
            <MetricCard label="Volatility"    value={fmt(s.ann_volatility)} />
            <MetricCard label="Sharpe"        value={fmtNum(s.sharpe_ratio)} positive={s.sharpe_ratio > 1} negative={s.sharpe_ratio < 0} />
            <MetricCard label="Sortino"       value={fmtNum(s.sortino_ratio)} />
            <MetricCard label="Max Drawdown"  value={fmt(s.max_drawdown)}   negative />
            <MetricCard label="Win Rate"      value={fmt(s.win_rate)}        positive={s.win_rate > 0.5} />
          </div>

          {/* Second row: extra metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 gap-3 mt-3">
            <MetricCard label="Calmar"        value={fmtNum(s.calmar_ratio)} />
            <MetricCard label="Profit Factor" value={fmtNum(s.profit_factor)} positive={s.profit_factor > 1} />
            <MetricCard label="VaR (95%)"     value={fmt(s.var_95)}          negative />
            {s.alpha_ann !== undefined && <MetricCard label="Alpha (ann.)" value={fmt(s.alpha_ann)} positive={s.alpha_ann > 0} negative={s.alpha_ann < 0} />}
            {s.beta      !== undefined && <MetricCard label="Beta"         value={fmtNum(s.beta, 2)} />}
            {s.info_ratio !== undefined && <MetricCard label="Info Ratio"  value={fmtNum(s.info_ratio)} />}
          </div>

          {/* Equity curve */}
          <EquityChart equityCurve={result.equity_curve} initialCapital={Number(initialCapital)} />

          {/* Per-ticker table */}
          <PerTickerTable rows={result.per_ticker} />
        </div>
      )}

      {/* ── Comparison ── */}
      {comparison && (
        <div className="rounded-xl bg-[var(--c-surface)] border border-[var(--c-border)] p-5">
          <CompareTable comparison={comparison} />
        </div>
      )}
    </div>
  );
}
