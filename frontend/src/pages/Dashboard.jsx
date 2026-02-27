/**
 * Dashboard — Company-Centric NSE Sentiment Research Terminal
 * Module 4 + Module 5 (Hidden Auto-Backtest)
 *
 * Flow:
 *  1. Search bar with sector filter → autocomplete from 500 NSE companies
 *  2. Select company → analyzeTicker() fires  +  silent backtest auto-starts
 *  3. Backtest polls in background; results injected as Performance Summary
 *  4. UI: company header | sentiment | recommendation | risk | allocation | news | metrics | perf summary
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search, X, Loader2, AlertCircle, Activity, Zap,
  ExternalLink, ChevronDown, RefreshCw, ShieldCheck, TrendingUp,
} from 'lucide-react';
import {
  searchCompanies, getSectors, analyzeTicker,
  getDashboard, runAnalysis, analyzeStatus,
  startBacktestForTicker, backtestStatus, backtestLatestResult,
} from '../services/api';
import { DownloadReportButton } from '../components/PDFReport';


// ── Helpers ───────────────────────────────────────────────────────────────────

function sentimentColor(score) {
  if (typeof score !== 'number') return 'text-[var(--c-muted)]';
  if (score > 0.15)  return 'text-emerald-400';
  if (score > 0.05)  return 'text-green-400';
  if (score < -0.15) return 'text-rose-400';
  if (score < -0.05) return 'text-orange-400';
  return 'text-amber-400';
}

function sentimentBg(score) {
  if (typeof score !== 'number') return 'bg-[var(--c-border)] text-[var(--c-muted)]';
  if (score > 0.05)  return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
  if (score < -0.05) return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
  return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
}

function recBadge(rec) {
  const r = (rec || '').toLowerCase();
  if (r.includes('strong buy'))  return { label: 'Strong Buy',  cls: 'bg-emerald-500/10 border-emerald-400/40 text-emerald-400' };
  if (r.includes('buy'))         return { label: 'Buy',         cls: 'bg-green-500/10 border-green-400/40 text-green-400' };
  if (r.includes('strong sell')) return { label: 'Strong Sell', cls: 'bg-rose-500/10 border-rose-400/40 text-rose-400' };
  if (r.includes('sell'))        return { label: 'Sell',        cls: 'bg-orange-500/10 border-orange-400/40 text-orange-400' };
  return { label: 'Hold', cls: 'bg-amber-500/10 border-amber-400/40 text-amber-400' };
}

function fmt(v, prefix = '', suffix = '', decimals = 2) {
  if (v === null || v === undefined || v === '') return '—';
  const n = parseFloat(v);
  if (isNaN(n)) return v;
  return `${prefix}${n.toFixed(decimals)}${suffix}`;
}

function fmtCr(v) {
  if (!v) return '—';
  const n = parseFloat(v);
  if (isNaN(n)) return v;
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toFixed(0)}`;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color }) {
  return (
    <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-4 flex flex-col gap-1">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)]">{label}</span>
      <span className={`text-xl font-bold mono leading-none ${color || 'text-[var(--c-text)]'}`}>{value}</span>
      {sub && <span className="text-[11px] text-[var(--c-muted)]">{sub}</span>}
    </div>
  );
}

function SentimentBar({ label, value, total, color }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-[12px]">
      <span className="w-16 text-[var(--c-muted)]">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-[var(--c-border2)]">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`w-8 text-right font-mono font-bold ${color.replace('bg-', 'text-')}`}>{pct}%</span>
      <span className="w-8 text-right text-[var(--c-dimmer)]">{value}</span>
    </div>
  );
}

// ── Company Search ────────────────────────────────────────────────────────────

function CompanySearch({ onSelect, loading }) {
  const [sectors, setSectors]       = useState([]);
  const [sectorCounts, setCounts]   = useState({});
  const [sector, setSector]         = useState('');
  const [query, setQuery]           = useState('');
  const [results, setResults]       = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [searching, setSearching]   = useState(false);
  const [open, setOpen]             = useState(false);
  const dropRef = useRef(null);

  // Load sector list + counts once on mount
  useEffect(() => {
    getSectors()
      .then((r) => {
        // new format: { sectors: [...], counts: {...} }
        // fallback: old format was a plain array
        const raw = r.data;
        if (Array.isArray(raw)) {
          setSectors(raw);
        } else {
          setSectors(raw?.sectors || []);
          setCounts(raw?.counts  || {});
        }
      })
      .catch(() => {});
  }, []);

  // Fire whenever query OR sector changes
  useEffect(() => {
    // If no query AND no sector selected → clear results
    if (!query && !sector) {
      setResults([]);
      setOpen(false);
      return;
    }

    const delay = query ? 250 : 0; // instant for sector-browse, debounce for typing
    const t = setTimeout(async () => {
      setSearching(true);
      try {
        // Pass both query and sector to server — server does the filtering
        const r = await searchCompanies(query, sector);

        // New response: { results: [...], total: N }  ← server always returns this shape now
        const raw = r.data;
        let list;
        if (raw && Array.isArray(raw.results)) {
          list = raw.results;
          setTotalCount(raw.total ?? list.length);
        } else if (Array.isArray(raw)) {
          // Safety fallback for old format
          list = raw;
          setTotalCount(list.length);
        } else {
          list = [];
          setTotalCount(0);
        }

        setResults(list.slice(0, 30));  // show up to 30 in dropdown
        setOpen(list.length > 0);
      } catch {
        setResults([]);
        setTotalCount(0);
      }
      setSearching(false);
    }, delay);
    return () => clearTimeout(t);
  }, [query, sector]);

  // Close dropdown on outside click
  useEffect(() => {
    const fn = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', fn);
    return () => document.removeEventListener('mousedown', fn);
  }, []);

  const pick = (company) => { onSelect(company); setQuery(''); setOpen(false); };

  const handleSectorChange = (e) => {
    setSector(e.target.value);
    setResults([]);
    setOpen(false);
    // effect above will re-run automatically and fetch sector companies
  };

  const clearQuery = () => { setQuery(''); if (!sector) setOpen(false); };

  return (
    <div className="flex gap-2 relative" ref={dropRef}>
      {/* ── Sector dropdown ── */}
      <div className="relative shrink-0">
        <select
          value={sector}
          onChange={handleSectorChange}
          className="h-10 pl-3 pr-8 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-sub)] text-[13px] font-medium focus:outline-none focus:border-indigo-500 appearance-none cursor-pointer transition-colors"
        >
          <option value="">All Sectors</option>
          {sectors.map((s) => (
            <option key={s} value={s}>
              {s}{sectorCounts[s] ? ` (${sectorCounts[s]})` : ''}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--c-muted)] pointer-events-none" />
      </div>

      {/* ── Text search ── */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--c-dimmer)]" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={sector ? `Search within ${sector}…` : 'Search company or NSE ticker…'}
          disabled={loading}
          className="w-full h-10 pl-9 pr-9 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-text)] text-[13px] placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 disabled:opacity-50 transition-colors"
        />
        {(searching || loading) && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--c-dimmer)] animate-spin" />
        )}
        {query && !searching && (
          <button onClick={clearQuery} className="absolute right-3 top-1/2 -translate-y-1/2">
            <X className="w-4 h-4 text-[var(--c-dimmer)] hover:text-[var(--c-muted)]" />
          </button>
        )}

        {/* ── Results dropdown ── */}
        {open && results.length > 0 && (
          <div className="absolute top-full left-0 mt-1 w-full z-50 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] shadow-xl overflow-hidden">
            {/* Header row showing count */}
            <div className="px-4 py-2 border-b border-[var(--c-border)] flex items-center justify-between">
              <span className="text-[11px] font-semibold text-[var(--c-dimmer)] uppercase tracking-wider">
                {sector || 'All Sectors'}
              </span>
              <span className="text-[11px] text-[var(--c-muted)]">
                {totalCount > 30
                  ? `Showing 30 of ${totalCount}`
                  : `${totalCount} compan${totalCount === 1 ? 'y' : 'ies'}`}
              </span>
            </div>
            <div className="max-h-72 overflow-y-auto">
              {results.map((c) => (
                <button
                  key={c.ticker}
                  onClick={() => pick(c)}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-[var(--c-border)]/40 transition-colors text-left"
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <span className="text-[13px] font-semibold text-[var(--c-text)] truncate block">{c.name || c.ticker}</span>
                    <span className="text-[11px] mono text-indigo-400">{c.ticker}</span>
                  </div>
                  <span className="text-[10px] text-[var(--c-dimmer)] shrink-0 text-right">{c.sector}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* No results message */}
        {open && (query || sector) && results.length === 0 && !searching && (
          <div className="absolute top-full left-0 mt-1 w-full z-50 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] shadow-xl px-4 py-3">
            <p className="text-[12px] text-[var(--c-muted)]">
              No companies found{query ? ` for "${query}"` : ''}{sector ? ` in ${sector}` : ''}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Performance Summary card (injected silently after backtest completes) ──────

function PerfStat({ label, value, color, note }) {
  return (
    <div className="flex flex-col gap-1 text-center">
      <span className={`text-2xl font-bold mono leading-none ${color || 'text-[var(--c-text)]'}`}>{value}</span>
      <span className="text-[11px] font-medium text-[var(--c-sub)]">{label}</span>
      {note && <span className="text-[10px] text-[var(--c-dimmer)]">{note}</span>}
    </div>
  );
}

function PerformanceSummary({ btResult, btLoading }) {
  if (!btResult && !btLoading) return null;

  const sm = btResult?.summary || {};
  const pct = (v) => (typeof v === 'number' ? `${(v * 100).toFixed(2)}%` : '—');
  const pp  = (v) => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${(v * 100).toFixed(2)}%` : '—');

  const cumRet  = sm.cum_return  ?? null;
  const annRet  = sm.ann_return  ?? null;
  const sharpe  = sm.sharpe_ratio ?? null;
  const maxDd   = sm.max_drawdown ?? null;
  const winRate = sm.win_rate     ?? null;
  const alpha   = sm.alpha        ?? null;

  const retColor = cumRet === null ? 'text-[var(--c-text)]' : cumRet >= 0 ? 'text-emerald-400' : 'text-rose-400';
  const ddColor  = 'text-rose-400';
  const sharpeColor = sharpe === null ? 'text-[var(--c-text)]' : sharpe >= 1 ? 'text-emerald-400' : sharpe >= 0 ? 'text-amber-400' : 'text-rose-400';

  return (
    <div className="rounded-xl border border-indigo-500/20 bg-indigo-600/5 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3 border-b border-indigo-500/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-indigo-400" />
          <span className="text-[12px] font-semibold text-[var(--c-text)]">
            3-Year Backtest Performance
          </span>
          <span className="text-[10px] text-[var(--c-muted)]">Jan 2023 – Jan 2026 · NSE · Nifty 50 Benchmark</span>
        </div>
        {btLoading && (
          <div className="flex items-center gap-1.5 text-[11px] text-indigo-400">
            <Loader2 className="w-3 h-3 animate-spin" />
            Running backtest…
          </div>
        )}
        {btResult && !btLoading && (
          <span className="text-[10px] px-2 py-0.5 rounded border border-emerald-500/30 bg-emerald-500/5 text-emerald-400">
            Walk-Forward · Auto
          </span>
        )}
      </div>

      {/* Loading placeholder */}
      {btLoading && !btResult && (
        <div className="px-5 py-8 flex flex-col items-center gap-2">
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
          <p className="text-[12px] text-[var(--c-muted)]">
            Running 3-year walk-forward backtest on NSE price data…
          </p>
          <p className="text-[11px] text-[var(--c-dimmer)]">
            This runs silently in the background and will appear here when ready.
          </p>
        </div>
      )}

      {/* Results */}
      {btResult && (
        <div className="p-5 space-y-5">
          {/* Main stat row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 divide-x divide-indigo-500/10">
            <PerfStat
              label="Strategy Return"
              value={pp(cumRet)}
              color={retColor}
              note={`${pp(annRet)} annualised`}
            />
            <PerfStat
              label="Max Drawdown"
              value={pct(maxDd)}
              color={ddColor}
              note="Worst peak-to-trough"
            />
            <PerfStat
              label="Sharpe Ratio"
              value={sharpe !== null ? sharpe.toFixed(3) : '—'}
              color={sharpeColor}
              note="Risk-adjusted return"
            />
            <PerfStat
              label="Win Rate"
              value={pct(winRate)}
              color="text-amber-400"
              note="Days with positive return"
            />
          </div>

          {/* Secondary metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[12px]">
            {[
              ['Annualised Volatility', typeof sm.ann_volatility === 'number' ? pct(sm.ann_volatility) : '—'],
              ['Sortino Ratio',         typeof sm.sortino_ratio  === 'number' ? sm.sortino_ratio.toFixed(3) : '—'],
              ['Calmar Ratio',          typeof sm.calmar_ratio   === 'number' ? sm.calmar_ratio.toFixed(3)  : '—'],
              ['Alpha vs Nifty 50',     alpha !== null ? pp(alpha) : '—'],
            ].map(([k, v]) => (
              <div key={k} className="flex flex-col gap-0.5">
                <span className="text-[10px] text-[var(--c-dimmer)] uppercase tracking-wide">{k}</span>
                <span className="font-bold mono text-[var(--c-text)]">{v}</span>
              </div>
            ))}
          </div>

          {/* Backtest params strip */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-[var(--c-dimmer)] border-t border-indigo-500/10 pt-3">
            <span>Period: Jan 2023 – Jan 2026</span>
            <span>·</span>
            <span>Benchmark: Nifty 50 (^NSEI)</span>
            <span>·</span>
            <span>Slippage: 5 bps</span>
            <span>·</span>
            <span>Strategy: Sentiment-Momentum Threshold</span>
            <span>·</span>
            <span className="text-amber-300/70">For research purposes only. Not investment advice.</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Company Analysis Panel ────────────────────────────────────────────────────

function AnalysisPanel({ company, data, onRefresh, btResult, btLoading }) {
  const s     = data.sentiment || {};
  const score = s.score ?? data.score ?? 0;
  const label = s.label || data.label || (score > 0.05 ? 'Bullish' : score < -0.05 ? 'Bearish' : 'Neutral');
  const bull  = s.positive ?? data.bullish ?? 0;
  const bear  = s.negative ?? data.bearish ?? 0;
  const flat  = s.neutral  ?? data.neutral  ?? 0;
  const total = (s.total_headlines ?? (bull + bear + flat)) || 1;

  const rec = data.recommendation || data.signal || 'Hold';
  const { label: recLabel, cls: recCls } = recBadge(rec);
  const confidence  = data.confidence ?? data.confidence_pct ?? null;
  const explanation = data.explanation || data.ai_explanation || data.summary || null;
  const metrics     = data.metrics || data.financial_metrics || {};
  const alloc       = data.allocation || {};
  const news        = data.news || data.headlines || data.articles || [];
  const isMock      = data.is_mock_data === true;

  return (
    <div className="space-y-5">
      {/* Company header */}
      <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-[var(--c-text)]">{data.name || company.name}</h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">{data.ticker || company.ticker}</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold border border-[var(--c-border)] text-[var(--c-muted)]">{data.exchange || 'NSE'}</span>
              <span className="px-2 py-0.5 rounded text-[11px] border border-[var(--c-border)] text-[var(--c-muted)]">{data.sector || company.sector}</span>
              {isMock && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold border border-amber-500/40 bg-amber-500/10 text-amber-400">
                  ⚠ Simulated Data
                </span>
              )}
            </div>
            {explanation && <p className="mt-2 text-[12px] text-[var(--c-muted)] max-w-2xl leading-relaxed">{explanation}</p>}
            {isMock && (
              <p className="mt-1.5 text-[11px] text-amber-400/80 max-w-2xl">
                Live news APIs (Finnhub / NewsAPI) returned no results for this ticker. Sentiment is based on simulated sector-relevant articles. Set{' '}
                <code className="px-1 py-0.5 rounded bg-[var(--c-border)] font-mono text-[10px]">FINNHUB_API_KEY</code> and{' '}
                <code className="px-1 py-0.5 rounded bg-[var(--c-border)] font-mono text-[10px]">NEWSAPI_KEY</code> in <code className="px-1 py-0.5 rounded bg-[var(--c-border)] font-mono text-[10px]">.env</code> for live analysis.
              </p>
            )}
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`inline-block px-5 py-2 rounded-lg border text-[15px] font-extrabold tracking-wide ${recCls}`}>{recLabel}</span>
            {confidence !== null && (
              <div className="text-center">
                <span className="text-2xl font-bold mono text-[var(--c-text)]">{Number(confidence).toFixed(1)}%</span>
                <p className="text-[10px] text-[var(--c-dimmer)] uppercase tracking-wide">Confidence</p>
              </div>
            )}
            <div className="flex items-center gap-2 ml-auto">
              <DownloadReportButton company={company} data={data} btResult={btResult} />
              <button onClick={onRefresh} className="flex items-center gap-1 text-[11px] text-[var(--c-muted)] hover:text-indigo-400 transition-colors h-8 px-2">
                <RefreshCw className="w-3.5 h-3.5" />Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Score strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Sentiment Score" value={`${score > 0 ? '+' : ''}${score.toFixed(3)}`} color={sentimentColor(score)} sub={label} />
        <StatCard label="Bullish Headlines" value={bull} color="text-emerald-400" sub={`${Math.round(bull/total*100)}% of ${total}`} />
        <StatCard label="Bearish Headlines" value={bear} color="text-rose-400"    sub={`${Math.round(bear/total*100)}% of ${total}`} />
        <StatCard label="Neutral Headlines" value={flat} color="text-amber-400"   sub={`${Math.round(flat/total*100)}% of ${total}`} />
      </div>

      {/* Gauge + Risk + Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Gauge */}
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5 space-y-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)]">Sentiment Breakdown</span>
          <div>
            <div className="flex justify-between text-[10px] text-[var(--c-muted)] mb-1.5">
              <span>Bearish -1</span><span>Neutral 0</span><span>Bullish +1</span>
            </div>
            <div className="relative h-3 rounded-full bg-[var(--c-border2)] overflow-hidden">
              <div className="absolute inset-0 flex">
                <div className="flex-1 bg-rose-500/20" />
                <div className="flex-1 bg-[var(--c-border2)]" />
                <div className="flex-1 bg-emerald-500/20" />
              </div>
              <div className="absolute top-0 h-full w-1 bg-white rounded-full shadow transition-all" style={{ left: `calc(${((score + 1) / 2) * 100}% - 2px)` }} />
            </div>
            <p className={`text-center mt-2 text-[13px] font-bold mono ${sentimentColor(score)}`}>{score > 0 ? '+' : ''}{score.toFixed(4)}</p>
          </div>
          <div className="space-y-2 pt-1">
            <SentimentBar label="Bullish" value={bull} total={total} color="bg-emerald-500" />
            <SentimentBar label="Bearish" value={bear} total={total} color="bg-rose-500" />
            <SentimentBar label="Neutral" value={flat} total={total} color="bg-amber-400" />
          </div>
        </div>

        {/* Risk */}
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)]">Risk Assessment</span>
          <div className="mt-4 space-y-3">
            {['Low', 'Medium', 'High'].map((lvl) => {
              const rl = (data.risk_level || data.risk_preference || 'medium').toLowerCase();
              const active = rl === lvl.toLowerCase();
              const colors = { Low: 'text-emerald-400 border-emerald-400/40 bg-emerald-500/5', Medium: 'text-amber-400 border-amber-400/40 bg-amber-500/5', High: 'text-rose-400 border-rose-400/40 bg-rose-500/5' };
              return (
                <div key={lvl} className={`flex items-center gap-3 px-3 py-2 rounded-lg border transition-all ${active ? colors[lvl] : 'border-[var(--c-border)] opacity-40'}`}>
                  <ShieldCheck className="w-4 h-4" />
                  <span className="text-[13px] font-semibold">{lvl} Risk</span>
                  {active && <span className="ml-auto text-[10px] font-bold uppercase tracking-wide">Active</span>}
                </div>
              );
            })}
          </div>
        </div>

        {/* Allocation */}
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)]">Portfolio Allocation</span>
          <div className="mt-4 space-y-3 text-[13px]">
            {[
              ['Suggested Amount', fmtCr(alloc.suggested_amount ?? alloc.amount ?? data.suggested_amount)],
              ['Position Size',    fmt(alloc.suggested_pct ?? alloc.pct ?? data.position_pct, '', '%', 1)],
              ['Max Position',     '20% of Capital'],
              ['Currency',         'INR'],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between border-b border-[var(--c-border)] pb-2 last:border-0 last:pb-0">
                <span className="text-[var(--c-muted)]">{k}</span>
                <span className="font-semibold text-[var(--c-text)] mono">{v}</span>
              </div>
            ))}
          </div>
          {data.orders && data.orders.length > 0 && (
            <div className="mt-4 space-y-2">
              {data.orders.map((ord, i) => (
                <div key={i} className="flex justify-between text-[11px] px-2.5 py-1.5 rounded bg-[var(--c-bg)] border border-[var(--c-border)]">
                  <span className={ord.action === 'BUY' ? 'text-emerald-400 font-bold' : ord.action === 'SELL' ? 'text-rose-400 font-bold' : 'text-amber-400 font-bold'}>{ord.action}</span>
                  <span className="font-mono text-[var(--c-text)]">{ord.units} units</span>
                  <span className="text-[var(--c-muted)]">{fmtCr(ord.value ?? ord.amount)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Metrics grid */}
      {Object.keys(metrics).length > 0 && (
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)] block mb-4">Key Financial Metrics</span>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              ['P/E Ratio',  fmt(metrics.pe_ratio, '', 'x', 1)],
              ['P/B Ratio',  fmt(metrics.pb_ratio, '', 'x', 2)],
              ['Market Cap', fmtCr(metrics.market_cap)],
              ['52W High',   fmt(metrics.week_52_high, '₹', '', 2)],
              ['52W Low',    fmt(metrics.week_52_low, '₹', '', 2)],
              ['Volume',     metrics.volume ? Number(metrics.volume).toLocaleString('en-IN') : '—'],
            ].map(([k, v]) => (
              <div key={k} className="flex flex-col gap-0.5">
                <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--c-dimmer)]">{k}</span>
                <span className="text-[15px] font-bold mono text-[var(--c-text)]">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* News table */}
      {news.length > 0 && (
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] overflow-hidden">
          <div className="px-5 py-3 border-b border-[var(--c-border)] flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)]">Recent Headlines ({news.length})</span>
            <span className="text-[11px] text-[var(--c-dimmer)]">Sentiment per article</span>
          </div>
          <table className="w-full">
            <tbody className="divide-y divide-[var(--c-border)]">
              {news.map((item, i) => {
                const sc = item.score ?? item.sentiment_score ?? 0;
                const lbl = sc > 0.05 ? 'Bullish' : sc < -0.05 ? 'Bearish' : 'Neutral';
                const cls = sc > 0.05 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : sc < -0.05 ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' : 'bg-amber-500/10 border-amber-500/30 text-amber-400';
                return (
                  <tr key={i}>
                    <td className="px-5 py-2.5 text-[12px] text-[var(--c-text)] leading-snug">
                      {item.url
                        ? <a href={item.url} target="_blank" rel="noreferrer" className="hover:text-indigo-400 transition-colors inline-flex items-start gap-1">
                            {item.title || item.headline || 'Untitled'}<ExternalLink className="w-2.5 h-2.5 mt-0.5 shrink-0 opacity-50" />
                          </a>
                        : (item.title || item.headline || 'Untitled')}
                      {item.source && <span className="ml-2 text-[10px] text-[var(--c-dimmer)]">{item.source}</span>}
                    </td>
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">
                      <span className={`inline-block px-2 py-0.5 rounded border text-[10px] font-semibold ${cls}`}>{lbl}</span>
                    </td>
                    <td className={`px-5 py-2.5 text-right text-[12px] font-mono font-bold whitespace-nowrap ${sentimentColor(sc)}`}>
                      {sc > 0 ? '+' : ''}{Number(sc).toFixed(3)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Ticker breakdown */}
      {data.ticker_sentiments && Object.keys(data.ticker_sentiments).length > 0 && (
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)] block mb-3">Ticker Breakdown</span>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {Object.entries(data.ticker_sentiments).map(([tk, info]) => {
              const sc = info?.score ?? 0;
              return (
                <div key={tk} className={`flex items-center justify-between p-2.5 rounded-lg border ${sentimentBg(sc)}`}>
                  <span className="text-[12px] font-semibold">{tk}</span>
                  <span className="mono text-[11px] font-bold">{sc > 0 ? '+' : ''}{sc.toFixed(2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Hidden Auto-Backtest Performance Summary — Module 5 */}
      <PerformanceSummary btResult={btResult} btLoading={btLoading} />
    </div>
  );
}

// ── Legacy Portfolio Overview (when no company selected but global data exists) ─

function LegacyDashboard({ data, onAnalyze, isAnalyzing, settingsChangedAt }) {
  const s = data.sentiment || {};
  const bull = s.positive ?? 0;
  const bear = s.negative ?? 0;
  const flat = s.neutral  ?? 0;
  const total = (s.total_headlines ?? (bull + bear + flat)) || 1;
  const score = s.score ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[17px] font-semibold text-[var(--c-text)]">Portfolio Overview</h2>
          <p className="text-[12px] text-[var(--c-dimmer)] mt-0.5">{(data.tickers || []).join(' · ')}</p>
        </div>
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className="flex items-center gap-1.5 h-8 px-3.5 rounded-lg text-[12px] font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
        >
          {isAnalyzing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          {isAnalyzing ? 'Analyzing…' : 'Re-run Analysis'}
        </button>
      </div>

      {settingsChangedAt && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-emerald-900/20 border border-emerald-500/20 text-emerald-400 text-[12px]">
          <Zap className="w-3.5 h-3.5" />
          Settings saved — search for a company above or press <strong className="mx-1">Re-run Analysis</strong>.
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Score"   value={`${score > 0 ? '+' : ''}${score.toFixed(3)}`} color={sentimentColor(score)} sub={s.label} />
        <StatCard label="Bullish" value={bull} color="text-emerald-400" sub={`${Math.round(bull/total*100)}%`} />
        <StatCard label="Bearish" value={bear} color="text-rose-400"    sub={`${Math.round(bear/total*100)}%`} />
        <StatCard label="Neutral" value={flat} color="text-amber-400"   sub={`${Math.round(flat/total*100)}%`} />
      </div>

      {data.ticker_sentiments && Object.keys(data.ticker_sentiments).length > 0 && (
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)] block mb-3">Ticker Sentiments</span>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {Object.entries(data.ticker_sentiments).map(([tk, info]) => {
              const sc = info?.score ?? 0;
              return (
                <div key={tk} className={`flex items-center justify-between p-2.5 rounded-lg border ${sentimentBg(sc)}`}>
                  <span className="text-[12px] font-semibold">{tk}</span>
                  <span className="mono text-[11px] font-bold">{sc > 0 ? '+' : ''}{sc.toFixed(2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {data.orders && data.orders.length > 0 && (
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--c-dimmer)] block mb-3">Order Signals</span>
          <div className="space-y-2">
            {data.orders.map((ord, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-[var(--c-bg)] border border-[var(--c-border)] text-[12px]">
                <span className={ord.action === 'BUY' ? 'font-bold text-emerald-400' : ord.action === 'SELL' ? 'font-bold text-rose-400' : 'font-bold text-amber-400'}>{ord.action}</span>
                <span className="font-mono text-[var(--c-text)]">{ord.ticker}</span>
                <span className="text-[var(--c-muted)]">{ord.units} units</span>
                <span className="font-mono text-[var(--c-text)]">{fmtCr(ord.value ?? ord.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function Dashboard({ dashboardData, setDashboardData, isAnalyzing, setIsAnalyzing, settingsChangedAt }) {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyData, setCompanyData]         = useState(null);
  const [companyLoading, setCompanyLoading]   = useState(false);
  const [companyError, setCompanyError]       = useState(null);
  const [progress, setProgress]               = useState('');
  const [globalError, setGlobalError]         = useState(null);
  // Module 5 — hidden backtest state
  const [btData, setBtData]       = useState(null);   // completed backtest result
  const [btLoading, setBtLoading] = useState(false);  // backtest still running
  const pollRef   = useRef(null);
  const btPollRef = useRef(null);

  const clearBtPoll = () => {
    if (btPollRef.current) { clearInterval(btPollRef.current); btPollRef.current = null; }
  };

  // Fire silent backtest for a ticker; never blocks UI
  const fireSilentBacktest = useCallback(async (ticker) => {
    clearBtPoll();
    setBtData(null);
    setBtLoading(true);
    try {
      await startBacktestForTicker(ticker);
    } catch {
      // If already running or server down, still poll quietly
    }
    btPollRef.current = setInterval(async () => {
      try {
        const st = await backtestStatus();
        const { status } = st.data;
        if (status === 'complete') {
          clearBtPoll();
          setBtLoading(false);
          try {
            const r = await backtestLatestResult();
            setBtData(r.data);
          } catch { setBtData(null); }
        } else if (status === 'error' || status === 'idle') {
          clearBtPoll();
          setBtLoading(false);
        }
      } catch {
        clearBtPoll();
        setBtLoading(false);
      }
    }, 3000);
  }, []);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await getDashboard();
      if (res.data?.status === 'ok') setDashboardData(res.data);
    } catch {}
  }, [setDashboardData]);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);
  useEffect(() => () => {
    if (pollRef.current)   clearInterval(pollRef.current);
    if (btPollRef.current) clearInterval(btPollRef.current);
  }, []);

  const handleCompanySelect = async (company) => {
    setSelectedCompany(company);
    setCompanyData(null);
    setCompanyError(null);
    setCompanyLoading(true);
    // Fire silent hidden backtest immediately (Module 5)
    fireSilentBacktest(company.ticker);
    try {
      const res = await analyzeTicker(company.ticker);
      setCompanyData(res.data);
    } catch (e) {
      setCompanyError(e.response?.data?.error || e.response?.data?.message || 'Analysis failed. Make sure the backend is running.');
    } finally {
      setCompanyLoading(false);
    }
  };

  const handleGlobalAnalyze = async () => {
    setIsAnalyzing(true);
    setGlobalError(null);
    setProgress('Starting pipeline…');
    if (pollRef.current) clearInterval(pollRef.current);
    try { await runAnalysis(); } catch (e) {
      setGlobalError(e.response?.data?.message || 'Could not reach API server');
      setIsAnalyzing(false); setProgress(''); return;
    }
    pollRef.current = setInterval(async () => {
      try {
        const st = await analyzeStatus();
        const { status, progress: prog, error: errMsg } = st.data;
        if (prog) setProgress(prog);
        if (status === 'complete') {
          clearInterval(pollRef.current); pollRef.current = null;
          await fetchDashboard();
          setIsAnalyzing(false); setProgress('');
        } else if (status === 'error') {
          clearInterval(pollRef.current); pollRef.current = null;
          setGlobalError(errMsg || 'Analysis failed');
          setIsAnalyzing(false); setProgress('');
        }
      } catch {
        clearInterval(pollRef.current); pollRef.current = null;
        setGlobalError('Lost connection to API server');
        setIsAnalyzing(false); setProgress('');
      }
    }, 2500);
  };

  const globalOk = dashboardData && dashboardData.status === 'ok' && dashboardData.sentiment;

  return (
    <div className="space-y-5">

      {/* Top bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-[20px] font-bold text-[var(--c-text)]">Dashboard</h1>
          <p className="text-[12px] text-[var(--c-dimmer)] mt-0.5">Indian NSE · 500 companies · FinBERT sentiment + AI recommendation</p>
        </div>
        <CompanySearch onSelect={handleCompanySelect} loading={companyLoading} />
      </div>

      {/* Global progress */}
      {isAnalyzing && (
        <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] flex items-center gap-3 px-5 py-4">
          <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
          <p className="text-[13px] text-[var(--c-muted)]">{progress || 'Running analysis pipeline…'}</p>
        </div>
      )}

      {/* Per-company analysis */}
      {selectedCompany && (
        <div className="space-y-4">
          {companyLoading && (
            <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] flex flex-col items-center gap-3 py-16">
              <Loader2 className="w-7 h-7 text-indigo-400 animate-spin" />
              <p className="text-[13px] text-[var(--c-muted)]">
                Analysing <strong className="text-[var(--c-sub)]">{selectedCompany.name || selectedCompany.ticker}</strong>…
              </p>
              <div className="flex gap-2 flex-wrap justify-center">
                {['FinBERT', 'News API', 'Gemini', 'NSE Price Data'].map((s) => (
                  <span key={s} className="text-[10px] px-2 py-1 rounded-full bg-[var(--c-border)] text-[var(--c-dimmer)] border border-[var(--c-border2)]">{s}</span>
                ))}
              </div>
            </div>
          )}
          {companyError && !companyLoading && (
            <div className="flex items-start gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/5 px-4 py-3">
              <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
              <div>
                <p className="text-[13px] font-medium text-rose-400">{companyError}</p>
                <button onClick={() => handleCompanySelect(selectedCompany)} className="mt-1.5 text-[12px] text-[var(--c-muted)] hover:text-[var(--c-sub)] underline underline-offset-2">Try again</button>
              </div>
            </div>
          )}
          {companyData && !companyLoading && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] text-[var(--c-dimmer)]">{new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST</span>
              </div>
              <AnalysisPanel company={selectedCompany} data={companyData} onRefresh={() => handleCompanySelect(selectedCompany)} btResult={btData} btLoading={btLoading} />
            </div>
          )}
        </div>
      )}

      {/* Divider between company view and portfolio overview */}
      {selectedCompany && globalOk && (
        <div className="flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-[var(--c-border)]" />
          <span className="text-[11px] text-[var(--c-dimmer)] uppercase tracking-wide">Portfolio Overview</span>
          <div className="flex-1 h-px bg-[var(--c-border)]" />
        </div>
      )}

      {globalError && (
        <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-lg border border-rose-500/20 bg-rose-500/5 text-rose-400 text-[12px]">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />{globalError}
        </div>
      )}

      {globalOk
        ? <LegacyDashboard data={dashboardData} onAnalyze={handleGlobalAnalyze} isAnalyzing={isAnalyzing} settingsChangedAt={settingsChangedAt} />
        : !selectedCompany && !isAnalyzing && (
          <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] flex flex-col items-center justify-center py-20 text-center">
            <Activity className="w-9 h-9 text-[var(--c-ghost)] mb-3" />
            <p className="text-[14px] font-medium text-[var(--c-muted)]">Search for a company to begin</p>
            <p className="text-[12px] text-[var(--c-dimmer)] mt-1.5 max-w-xs">
              Use the search bar above to analyse any NSE company — or run the portfolio analysis below.
            </p>
            <button
              onClick={handleGlobalAnalyze}
              disabled={isAnalyzing}
              className="mt-5 flex items-center gap-2 h-8 px-4 rounded-lg text-[12px] font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
            >
              <Zap className="w-3.5 h-3.5" />Run Portfolio Analysis
            </button>
          </div>
        )
      }

    </div>
  );
}

