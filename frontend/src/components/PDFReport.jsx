/**
 * PDFReport — Module 8
 *
 * Generates a downloadable PDF report for a selected NSE company.
 * Uses html2canvas + jsPDF (client-side, no server required).
 *
 * Contents:
 *  1. Company header (name, ticker, exchange, sector, generated date)
 *  2. Recommendation + confidence badge
 *  3. Sentiment score + breakdown (bull/bear/neutral)
 *  4. AI summary / explanation
 *  5. Risk level + allocation
 *  6. Key financial metrics
 *  7. 3-year backtest performance (if available)
 *  8. Top recent headlines (up to 8)
 *  9. Disclaimer footer
 *
 * Export: <DownloadReportButton company={} data={} btResult={} />
 */

import { useRef, useState } from 'react';
import { FileDown, Loader2 } from 'lucide-react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

// ── Helpers ───────────────────────────────────────────────────
function pp(v)   { return typeof v === 'number' ? `${v >= 0 ? '+' : ''}${(v * 100).toFixed(2)}%` : '—'; }
function pct(v)  { return typeof v === 'number' ? `${(v * 100).toFixed(2)}%` : '—'; }
function fmtN(v, d = 2) {
  if (v === null || v === undefined) return '—';
  const n = parseFloat(v);
  return isNaN(n) ? String(v) : n.toFixed(d);
}
function fmtINR(v) {
  if (!v) return '—';
  const n = parseFloat(v);
  if (isNaN(n)) return v;
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toFixed(0)}`;
}

function sentColor(score) {
  if (score > 0.15)  return '#34d399';
  if (score > 0.05)  return '#4ade80';
  if (score < -0.15) return '#f87171';
  if (score < -0.05) return '#fb923c';
  return '#fbbf24';
}
function recColors(rec) {
  const r = (rec || '').toLowerCase();
  if (r.includes('strong buy'))  return { bg: '#059669', text: '#fff' };
  if (r.includes('buy'))         return { bg: '#16a34a', text: '#fff' };
  if (r.includes('strong sell')) return { bg: '#dc2626', text: '#fff' };
  if (r.includes('sell'))        return { bg: '#ea580c', text: '#fff' };
  return { bg: '#d97706', text: '#fff' };
}
function recLabel(rec) {
  const r = (rec || '').toLowerCase();
  if (r.includes('strong buy'))  return 'STRONG BUY';
  if (r.includes('buy'))         return 'BUY';
  if (r.includes('strong sell')) return 'STRONG SELL';
  if (r.includes('sell'))        return 'SELL';
  return 'HOLD';
}

// ── Report template (rendered off-screen, captured by html2canvas) ────────────
function ReportTemplate({ company, data, btResult, reportRef }) {
  const s         = data.sentiment || {};
  const score     = s.score ?? data.score ?? 0;
  const bull      = s.positive ?? data.bullish ?? 0;
  const bear      = s.negative ?? data.bearish ?? 0;
  const flat      = s.neutral  ?? data.neutral  ?? 0;
  const total     = (s.total_headlines ?? (bull + bear + flat)) || 1;
  const rec       = data.recommendation || data.signal || 'Hold';
  const recC      = recColors(rec);
  const recLbl    = recLabel(rec);
  const confidence = data.confidence ?? data.confidence_pct ?? null;
  const explanation = data.explanation || data.ai_explanation || data.summary || null;
  const alloc     = data.allocation || {};
  const metrics   = data.metrics || data.financial_metrics || {};
  const news      = (data.news || data.headlines || data.articles || []).slice(0, 8);
  const bm        = btResult?.summary || null;
  const riskLevel = (data.risk_level || data.risk_preference || 'Medium');
  const now       = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'long', timeStyle: 'short' });

  const scoreColor = sentColor(score);

  return (
    <div
      ref={reportRef}
      style={{
        position: 'fixed',
        left: '-9999px',
        top: 0,
        width: '794px',           // A4 at 96 dpi
        background: '#ffffff',
        fontFamily: "'Segoe UI', Arial, sans-serif",
        fontSize: '13px',
        color: '#1e293b',
        lineHeight: '1.5',
        padding: '0',
      }}
    >
      {/* ── PAGE HEADER ── */}
      <div style={{ background: '#0f172a', padding: '32px 40px 24px', position: 'relative' }}>
        {/* Branding stripe */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: 'linear-gradient(90deg,#2563eb,#6366f1,#8b5cf6)' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em', color: '#64748b', textTransform: 'uppercase', marginBottom: '6px' }}>
              SentXStock — NSE Sentiment Research
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.5px' }}>
              {data.name || company.name}
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ background: '#1e3a8a', border: '1px solid #3b82f6', color: '#93c5fd', fontSize: '11px', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', fontFamily: 'monospace' }}>
                {data.ticker || company.ticker}
              </span>
              <span style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', fontSize: '11px', padding: '2px 8px', borderRadius: '4px' }}>
                {data.exchange || 'NSE'}
              </span>
              <span style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', fontSize: '11px', padding: '2px 8px', borderRadius: '4px' }}>
                {data.sector || company.sector || '—'}
              </span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ ...recC, padding: '8px 20px', borderRadius: '8px', fontSize: '16px', fontWeight: 900, letterSpacing: '0.05em', marginBottom: '8px' }}>
              {recLbl}
            </div>
            {confidence !== null && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#f1f5f9', fontFamily: 'monospace' }}>
                  {Number(confidence).toFixed(1)}%
                </div>
                <div style={{ fontSize: '9px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Confidence</div>
              </div>
            )}
          </div>
        </div>

        <div style={{ marginTop: '16px', fontSize: '10px', color: '#475569' }}>
          Generated: {now} IST
        </div>
      </div>

      {/* ── BODY ── */}
      <div style={{ padding: '32px 40px', background: '#f8fafc' }}>

        {/* ── SENTIMENT SCORE STRIP ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          {[
            { label: 'Sentiment Score', value: `${score > 0 ? '+' : ''}${score.toFixed(4)}`, color: scoreColor },
            { label: 'Bullish Headlines', value: bull, color: '#34d399' },
            { label: 'Bearish Headlines', value: bear, color: '#f87171' },
            { label: 'Neutral Headlines', value: flat, color: '#fbbf24' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px 14px' }}>
              <div style={{ fontSize: '9px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#94a3b8', marginBottom: '4px' }}>{label}</div>
              <div style={{ fontSize: '20px', fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</div>
            </div>
          ))}
        </div>

        {/* ── SENTIMENT BAR ── */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
          <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#94a3b8', marginBottom: '10px' }}>Sentiment Breakdown</div>
          {[
            { label: 'Bullish', count: bull, color: '#22c55e' },
            { label: 'Bearish', count: bear, color: '#ef4444' },
            { label: 'Neutral', count: flat, color: '#f59e0b' },
          ].map(({ label, count, color }) => {
            const w = Math.round((count / total) * 100);
            return (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', fontSize: '12px' }}>
                <span style={{ width: '56px', color: '#64748b' }}>{label}</span>
                <div style={{ flex: 1, height: '8px', background: '#f1f5f9', borderRadius: '99px', overflow: 'hidden' }}>
                  <div style={{ width: `${w}%`, height: '100%', background: color, borderRadius: '99px' }} />
                </div>
                <span style={{ width: '32px', textAlign: 'right', fontWeight: 700, color, fontFamily: 'monospace' }}>{w}%</span>
                <span style={{ width: '28px', textAlign: 'right', color: '#94a3b8' }}>{count}</span>
              </div>
            );
          })}
        </div>

        {/* ── AI EXPLANATION ── */}
        {explanation && (
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#3b82f6', marginBottom: '8px' }}>AI Analysis Summary</div>
            <div style={{ color: '#334155', lineHeight: '1.6', fontSize: '12px' }}>{explanation}</div>
          </div>
        )}

        {/* ── RISK + ALLOCATION + METRICS row ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>

          {/* Risk + Allocation */}
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#94a3b8', marginBottom: '10px' }}>Risk &amp; Allocation</div>
            {[
              ['Risk Level',      riskLevel],
              ['Suggested Amount', fmtINR(alloc.suggested_amount ?? alloc.amount ?? data.suggested_amount)],
              ['Position Size',   alloc.suggested_pct != null ? `${(alloc.suggested_pct * 100).toFixed(1)}%` : '—'],
              ['Max Position',    '20% of Capital'],
              ['Currency',        'INR (₹)'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #f1f5f9', fontSize: '12px' }}>
                <span style={{ color: '#64748b' }}>{k}</span>
                <span style={{ fontWeight: 700, fontFamily: 'monospace', color: '#1e293b' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Financial Metrics */}
          {Object.keys(metrics).length > 0 && (
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
              <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#94a3b8', marginBottom: '10px' }}>Key Financial Metrics</div>
              {[
                ['P/E Ratio',  metrics.pe_ratio  != null ? `${parseFloat(metrics.pe_ratio).toFixed(1)}x` : '—'],
                ['P/B Ratio',  metrics.pb_ratio  != null ? `${parseFloat(metrics.pb_ratio).toFixed(2)}x` : '—'],
                ['Market Cap', fmtINR(metrics.market_cap)],
                ['52W High',   metrics.week_52_high != null ? `₹${parseFloat(metrics.week_52_high).toFixed(2)}` : '—'],
                ['52W Low',    metrics.week_52_low  != null ? `₹${parseFloat(metrics.week_52_low).toFixed(2)}`  : '—'],
                ['Volume',     metrics.volume ? Number(metrics.volume).toLocaleString('en-IN') : '—'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: '1px solid #f1f5f9', fontSize: '12px' }}>
                  <span style={{ color: '#64748b' }}>{k}</span>
                  <span style={{ fontWeight: 700, fontFamily: 'monospace', color: '#1e293b' }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── 3-YEAR BACKTEST PERFORMANCE ── */}
        {bm && (
          <div style={{ background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
            <div style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#6366f1', marginBottom: '10px' }}>
              3-Year Backtest Performance · Jan 2023 – Jan 2026 · NSE · Nifty 50 Benchmark
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '12px' }}>
              {[
                { label: 'Strategy Return', value: pp(bm.cum_return),  color: (bm.cum_return ?? 0) >= 0 ? '#059669' : '#dc2626' },
                { label: 'Annual Return',   value: pp(bm.ann_return),  color: (bm.ann_return  ?? 0) >= 0 ? '#059669' : '#dc2626' },
                { label: 'Sharpe Ratio',    value: fmtN(bm.sharpe_ratio, 3), color: (bm.sharpe_ratio ?? 0) >= 1 ? '#059669' : (bm.sharpe_ratio ?? 0) >= 0 ? '#d97706' : '#dc2626' },
                { label: 'Max Drawdown',    value: pct(bm.max_drawdown), color: '#dc2626' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: '#fff', border: '1px solid #e0e7ff', borderRadius: '6px', padding: '10px', textAlign: 'center' }}>
                  <div style={{ fontSize: '18px', fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</div>
                  <div style={{ fontSize: '9px', color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.07em', marginTop: '3px' }}>{label}</div>
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
              {[
                ['Win Rate',            pct(bm.win_rate)],
                ['Ann. Volatility',     pct(bm.ann_volatility  ?? bm.ann_vol)],
                ['Sortino Ratio',       fmtN(bm.sortino_ratio, 3)],
                ['Calmar Ratio',        fmtN(bm.calmar_ratio,  3)],
              ].map(([k, v]) => (
                <div key={k} style={{ fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <span style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{k}</span>
                  <span style={{ fontWeight: 700, fontFamily: 'monospace', color: '#1e293b' }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── RECENT HEADLINES ── */}
        {news.length > 0 && (
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px' }}>
            <div style={{ background: '#f8fafc', padding: '10px 16px', borderBottom: '1px solid #e2e8f0', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: '#94a3b8' }}>
              Recent Headlines ({news.length})
            </div>
            {news.map((item, i) => {
              const sc  = item.score ?? item.sentiment_score ?? 0;
              const lbl = sc > 0.05 ? 'Bullish' : sc < -0.05 ? 'Bearish' : 'Neutral';
              const col = sc > 0.05 ? '#059669' : sc < -0.05 ? '#dc2626' : '#d97706';
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', padding: '9px 16px', borderBottom: i < news.length - 1 ? '1px solid #f1f5f9' : 'none', gap: '12px' }}>
                  <div style={{ flex: 1, fontSize: '11px', color: '#334155', lineHeight: '1.4' }}>
                    {item.title || item.headline || 'Untitled'}
                    {item.source && <span style={{ marginLeft: '6px', fontSize: '9px', color: '#94a3b8' }}>{item.source}</span>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                    <span style={{ fontSize: '9px', fontWeight: 700, color: col, border: `1px solid ${col}40`, background: `${col}12`, borderRadius: '4px', padding: '1px 6px' }}>{lbl}</span>
                    <span style={{ fontSize: '10px', fontWeight: 800, fontFamily: 'monospace', color: col }}>{sc > 0 ? '+' : ''}{Number(sc).toFixed(3)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── FOOTER / DISCLAIMER ── */}
        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '16px', fontSize: '10px', color: '#94a3b8', lineHeight: '1.6' }}>
          <div style={{ fontWeight: 700, color: '#64748b', marginBottom: '4px' }}>Disclaimer</div>
          <p>
            This report is generated by <strong>SentXStock</strong> and is intended for educational and research purposes only.
            It does not constitute financial advice, investment recommendations, or an offer to buy or sell securities.
            Sentiment scores are derived from automated analysis of publicly available news and social media content.
            Past backtest performance does not guarantee future results.
            Always consult a SEBI-registered investment advisor before making investment decisions.
          </p>
          <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
            <span>SentXStock © {new Date().getFullYear()} · NSE Market Sentiment Platform</span>
            <span>Report generated: {now} IST</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Download button + generation logic ───────────────────────────────────────
export function DownloadReportButton({ company, data, btResult }) {
  const reportRef = useRef(null);
  const [generating, setGenerating] = useState(false);

  const handleDownload = async () => {
    if (!data || generating) return;
    setGenerating(true);
    try {
      // brief tick to let the hidden DOM render
      await new Promise(r => setTimeout(r, 80));

      const el = reportRef.current;
      if (!el) throw new Error('Report element not found');

      // A4 dimensions in mm: 210 x 297
      const A4_W_MM = 210;
      const A4_H_MM = 297;
      const PX_PER_MM = 3.7795; // at 96 dpi approx

      const canvas = await html2canvas(el, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
        width: 794,
      });

      const imgData = canvas.toDataURL('image/png');
      const imgW    = A4_W_MM;
      const imgH    = (canvas.height / canvas.width) * imgW;

      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      let yPos  = 0;
      let remaining = imgH;

      while (remaining > 0) {
        const sliceH = Math.min(remaining, A4_H_MM);
        const srcY   = yPos * (canvas.height / imgH);
        const srcH   = sliceH * (canvas.height / imgH);

        // Create a slice canvas
        const slice = document.createElement('canvas');
        slice.width  = canvas.width;
        slice.height = srcH;
        const ctx = slice.getContext('2d');
        ctx.drawImage(canvas, 0, srcY, canvas.width, srcH, 0, 0, canvas.width, srcH);

        if (yPos > 0) pdf.addPage();
        pdf.addImage(slice.toDataURL('image/png'), 'PNG', 0, 0, imgW, sliceH);

        yPos      += A4_H_MM;
        remaining -= A4_H_MM;
      }

      const ticker = (data.ticker || company.ticker || 'report').replace('.NS', '');
      const date   = new Date().toISOString().slice(0, 10);
      pdf.save(`SentXStock_${ticker}_${date}.pdf`);
    } catch (err) {
      console.error('[PDFReport] generation failed:', err);
      alert('PDF generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <>
      {/* Hidden report template — rendered off-screen */}
      {data && <ReportTemplate company={company} data={data} btResult={btResult} reportRef={reportRef} />}

      {/* Visible download button */}
      <button
        onClick={handleDownload}
        disabled={!data || generating}
        title="Download PDF Report"
        className={`flex items-center gap-1.5 h-8 px-3 rounded-lg text-[11px] font-semibold border transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
          generating
            ? 'border-indigo-500/40 bg-indigo-500/10 text-indigo-400 cursor-wait'
            : 'border-[var(--c-border2)] bg-[var(--c-surface2)] text-[var(--c-sub)] hover:border-indigo-500/40 hover:bg-indigo-500/10 hover:text-indigo-400'
        }`}
      >
        {generating
          ? <><Loader2 className="w-3 h-3 animate-spin" /> Generating…</>
          : <><FileDown className="w-3 h-3" /> PDF Report</>}
      </button>
    </>
  );
}
