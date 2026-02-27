import { useState, useEffect, useCallback, useRef } from 'react';
import {
  RefreshCw,
  Loader2,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Zap,
} from 'lucide-react';
import SentimentGauge from '../components/SentimentGauge';
import RiskLevel from '../components/RiskLevel';
import PortfolioChart from '../components/PortfolioChart';
import OrderCards from '../components/OrderCards';
import { getDashboard, runAnalysis, analyzeStatus } from '../services/api';

function StatCell({ label, value, sub, color }) {
  return (
    <div className="px-4 py-3">
      <span className="text-[10px] font-medium text-[#374151] uppercase tracking-wide block mb-1">
        {label}
      </span>
      <span className={`mono text-lg font-bold leading-none ${color || 'text-white'}`}>
        {value}
      </span>
      {sub && <span className="block text-[10px] text-[#4b5563] mt-1">{sub}</span>}
    </div>
  );
}

export default function Dashboard({ dashboardData, setDashboardData, isAnalyzing, setIsAnalyzing, settingsChangedAt }) {
  const [error, setError] = useState(null);
  const [ts, setTs] = useState(null);
  const [progress, setProgress] = useState('');
  const pollRef = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await getDashboard();
      if (res.data?.status === 'ok') {
        setDashboardData(res.data);
        setTs(new Date());
        setError(null);
      }
    } catch { /* no data yet */ }
  }, [setDashboardData]);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  // Clean up poll on unmount
  useEffect(() => () => stopPolling(), []);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setError(null);
    setProgress('Starting pipeline…');
    stopPolling();
    try {
      await runAnalysis();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not reach the API server');
      setIsAnalyzing(false);
      setProgress('');
      return;
    }
    // Poll status every 2.5s until complete or error
    pollRef.current = setInterval(async () => {
      try {
        const s = await analyzeStatus();
        const { status, progress: prog, error: errMsg } = s.data;
        if (prog) setProgress(prog);
        if (status === 'complete') {
          stopPolling();
          await fetchDashboard();
          setIsAnalyzing(false);
          setProgress('');
        } else if (status === 'error') {
          stopPolling();
          setError(errMsg || 'Analysis failed');
          setIsAnalyzing(false);
          setProgress('');
        }
      } catch {
        stopPolling();
        setError('Lost connection to API server');
        setIsAnalyzing(false);
        setProgress('');
      }
    }, 2500);
  };

  const d = dashboardData;
  const ok = d && d.status === 'ok' && d.sentiment;

  /* ── Loading ────────────────────────────────────── */
  if (isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 pt-32">
        <Loader2 className="w-7 h-7 text-[#2563eb] animate-spin" />
        <p className="text-[13px] text-[#4b5563]">{progress || 'Running sentiment pipeline…'}</p>
        <div className="flex gap-3 mt-2">
          {['FinBERT', 'Gemini', 'NewsAPI', 'Reddit'].map((s) => (
            <span key={s} className="text-[10px] px-2 py-1 rounded bg-[#0d1320] text-[#374151] border border-[#151d2e]">
              {s}
            </span>
          ))}
        </div>
      </div>
    );
  }

  /* ── Empty state ────────────────────────────────── */
  if (!ok) {
    return (
      <div className="space-y-5">
        <Header ts={ts} onAnalyze={handleAnalyze} disabled={isAnalyzing} />
        {error && <ErrorBanner msg={error} />}
        {settingsChangedAt && (
          <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-[#1f2d1a] border border-[#22c55e]/20 text-[#22c55e] text-[12px] font-medium">
            <Zap className="w-3.5 h-3.5 flex-shrink-0" />
            Settings saved — press <strong className="mx-1">Run Analysis</strong> to fetch data with your new tickers / portfolio.
          </div>
        )}
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <Zap className="w-8 h-8 text-[#1e293b] mb-3" />
          <p className="text-[14px] text-[#64748b] font-medium">No data yet</p>
          <p className="text-[12px] text-[#374151] mt-1 max-w-xs">
            Set your tickers in Settings, then hit Run Analysis.
          </p>
        </div>
      </div>
    );
  }

  /* ── Data ───────────────────────────────────────── */
  const s = d.sentiment;
  const bull = s.positive ?? 0;
  const bear = s.negative ?? 0;
  const flat = s.neutral ?? 0;
  const total = s.total_headlines ?? (bull + bear + flat);

  return (
    <div className="space-y-4">
      <Header
        ts={ts}
        tickers={d.tickers}
        onAnalyze={handleAnalyze}
        disabled={isAnalyzing}
      />

      {error && <ErrorBanner msg={error} />}

      {/* ── Stat strip ────────────────────────────── */}
      <div className="card grid grid-cols-2 sm:grid-cols-5 divide-x divide-[#151d2e]">
        <StatCell label="Headlines" value={total} />
        <StatCell label="Bullish" value={bull} color="c-bull" />
        <StatCell label="Bearish" value={bear} color="c-bear" />
        <StatCell label="Neutral" value={flat} color="c-flat" />
        <StatCell
          label="Score"
          value={`${s.score > 0 ? '+' : ''}${s.score.toFixed(3)}`}
          color={s.score > 0.05 ? 'c-bull' : s.score < -0.05 ? 'c-bear' : 'c-flat'}
        />
      </div>

      {/* ── Main grid ─────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <SentimentGauge score={s.score} label={s.label} />
        <RiskLevel level={d.risk_preference || 'medium'} />
        <PortfolioChart portfolio={d.allocation} />
      </div>

      {/* ── Orders ────────────────────────────────── */}
      <OrderCards orders={d.orders || []} />

      {/* ── Ticker grid ───────────────────────────── */}
      {d.ticker_sentiments && Object.keys(d.ticker_sentiments).length > 0 && (
        <div className="card p-5">
          <span className="text-[11px] font-medium text-[#4b5563] uppercase tracking-wide">
            Ticker Breakdown
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 mt-3">
            {Object.entries(d.ticker_sentiments).map(([tk, info]) => {
              const sc = info?.score ?? 0;
              const c = sc > 0.05 ? '#22c55e' : sc < -0.05 ? '#ef4444' : '#4b5563';
              return (
                <div key={tk} className="flex items-center justify-between p-2.5 rounded-md bg-[#080c14] border border-[#151d2e]">
                  <span className="text-[13px] font-semibold text-white">{tk}</span>
                  <span className="mono text-[12px] font-semibold" style={{ color: c }}>
                    {sc > 0 ? '+' : ''}{sc.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ────────────────────────────────── */

function Header({ ts, tickers, onAnalyze, disabled }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-[18px] font-semibold text-white leading-tight">Dashboard</h1>
        <p className="text-[12px] text-[#374151] mt-0.5">
          {tickers?.length
            ? tickers.join(' · ')
            : 'Sentiment Trading Agent'}
          {ts && (
            <span className="ml-2 text-[#1e293b]">|</span>
          )}
          {ts && (
            <span className="ml-2">{ts.toLocaleTimeString()}</span>
          )}
        </p>
      </div>
      <button
        onClick={onAnalyze}
        disabled={disabled}
        className="flex items-center gap-1.5 h-8 px-3.5 rounded-md text-[12px] font-semibold
          bg-[#2563eb] text-white hover:bg-[#1d4ed8] disabled:opacity-40
          transition-colors"
      >
        {disabled
          ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
          : <RefreshCw className="w-3.5 h-3.5" />}
        {disabled ? 'Analyzing' : 'Run Analysis'}
      </button>
    </div>
  );
}

function ErrorBanner({ msg }) {
  return (
    <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-md bg-[#ef4444]/8 border border-[#ef4444]/15 text-[#f87171] text-[12px]">
      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
      {msg}
    </div>
  );
}
