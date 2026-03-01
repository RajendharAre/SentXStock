/**
 * Admin Panel — /admin
 * Full dataset management: upload → train → view results.
 * Protected: redirects to /admin/login if no valid token.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck, Upload, Trash2, Play, RefreshCw, LogOut,
  FileText, Database, BarChart2, ChevronDown, ChevronUp,
  CheckCircle, XCircle, Clock, AlertCircle, TrendingUp,
  TrendingDown, Minus, Eye, X, FileSpreadsheet, FileJson,
} from 'lucide-react';
import {
  adminVerify, adminLogout,
  fetchDatasets, uploadDataset, deleteDataset,
  startTraining, fetchTrainStatus,
  fetchResults, fetchResult,
} from '../services/adminApi';

// ── Helpers ─────────────────────────────────────────────────────────────────

function Badge({ children, color = 'indigo' }) {
  const map = {
    indigo:  'border-indigo-500/30 bg-indigo-600/10 text-indigo-400',
    emerald: 'border-emerald-500/30 bg-emerald-600/10 text-emerald-400',
    red:     'border-red-500/30 bg-red-600/10 text-red-400',
    amber:   'border-amber-500/30 bg-amber-600/10 text-amber-400',
    slate:   'border-[var(--c-border)] bg-[var(--c-surface2)] text-[var(--c-muted)]',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full border text-[10px] font-semibold ${map[color]}`}>
      {children}
    </span>
  );
}

function SignalBadge({ signal }) {
  if (signal === 'BUY')  return <Badge color="emerald">📈 BUY</Badge>;
  if (signal === 'SELL') return <Badge color="red">📉 SELL</Badge>;
  return <Badge color="amber">➡ HOLD</Badge>;
}

function ExtIcon({ ext }) {
  if (ext === '.json') return <FileJson className="w-4 h-4 text-amber-400" />;
  if (ext === '.sql')  return <Database className="w-4 h-4 text-indigo-400" />;
  return <FileSpreadsheet className="w-4 h-4 text-emerald-400" />;
}

function SectionHeading({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="w-9 h-9 rounded-lg bg-[var(--c-surface2)] border border-[var(--c-border)] flex items-center justify-center">
        <Icon className="w-4 h-4 text-indigo-400" />
      </div>
      <div>
        <p className="text-[15px] font-bold text-[var(--c-text)]">{title}</p>
        {subtitle && <p className="text-[11px] text-[var(--c-muted)]">{subtitle}</p>}
      </div>
    </div>
  );
}

// ── Upload Form ──────────────────────────────────────────────────────────────

function UploadForm({ onUploaded }) {
  const [company,     setCompany]     = useState('');
  const [periodFrom,  setPeriodFrom]  = useState('');
  const [periodTo,    setPeriodTo]    = useState('');
  const [description, setDescription] = useState('');
  const [file,        setFile]        = useState(null);
  const [dragOver,    setDragOver]    = useState(false);
  const [uploading,   setUploading]   = useState(false);
  const [error,       setError]       = useState('');
  const inputRef = useRef();

  const ACCEPTED = '.csv,.xlsx,.xls,.json,.sql';

  const handleFile = (f) => {
    if (!f) return;
    const ext = f.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls', 'json', 'sql'].includes(ext)) {
      setError('Unsupported file type. Allowed: CSV, XLSX, XLS, JSON, SQL');
      return;
    }
    setFile(f);
    setError('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) { setError('Please select a file'); return; }
    if (!company.trim()) { setError('Company name is required'); return; }

    setUploading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file',        file);
      fd.append('company',     company.trim());
      fd.append('period_from', periodFrom);
      fd.append('period_to',   periodTo);
      fd.append('description', description);
      const meta = await uploadDataset(fd);
      setCompany(''); setPeriodFrom(''); setPeriodTo('');
      setDescription(''); setFile(null);
      onUploaded(meta);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2.5">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-400">{error}</p>
        </div>
      )}

      {/* File drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`relative rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
          dragOver
            ? 'border-indigo-500 bg-indigo-600/5'
            : file
            ? 'border-emerald-500/50 bg-emerald-600/5'
            : 'border-[var(--c-border)] hover:border-indigo-500/50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <CheckCircle className="w-6 h-6 text-emerald-400" />
            <div className="text-left">
              <p className="text-[13px] font-semibold text-emerald-400">{file.name}</p>
              <p className="text-[11px] text-[var(--c-muted)]">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="ml-2 text-[var(--c-dimmer)] hover:text-red-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="w-8 h-8 text-[var(--c-dimmer)] mx-auto mb-2" />
            <p className="text-[13px] font-medium text-[var(--c-sub)]">
              Drop your dataset here or <span className="text-indigo-400">browse</span>
            </p>
            <p className="text-[11px] text-[var(--c-dimmer)] mt-1">CSV · XLSX · XLS · JSON · SQL</p>
          </>
        )}
      </div>

      {/* Metadata fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2 space-y-1">
          <label className="text-[12px] font-medium text-[var(--c-sub)]">Company Name *</label>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="e.g. Zepto, Reliance Industries, HDFC Bank"
            required
            className="w-full h-9 px-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="space-y-1">
          <label className="text-[12px] font-medium text-[var(--c-sub)]">Period From</label>
          <input
            type="date"
            value={periodFrom}
            onChange={(e) => setPeriodFrom(e.target.value)}
            className="w-full h-9 px-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="space-y-1">
          <label className="text-[12px] font-medium text-[var(--c-sub)]">Period To</label>
          <input
            type="date"
            value={periodTo}
            onChange={(e) => setPeriodTo(e.target.value)}
            className="w-full h-9 px-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="sm:col-span-2 space-y-1">
          <label className="text-[12px] font-medium text-[var(--c-sub)]">
            Description <span className="text-[var(--c-dimmer)]">(optional)</span>
          </label>
          <textarea
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of this dataset…"
            className="w-full px-3 py-2 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors resize-none"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={uploading || !file}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {uploading
          ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Uploading…</>
          : <><Upload className="w-4 h-4" /> Upload Dataset</>
        }
      </button>
    </form>
  );
}

// ── Dataset Row ──────────────────────────────────────────────────────────────

function DatasetRow({ meta, trainingId, onTrain, onDelete, onViewResult }) {
  const [deleting, setDeleting] = useState(false);
  const isTraining = trainingId === meta.id;

  const handleDelete = async () => {
    if (!window.confirm(`Delete dataset "${meta.company} (${meta.filename})"?`)) return;
    setDeleting(true);
    await onDelete(meta.id);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] hover:border-[var(--c-border2)] transition-colors">
      {/* Icon + info */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-[var(--c-surface2)] border border-[var(--c-border)] flex items-center justify-center shrink-0">
          <ExtIcon ext={meta.ext} />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-[var(--c-text)] truncate">{meta.company}</p>
          <p className="text-[11px] text-[var(--c-muted)] truncate">{meta.filename}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-[11px] text-[var(--c-muted)]">
        <span>{meta.rows?.toLocaleString()} rows</span>
        <span>{meta.col_count} cols</span>
        {meta.period_from && (
          <span>{meta.period_from} → {meta.period_to || '…'}</span>
        )}
        <Badge color={meta.trained ? 'emerald' : 'slate'}>
          {meta.trained ? '✓ Trained' : 'Not trained'}
        </Badge>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {meta.trained && (
          <button
            onClick={() => onViewResult(meta.id)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-indigo-500/30 text-indigo-400 text-[12px] font-medium hover:bg-indigo-600/10 transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            Results
          </button>
        )}
        <button
          onClick={() => onTrain(meta.id)}
          disabled={isTraining}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-emerald-500/30 text-emerald-400 text-[12px] font-medium hover:bg-emerald-600/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isTraining
            ? <><span className="w-3 h-3 border-2 border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin" /> Training…</>
            : <><Play className="w-3.5 h-3.5" /> {meta.trained ? 'Re-train' : 'Train'}</>
          }
        </button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-red-500/20 text-red-400 text-[12px] font-medium hover:bg-red-600/10 transition-colors disabled:opacity-40"
        >
          {deleting
            ? <span className="w-3 h-3 border-2 border-red-400/30 border-t-red-400 rounded-full animate-spin" />
            : <Trash2 className="w-3.5 h-3.5" />
          }
        </button>
      </div>
    </div>
  );
}

// ── Result Modal ─────────────────────────────────────────────────────────────

function ResultModal({ datasetId, onClose }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');

  useEffect(() => {
    fetchResult(datasetId)
      .then(setResult)
      .catch(() => setResult(null))
      .finally(() => setLoading(false));
  }, [datasetId]);

  if (loading) return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
    </div>
  );

  if (!result) return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="rounded-2xl border border-[var(--c-border)] bg-[var(--c-surface)] p-8 text-center max-w-sm w-full">
        <p className="text-[var(--c-muted)]">No result found for this dataset.</p>
        <button onClick={onClose} className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm">Close</button>
      </div>
    </div>
  );

  const TABS = ['overview', 'sentiment', 'prices'];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-3xl mt-8 mb-8 rounded-2xl border border-[var(--c-border)] bg-[var(--c-bg)] flex flex-col">

        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--c-border)]">
          <div>
            <p className="text-[15px] font-bold text-[var(--c-text)]">{result.company}</p>
            <p className="text-[11px] text-[var(--c-muted)]">Trained: {result.trained_at} · {result.total_rows} rows</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-[var(--c-surface)] flex items-center justify-center text-[var(--c-muted)] hover:text-[var(--c-text)] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-[12px] font-medium capitalize transition-colors ${
                tab === t
                  ? 'bg-indigo-600/10 border border-indigo-500/30 text-indigo-400'
                  : 'text-[var(--c-muted)] hover:text-[var(--c-sub)]'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="p-6 space-y-5">

          {/* ── Overview ── */}
          {tab === 'overview' && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Signal',     value: <SignalBadge signal={result.signal} /> },
                  { label: 'Confidence', value: `${result.confidence}%` },
                  { label: 'Score',      value: (result.composite_score >= 0 ? '+' : '') + result.composite_score },
                  { label: 'Rows',       value: result.total_rows?.toLocaleString() },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-4 text-center">
                    <p className="text-[11px] text-[var(--c-muted)] uppercase tracking-wide mb-1">{label}</p>
                    <div className="text-[16px] font-bold text-[var(--c-text)]">{value}</div>
                  </div>
                ))}
              </div>

              {/* Sentiment summary per column */}
              {Object.keys(result.sentiment_summary || {}).length > 0 && (
                <div className="space-y-2">
                  <p className="text-[12px] font-semibold text-[var(--c-sub)] uppercase tracking-wide">Sentiment by Column</p>
                  {Object.entries(result.sentiment_summary).map(([col, s]) => {
                    const total = s.analyzed || 1;
                    const bullPct = Math.round((s.bullish / total) * 100);
                    const bearPct = Math.round((s.bearish / total) * 100);
                    const neutPct = 100 - bullPct - bearPct;
                    return (
                      <div key={col} className="rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-[12px] font-medium text-[var(--c-text)]">{col}</p>
                          <span className={`text-[12px] font-bold ${s.avg_score > 0.05 ? 'text-emerald-400' : s.avg_score < -0.05 ? 'text-red-400' : 'text-[var(--c-muted)]'}`}>
                            score {s.avg_score > 0 ? '+' : ''}{s.avg_score}
                          </span>
                        </div>
                        <div className="flex rounded-full overflow-hidden h-2 gap-px">
                          <div style={{ width: `${bullPct}%` }} className="bg-emerald-500" />
                          <div style={{ width: `${neutPct}%` }} className="bg-[var(--c-border)]" />
                          <div style={{ width: `${bearPct}%` }} className="bg-red-500" />
                        </div>
                        <div className="flex gap-4 text-[11px] text-[var(--c-muted)]">
                          <span className="text-emerald-400">{s.bullish} bullish</span>
                          <span>{s.neutral} neutral</span>
                          <span className="text-red-400">{s.bearish} bearish</span>
                          <span className="ml-auto">{s.analyzed} analysed</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {result.errors?.length > 0 && (
                <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                  <p className="text-[11px] font-semibold text-amber-400 mb-1">Warnings</p>
                  {result.errors.map((e, i) => (
                    <p key={i} className="text-[11px] text-amber-300/70">• {e}</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Sentiment rows ── */}
          {tab === 'sentiment' && (
            <div className="space-y-3">
              {(result.sentiment_rows || []).length === 0 ? (
                <p className="text-[var(--c-muted)] text-sm text-center py-8">No text columns found in this dataset.</p>
              ) : (
                <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                  {result.sentiment_rows.map((row) => (
                    <div key={row.row} className="flex items-start gap-3 rounded-lg p-3 border border-[var(--c-border)] bg-[var(--c-surface)]">
                      <span className="text-[10px] font-mono text-[var(--c-dimmer)] mt-0.5 w-6 shrink-0">#{row.row}</span>
                      <p className="flex-1 text-[12px] text-[var(--c-text)] leading-relaxed">{row.text}</p>
                      <div className="shrink-0 text-right space-y-1">
                        <Badge color={row.label === 'Positive' ? 'emerald' : row.label === 'Negative' ? 'red' : 'slate'}>
                          {row.label}
                        </Badge>
                        <p className={`text-[11px] font-mono ${row.score > 0 ? 'text-emerald-400' : row.score < 0 ? 'text-red-400' : 'text-[var(--c-muted)]'}`}>
                          {row.score > 0 ? '+' : ''}{row.score}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Price analysis ── */}
          {tab === 'prices' && (
            <div className="space-y-3">
              {(result.price_analyses || []).length === 0 ? (
                <p className="text-[var(--c-muted)] text-sm text-center py-8">No numeric price columns found in this dataset.</p>
              ) : result.price_analyses.map((p) => (
                <div key={p.column} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-4">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-[13px] font-semibold text-[var(--c-text)]">{p.column}</p>
                    <div className="flex items-center gap-1">
                      {p.trend === 'Uptrend'
                        ? <TrendingUp className="w-4 h-4 text-emerald-400" />
                        : <TrendingDown className="w-4 h-4 text-red-400" />}
                      <span className={`text-[12px] font-semibold ${p.trend === 'Uptrend' ? 'text-emerald-400' : 'text-red-400'}`}>
                        {p.trend}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                    {[
                      ['First',    p.first],
                      ['Last',     p.last],
                      ['Min',      p.min],
                      ['Max',      p.max],
                      ['Return',   `${p.total_return_pct > 0 ? '+' : ''}${p.total_return_pct}%`],
                      ['Volatility', `${p.volatility_pct}%`],
                    ].map(([k, v]) => (
                      <div key={k} className="text-center">
                        <p className="text-[10px] text-[var(--c-muted)] uppercase">{k}</p>
                        <p className="text-[13px] font-bold text-[var(--c-text)]">{v}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Training Status Bar ──────────────────────────────────────────────────────

function TrainStatusBar({ status, onDismiss }) {
  if (!status || status.status === 'idle') return null;

  const isRunning  = status.status === 'running';
  const isComplete = status.status === 'complete';
  const isError    = status.status === 'error';

  return (
    <div className={`flex items-center gap-3 rounded-xl border p-4 text-sm ${
      isRunning  ? 'border-indigo-500/30 bg-indigo-600/5'  :
      isComplete ? 'border-emerald-500/30 bg-emerald-600/5' :
                   'border-red-500/30 bg-red-600/5'
    }`}>
      {isRunning  && <span className="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin shrink-0" />}
      {isComplete && <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />}
      {isError    && <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
      <p className={`flex-1 ${isRunning ? 'text-indigo-400' : isComplete ? 'text-emerald-400' : 'text-red-400'}`}>
        {isRunning  ? status.progress :
         isComplete ? 'Training complete! Click "Results" to view the analysis.' :
                      `Error: ${status.error}`}
      </p>
      {!isRunning && (
        <button onClick={onDismiss} className="text-[var(--c-dimmer)] hover:text-[var(--c-text)]">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function AdminPanel() {
  const navigate = useNavigate();
  const [datasets,      setDatasets]      = useState([]);
  const [trainStatus,   setTrainStatus]   = useState(null);
  const [trainingId,    setTrainingId]    = useState(null);   // which dataset is being trained
  const [viewResultId,  setViewResultId]  = useState(null);
  const [loadingDs,     setLoadingDs]     = useState(true);
  const [error,         setError]         = useState('');
  const pollRef = useRef(null);

  // ── Auth guard + initial load (sequenced — verify first, then fetch) ───────
  const loadDatasets = useCallback(async () => {
    console.log('[AdminPanel] loadDatasets called');
    try {
      const data = await fetchDatasets();
      console.log('[AdminPanel] setDatasets with', data.length, 'items');
      setDatasets(data);
    } catch (e) {
      console.error('[AdminPanel] loadDatasets error:', e);
      setError('Failed to load datasets: ' + e.message);
    } finally {
      setLoadingDs(false);
    }
  }, []);

  useEffect(() => {
    console.log('[AdminPanel] mount — calling adminVerify()');
    adminVerify().then((ok) => {
      console.log('[AdminPanel] adminVerify result:', ok);
      if (!ok) {
        console.warn('[AdminPanel] not authenticated — redirecting to /admin/login');
        navigate('/admin/login');
      } else {
        console.log('[AdminPanel] authenticated — loading datasets');
        loadDatasets();
      }
    });
  }, [navigate, loadDatasets]);

  // ── Poll training status ──────────────────────────────────────────────────
  const startPoll = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(async () => {
      try {
        const s = await fetchTrainStatus();
        setTrainStatus(s);
        if (s.status !== 'running') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setTrainingId(null);
          loadDatasets();   // refresh to show "Trained" badge
        }
      } catch { /* ignore */ }
    }, 1500);
  }, [loadDatasets]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleUploaded = (meta) => {
    setDatasets((prev) => [meta, ...prev]);
  };

  const handleDelete = async (id) => {
    await deleteDataset(id);
    setDatasets((prev) => prev.filter((d) => d.id !== id));
  };

  const handleTrain = async (id) => {
    setTrainingId(id);
    setTrainStatus({ status: 'running', progress: 'Starting…', error: null });
    try {
      await startTraining(id);
      startPoll();
    } catch (err) {
      setTrainStatus({ status: 'error', error: err.message });
      setTrainingId(null);
    }
  };

  const handleLogout = () => {
    adminLogout();
    navigate('/admin/login');
  };

  return (
    <div className="min-h-screen bg-[var(--c-bg)]">

      {/* ── Top bar ── */}
      <header className="sticky top-0 z-30 border-b border-[var(--c-border)] bg-[var(--c-bg)]/90 backdrop-blur-sm">
        <div className="max-w-[1200px] mx-auto px-5 sm:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <span className="text-[15px] font-bold text-[var(--c-text)]">Admin Panel</span>
            <Badge color="indigo">SentXStock</Badge>
          </div>
          <div className="flex items-center gap-3">
            <a href="/" className="text-[12px] text-[var(--c-muted)] hover:text-indigo-400 transition-colors">
              ← Public Site
            </a>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--c-border)] text-[12px] text-[var(--c-muted)] hover:text-red-400 hover:border-red-500/30 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-5 sm:px-8 py-8 space-y-10">

        {/* ── DEBUG strip — remove after fix ── */}
        <div className="rounded-lg border border-yellow-500/40 bg-yellow-500/5 p-3 text-[11px] font-mono text-yellow-300 space-y-1">
          <p>🔍 DEBUG — loadingDs: <b>{String(loadingDs)}</b> | datasets.length: <b>{datasets.length}</b> | error: <b>{error || 'none'}</b></p>
          {datasets.length > 0 && <p>First dataset: {datasets[0].company} | {datasets[0].rows?.toLocaleString()} rows | id: {datasets[0].id}</p>}
        </div>

        {/* Error global */}
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Training status bar */}
        <TrainStatusBar
          status={trainStatus}
          onDismiss={() => setTrainStatus(null)}
        />

        {/* ── Stats row ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Datasets', value: datasets.length, icon: Database,    color: 'text-indigo-400' },
            { label: 'Trained',        value: datasets.filter(d => d.trained).length, icon: CheckCircle, color: 'text-emerald-400' },
            { label: 'Pending',        value: datasets.filter(d => !d.trained).length, icon: Clock,      color: 'text-amber-400' },
            { label: 'Total Rows',     value: datasets.reduce((s, d) => s + (d.rows || 0), 0).toLocaleString(), icon: BarChart2, color: 'text-[var(--c-sub)]' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${color}`} />
                <p className="text-[11px] text-[var(--c-muted)] uppercase tracking-wide">{label}</p>
              </div>
              <p className="text-2xl font-extrabold text-[var(--c-text)]">{value}</p>
            </div>
          ))}
        </div>

        {/* ── Upload section ── */}
        <section className="rounded-2xl border border-[var(--c-border)] bg-[var(--c-surface)] p-6">
          <SectionHeading icon={Upload} title="Upload Dataset" subtitle="CSV · XLSX · XLS · JSON · SQL — any company, any period" />
          <UploadForm onUploaded={handleUploaded} />
        </section>

        {/* ── Datasets table ── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <SectionHeading icon={Database} title="Datasets" subtitle={`${datasets.length} uploaded`} />
            <button
              onClick={loadDatasets}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--c-border)] text-[12px] text-[var(--c-muted)] hover:text-indigo-400 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          {loadingDs ? (
            <div className="flex items-center justify-center py-16">
              <span className="w-6 h-6 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
            </div>
          ) : datasets.length === 0 ? (
            <div className="text-center py-16 border border-dashed border-[var(--c-border)] rounded-xl">
              <Database className="w-10 h-10 text-[var(--c-dimmer)] mx-auto mb-3" />
              <p className="text-[var(--c-muted)] text-sm">No datasets uploaded yet.</p>
              <p className="text-[var(--c-dimmer)] text-[12px] mt-1">Use the form above to upload your first dataset.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {datasets.map((meta) => (
                <DatasetRow
                  key={meta.id}
                  meta={meta}
                  trainingId={trainingId}
                  onTrain={handleTrain}
                  onDelete={handleDelete}
                  onViewResult={setViewResultId}
                />
              ))}
            </div>
          )}
        </section>

      </main>

      {/* Result Modal */}
      {viewResultId && (
        <ResultModal
          datasetId={viewResultId}
          onClose={() => setViewResultId(null)}
        />
      )}
    </div>
  );
}
