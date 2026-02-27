import { useState, useEffect, useCallback } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  RefreshCw, TrendingUp, TrendingDown, Minus,
  AlertTriangle, IndianRupee, ShieldCheck,
  BarChart2, Layers, Info, Clock, Eye,
} from 'lucide-react';
import { getPortfolioAllocations, analyzePortfolioTickers, getSettings, setPortfolio } from '../services/api';

// ─── Constants ────────────────────────────────────────────────────────────────

const RISK_LABELS = { low: 'Conservative', medium: 'Moderate', high: 'Aggressive' };
const RISK_MULT   = { low: 0.5, medium: 1.0, high: 1.5 };

const RISK_COLORS = {
  low:    { text: 'text-blue-400',   border: 'border-blue-500/30',   bg: 'bg-blue-500/10'   },
  medium: { text: 'text-amber-400',  border: 'border-amber-500/30',  bg: 'bg-amber-500/10'  },
  high:   { text: 'text-rose-400',   border: 'border-rose-500/30',   bg: 'bg-rose-500/10'   },
};

const PIE_COLORS = [
  '#2563eb', '#7c3aed', '#0891b2', '#059669',
  '#d97706', '#dc2626', '#db2777', '#65a30d',
  '#0284c7', '#9333ea',
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (n) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n ?? 0);

const fmtPct = (n) => `${(n ?? 0).toFixed(2)}%`;

function recColor(rec = '') {
  const r = rec.toUpperCase();
  if (r.startsWith('BUY'))  return { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' };
  if (r.startsWith('SELL')) return { text: 'text-rose-400',    bg: 'bg-rose-500/10',    border: 'border-rose-500/30'    };
  return { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' };
}

function SentimentIcon({ sentiment = '' }) {
  const s = sentiment.toLowerCase();
  if (s.includes('bull')) return <TrendingUp  className="w-3.5 h-3.5 text-emerald-400" />;
  if (s.includes('bear')) return <TrendingDown className="w-3.5 h-3.5 text-rose-400"    />;
  return <Minus className="w-3.5 h-3.5 text-amber-400" />;
}

function ConfidenceBar({ value }) {
  const pct = Math.round((value ?? 0.5) * 100);
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[var(--c-border)] rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] text-[var(--c-muted)] w-8 text-right">{pct}%</span>
    </div>
  );
}

// ─── Custom Pie Tooltip ───────────────────────────────────────────────────────

function PieTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="bg-[var(--c-surface2)] border border-[var(--c-border2)] rounded-lg px-3 py-2 shadow-xl text-[12px]">
      <p className="font-semibold text-[var(--c-text)] mb-0.5">{d.name}</p>
      <p style={{ color: d.payload.fill }}>{fmtPct(d.value)}</p>
      <p className="text-[var(--c-muted)]">{fmt(d.payload.amount)}</p>
    </div>
  );
}

// ─── Allocation Card ──────────────────────────────────────────────────────────

function AllocationCard({ item, index }) {
  const rc = recColor(item.recommendation);
  const recLabel = (item.recommendation || 'HOLD').split('—')[0].trim().split(' ')[0];
  return (
    <div className="bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl p-4 flex flex-col gap-3 hover:border-[var(--c-border2)] transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-[11px]"
            style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
          >
            {item.ticker.slice(0, 2)}
          </div>
          <div>
            <p className="text-[13px] font-semibold text-[var(--c-text)] leading-tight">{item.ticker}</p>
            {item.name && (
              <p className="text-[10px] text-[var(--c-dim)] leading-tight">{item.name}</p>
            )}
            <div className="flex items-center gap-1 mt-0.5">
              <SentimentIcon sentiment={item.sentiment} />
              <span className="text-[11px] text-[var(--c-muted)]">{item.sentiment || 'Neutral'}</span>
              {item.is_mock && (
                <span className="ml-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-400">Simulated</span>
              )}
            </div>
          </div>
        </div>
        <span
          className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${rc.text} ${rc.bg} ${rc.border}`}
        >
          {recLabel}
        </span>
      </div>

      {/* Confidence */}
      <div>
        <p className="text-[10px] text-[var(--c-dim)] mb-1 uppercase tracking-widest">Confidence</p>
        <ConfidenceBar value={item.confidence} />
      </div>

      {/* Allocation */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-[var(--c-surface2)] rounded-lg p-2.5">
          <p className="text-[10px] text-[var(--c-dim)] uppercase tracking-widest mb-0.5">Allocation</p>
          <p className="text-[13px] font-semibold text-[var(--c-text)]">{fmtPct(item.allocation_pct)}</p>
        </div>
        <div className="bg-[var(--c-surface2)] rounded-lg p-2.5">
          <p className="text-[10px] text-[var(--c-dim)] uppercase tracking-widest mb-0.5">Amount (INR)</p>
          <p className="text-[13px] font-semibold text-[var(--c-text)]">{fmt(item.allocation_inr)}</p>
        </div>
      </div>

      {/* Capped warning */}
      {item.capped && (
        <div className="flex items-center gap-1.5 text-[11px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-md px-2 py-1.5">
          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
          <span>Position capped at 20% limit</span>
        </div>
      )}

      {/* Analyzed at timestamp */}
      {item.analyzed_at && (
        <p className="text-[10px] text-[var(--c-dim)]">Analyzed: {item.analyzed_at}</p>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Portfolio() {
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [saving, setSaving]     = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Editable capital/risk for inline adjustment
  const [editCapital, setEditCapital] = useState('');
  const [editRisk, setEditRisk]       = useState('medium');
  const [showEdit, setShowEdit]       = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getPortfolioAllocations();
      setData(r.data);
      setEditCapital(String(r.data.capital ?? 50000));
      setEditRisk(r.data.risk ?? 'medium');
    } catch (e) {
      setError('Failed to load portfolio data. Is the server running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    const cap = parseFloat(editCapital);
    if (!cap || cap < 1000) return;
    setSaving(true);
    try {
      await setPortfolio(cap, editRisk);
      setShowEdit(false);
      await load();
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  const handleAnalyzeAll = async () => {
    setAnalyzing(true);
    try {
      await analyzePortfolioTickers();
      await load();
    } catch {
      // ignore
    } finally {
      setAnalyzing(false);
    }
  };

  // ── Derived ────────────────────────────────────────────────────────────────

  // Use recently viewed 6 companies; fall back to full list only if none viewed yet
  const recentAllocs  = data?.recent_allocations ?? [];
  const allAllocs     = data?.allocations ?? [];
  const allocs        = recentAllocs.length > 0 ? recentAllocs : allAllocs;
  const recentCount   = data?.recently_viewed?.length ?? 0;
  const isShowingRecent = recentAllocs.length > 0;

  // Allocated total for display — use only shown allocs
  const shownTotal = allocs.reduce((s, a) => s + a.allocation_inr, 0);

  const pieData = allocs.map((a, i) => ({
    name:   a.ticker,
    value:  a.allocation_pct,
    amount: a.allocation_inr,
    fill:   PIE_COLORS[i % PIE_COLORS.length],
  }));

  const freeCashPct = data
    ? Math.max(0, (((data.capital - shownTotal) / data.capital) * 100))
    : 0;
  const freeCash = data ? Math.max(0, data.capital - shownTotal) : 0;

  if (freeCashPct > 0) {
    pieData.push({ name: 'Cash', value: freeCashPct, amount: freeCash, fill: '#374151' });
  }

  const riskStyle = RISK_COLORS[data?.risk ?? 'medium'] ?? RISK_COLORS.medium;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">

      {/* Page header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-[20px] font-bold text-[var(--c-text)]">Portfolio Engine</h1>
          <p className="text-[13px] text-[var(--c-muted)] mt-0.5">
            {isShowingRecent
              ? `Allocation plan for your ${recentCount} recently analysed compan${recentCount !== 1 ? 'ies' : 'y'}`
              : 'INR-denominated allocation plan based on sentiment confidence and risk profile'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowEdit(v => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--c-border2)]
              text-[12px] text-[var(--c-sub)] hover:text-[var(--c-text)] hover:border-[var(--c-border2)]
              bg-[var(--c-surface)] transition-colors"
          >
            <IndianRupee className="w-3.5 h-3.5" />
            Adjust Capital
          </button>
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--c-border2)]
              text-[12px] text-[var(--c-sub)] hover:text-[var(--c-text)] bg-[var(--c-surface)] transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Inline capital editor */}
      {showEdit && (
        <div className="bg-[var(--c-surface)] border border-[var(--c-border2)] rounded-xl p-4 flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-[11px] text-[var(--c-dim)] mb-1 uppercase tracking-widest">
              Capital (INR)
            </label>
            <div className="relative">
              <IndianRupee className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--c-muted)]" />
              <input
                type="number"
                value={editCapital}
                onChange={e => setEditCapital(e.target.value)}
                className="pl-7 pr-3 py-1.5 bg-[var(--c-surface2)] border border-[var(--c-border)]
                  rounded-lg text-[13px] text-[var(--c-text)] w-40 focus:outline-none
                  focus:border-[var(--c-border2)]"
              />
            </div>
          </div>
          <div>
            <label className="block text-[11px] text-[var(--c-dim)] mb-1 uppercase tracking-widest">
              Risk Profile
            </label>
            <select
              value={editRisk}
              onChange={e => setEditRisk(e.target.value)}
              className="px-3 py-1.5 bg-[var(--c-surface2)] border border-[var(--c-border)] rounded-lg
                text-[13px] text-[var(--c-text)] focus:outline-none focus:border-[var(--c-border2)]"
            >
              <option value="low">Conservative (0.5×)</option>
              <option value="medium">Moderate (1.0×)</option>
              <option value="high">Aggressive (1.5×)</option>
            </select>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-1.5 bg-[#2563eb] hover:bg-[#1d4ed8] text-white text-[13px] font-medium
              rounded-lg transition-colors disabled:opacity-40"
          >
            {saving ? 'Saving…' : 'Apply'}
          </button>
          <button
            onClick={() => setShowEdit(false)}
            className="px-3 py-1.5 border border-[var(--c-border)] rounded-lg text-[13px]
              text-[var(--c-muted)] hover:text-[var(--c-text)] bg-[var(--c-surface)] transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-rose-400 text-[13px]">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {loading && !data && (
        <div className="flex items-center justify-center h-40 text-[var(--c-muted)] text-[13px]">
          <RefreshCw className="w-4 h-4 animate-spin mr-2" />
          Loading portfolio…
        </div>
      )}

      {data && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SummaryCard
              icon={<IndianRupee className="w-4 h-4" />}
              label="Total Capital"
              value={fmt(data.capital)}
              accent="blue"
            />
            <SummaryCard
              icon={<Layers className="w-4 h-4" />}
              label={isShowingRecent ? 'Allocated (Recent)' : 'Allocated'}
              value={fmt(shownTotal)}
              sub={fmtPct(data.capital ? (shownTotal / data.capital) * 100 : 0)}
              accent="indigo"
            />
            <SummaryCard
              icon={<BarChart2 className="w-4 h-4" />}
              label="Available Cash"
              value={fmt(freeCash)}
              sub={fmtPct(freeCashPct)}
              accent="emerald"
            />
            <SummaryCard
              icon={<ShieldCheck className="w-4 h-4" />}
              label="Risk Profile"
              value={RISK_LABELS[data.risk] ?? 'Moderate'}
              sub={`${RISK_MULT[data.risk] ?? 1.0}× multiplier`}
              accent={data.risk === 'low' ? 'blue' : data.risk === 'high' ? 'rose' : 'amber'}
            />
          </div>

          {/* Risk banner */}
          <div className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${riskStyle.border} ${riskStyle.bg}`}>
            <ShieldCheck className={`w-4 h-4 flex-shrink-0 ${riskStyle.text}`} />
            <div className="flex-1 min-w-0">
              <p className={`text-[13px] font-semibold ${riskStyle.text}`}>
                {RISK_LABELS[data.risk ?? 'medium']} Strategy — {RISK_MULT[data.risk ?? 'medium']}× multiplier
              </p>
              <p className="text-[11px] text-[var(--c-muted)] mt-0.5">
                Formula: confidence × {RISK_MULT[data.risk ?? 'medium']} × (1 / {data.n_positions} positions) · max 20% per position
              </p>
            </div>
            {!data.has_analysis && (
              <div className="flex items-center gap-1.5 text-[11px] text-[var(--c-dim)]">
                <Info className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">No analysis yet — using 50% default confidence</span>
              </div>
            )}
          </div>

          {/* Timestamp */}
          {data.timestamp && (
            <p className="text-[11px] text-[var(--c-dim)]">
              Last analysis: {data.timestamp}
            </p>
          )}

          {/* Chart + table layout */}
          {allocs.length > 0 ? (
            <>
              {/* Recently viewed banner */}
              {isShowingRecent && (
                <div className="flex items-center gap-2.5 rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-4 py-2.5">
                  <Eye className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <p className="text-[12px] text-indigo-300/90">
                    Showing portfolio for your <span className="font-semibold">{recentCount} recently analysed</span> compan{recentCount !== 1 ? 'ies' : 'y'}.
                    Analyse more companies on the Dashboard to update this view.
                  </p>
                </div>
              )}
              {!isShowingRecent && (
                <div className="flex items-center gap-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-2.5">
                  <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <p className="text-[12px] text-amber-300/90">
                    No companies analysed yet. Go to the <span className="font-semibold">Dashboard</span>, search and click any company to analyse it — the portfolio will update automatically.
                  </p>
                </div>
              )}

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">

              {/* Allocation cards grid */}
              <div>
                <h2 className="text-[14px] font-semibold text-[var(--c-text)] mb-3">
                  {isShowingRecent ? 'Recently Analysed' : 'Position Breakdown'}
                  <span className="ml-2 text-[11px] text-[var(--c-muted)] font-normal">
                    {allocs.length} position{allocs.length !== 1 ? 's' : ''}
                  </span>
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
                  {allocs.map((item, i) => (
                    <AllocationCard key={item.ticker} item={item} index={i} />
                  ))}
                </div>
              </div>

              {/* Pie chart + table */}
              <div className="space-y-4">
                <h2 className="text-[14px] font-semibold text-[var(--c-text)]">Allocation Split</h2>

                {/* Pie */}
                <div className="bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl p-4">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {pieData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} stroke="transparent" />
                        ))}
                      </Pie>
                      <Tooltip content={<PieTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>

                  {/* Legend */}
                  <div className="mt-3 space-y-1.5">
                    {pieData.map((d, i) => (
                      <div key={i} className="flex items-center justify-between text-[12px]">
                        <div className="flex items-center gap-2">
                          <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: d.fill }} />
                          <span className="text-[var(--c-sub)]">{d.name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[var(--c-muted)]">{fmtPct(d.value)}</span>
                          <span className="text-[var(--c-text)] font-medium">{fmt(d.amount)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Allocation table */}
                <div className="bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl overflow-hidden">
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr className="border-b border-[var(--c-border)] bg-[var(--c-surface2)]">
                        <th className="text-left px-3 py-2 text-[var(--c-dim)] font-medium">Ticker</th>
                        <th className="text-right px-3 py-2 text-[var(--c-dim)] font-medium">Pct</th>
                        <th className="text-right px-3 py-2 text-[var(--c-dim)] font-medium">INR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allocs.map((a, i) => {
                        const rc = recColor(a.recommendation);
                        return (
                          <tr key={a.ticker} className="border-b border-[var(--c-border)] last:border-0 hover:bg-[var(--c-surface2)] transition-colors">
                            <td className="px-3 py-2">
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                                <span className="font-medium text-[var(--c-text)]">{a.ticker}</span>
                                {a.capped && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                              </div>
                            </td>
                            <td className={`px-3 py-2 text-right font-semibold ${rc.text}`}>
                              {fmtPct(a.allocation_pct)}
                            </td>
                            <td className="px-3 py-2 text-right text-[var(--c-text)]">
                              {fmt(a.allocation_inr)}
                            </td>
                          </tr>
                        );
                      })}
                      {/* Cash row */}
                      {freeCashPct > 0 && (
                        <tr className="bg-[var(--c-surface2)]">
                          <td className="px-3 py-2">
                            <div className="flex items-center gap-2">
                              <div className="w-2 h-2 rounded-full bg-[#374151]" />
                              <span className="text-[var(--c-dim)]">Cash</span>
                            </div>
                          </td>
                          <td className="px-3 py-2 text-right text-[var(--c-muted)]">{fmtPct(freeCashPct)}</td>
                          <td className="px-3 py-2 text-right text-[var(--c-muted)]">{fmt(freeCash)}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-40 text-center gap-3">
              <BarChart2 className="w-8 h-8 text-[var(--c-border2)]" />
              <div>
                <p className="text-[13px] text-[var(--c-sub)]">No tickers in your watchlist</p>
                <p className="text-[12px] text-[var(--c-muted)] mt-0.5">Add tickers in Settings to generate a portfolio plan</p>
              </div>
            </div>
          )}

          {/* SEBI disclaimer */}
          <div className="bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl p-4">
            <p className="text-[11px] text-[var(--c-dim)] leading-relaxed">
              <span className="font-semibold text-[var(--c-muted)]">Disclaimer:</span>{' '}
              Allocations shown are generated by a sentiment-based AI model. AI can make mistakes, please go through the real data currently.
              All amounts are in Indian Rupees (INR).
            </p>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Summary Card ─────────────────────────────────────────────────────────────

const ACCENT = {
  blue:   'text-blue-400   bg-blue-500/10  ',
  indigo: 'text-indigo-400 bg-indigo-500/10',
  emerald:'text-emerald-400 bg-emerald-500/10',
  amber:  'text-amber-400  bg-amber-500/10 ',
  rose:   'text-rose-400   bg-rose-500/10  ',
};

function SummaryCard({ icon, label, value, sub, accent = 'blue' }) {
  const col = ACCENT[accent] ?? ACCENT.blue;
  const [textColor, bgColor] = col.split(' ');
  return (
    <div className="bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl p-4 hover:border-[var(--c-border2)] transition-colors">
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center mb-3 ${bgColor} ${textColor}`}>
        {icon}
      </div>
      <p className="text-[10px] text-[var(--c-dim)] uppercase tracking-widest mb-0.5">{label}</p>
      <p className="text-[16px] font-bold text-[var(--c-text)] leading-tight">{value}</p>
      {sub && <p className="text-[11px] text-[var(--c-muted)] mt-0.5">{sub}</p>}
    </div>
  );
}
