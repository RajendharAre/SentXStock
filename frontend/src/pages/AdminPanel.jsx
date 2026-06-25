/**
 * Admin Panel — /admin
 * Dataset management: upload → train → view results.
 * Auth-guarded: redirects to /admin/login if token missing/expired.
 * Supports light/dark theme via ThemeContext.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck, Upload, Trash2, Play, RefreshCw, LogOut,
  Database, BarChart2, CheckCircle, XCircle, Clock,
  AlertCircle, TrendingUp, TrendingDown, Eye, X,
  FileSpreadsheet, FileJson, Sun, Moon,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import {
  adminVerify, adminLogout,
  fetchDatasets, uploadDataset, deleteDataset,
  startTraining, fetchTrainStatus,
  fetchResult,
} from '../services/adminApi';

/* ─── helpers ──────────────────────────────────────────────── */

const cx = (...c) => c.filter(Boolean).join(' ');

function Spinner({ size = 4 }) {
  const s = `w-${size} h-${size}`;
  return (
    <span className={cx(s, 'inline-block border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin')} />
  );
}

function Pill({ label, color = 'slate' }) {
  const map = {
    indigo:  'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    red:     'bg-red-500/10 text-red-400 border-red-500/30',
    amber:   'bg-amber-500/10 text-amber-400 border-amber-500/30',
    slate:   'bg-[var(--c-ghost)] text-[var(--c-muted)] border-[var(--c-border)]',
  };
  return (
    <span className={cx('inline-block px-2 py-0.5 rounded-full border text-[10px] font-semibold', map[color])}>
      {label}
    </span>
  );
}

function ExtIcon({ ext }) {
  if (ext === '.json') return <FileJson className="w-4 h-4 text-amber-400" />;
  if (ext === '.sql')  return <Database className="w-4 h-4 text-indigo-400" />;
  return <FileSpreadsheet className="w-4 h-4 text-emerald-400" />;
}

/* ─── UploadForm ────────────────────────────────────────────── */

function UploadForm({ onUploaded }) {
  const [company, setCompany] = useState('');
  const [from,    setFrom]    = useState('');
  const [to,      setTo]      = useState('');
  const [desc,    setDesc]    = useState('');
  const [file,    setFile]    = useState(null);
  const [drag,    setDrag]    = useState(false);
  const [busy,    setBusy]    = useState(false);
  const [err,     setErr]     = useState('');
  const ref = useRef();

  const pickFile = (f) => {
    if (!f) return;
    const ext = f.name.split('.').pop().toLowerCase();
    if (!['csv','xlsx','xls','json','sql'].includes(ext)) {
      setErr('Unsupported file — use CSV, XLSX, XLS, JSON or SQL'); return;
    }
    setFile(f); setErr('');
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!file)           { setErr('Choose a file first'); return; }
    if (!company.trim()) { setErr('Company name is required'); return; }
    setBusy(true); setErr('');
    try {
      const fd = new FormData();
      fd.append('file',        file);
      fd.append('company',     company.trim());
      fd.append('period_from', from);
      fd.append('period_to',   to);
      fd.append('description', desc);
      const meta = await uploadDataset(fd);
      setCompany(''); setFrom(''); setTo(''); setDesc(''); setFile(null);
      onUploaded(meta);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  const inputCls = 'w-full h-9 px-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors';

  return (
    <form onSubmit={submit} className="space-y-4">
      {err && (
        <div className="flex gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <p className="text-xs text-red-400">{err}</p>
        </div>
      )}

      {/* drop zone */}
      <div
        onClick={() => ref.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); pickFile(e.dataTransfer.files[0]); }}
        className={cx(
          'rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
          drag  ? 'border-indigo-500 bg-indigo-500/5' :
          file  ? 'border-emerald-500/40 bg-emerald-500/5' :
                  'border-[var(--c-border)] hover:border-[var(--c-border2)]'
        )}
      >
        <input ref={ref} type="file" accept=".csv,.xlsx,.xls,.json,.sql" className="hidden"
          onChange={(e) => pickFile(e.target.files[0])} />
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <div className="text-left">
              <p className="text-sm font-semibold text-emerald-400">{file.name}</p>
              <p className="text-xs text-[var(--c-muted)]">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <button type="button" onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="ml-2 text-[var(--c-dim)] hover:text-red-400 transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="w-7 h-7 text-[var(--c-dimmer)] mx-auto mb-2" />
            <p className="text-sm text-[var(--c-muted)]">Drop file here or <span className="text-indigo-400">browse</span></p>
            <p className="text-xs text-[var(--c-dim)] mt-1">CSV · XLSX · XLS · JSON · SQL</p>
          </>
        )}
      </div>

      {/* fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2 space-y-1">
          <label className="text-xs font-medium text-[var(--c-muted)]">Company Name *</label>
          <input type="text" value={company} onChange={e => setCompany(e.target.value)}
            placeholder="e.g. NASDAQ 100, Reliance, HDFC Bank" required className={inputCls} />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-[var(--c-muted)]">Period From</label>
          <input type="date" value={from} onChange={e => setFrom(e.target.value)} className={inputCls} />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-[var(--c-muted)]">Period To</label>
          <input type="date" value={to} onChange={e => setTo(e.target.value)} className={inputCls} />
        </div>
        <div className="sm:col-span-2 space-y-1">
          <label className="text-xs font-medium text-[var(--c-muted)]">Description (optional)</label>
          <textarea rows={2} value={desc} onChange={e => setDesc(e.target.value)}
            placeholder="Short note about this dataset…"
            className="w-full px-3 py-2 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors resize-none" />
        </div>
      </div>

      <button type="submit" disabled={busy || !file}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
        {busy ? <><Spinner /> Uploading…</> : <><Upload className="w-4 h-4" /> Upload Dataset</>}
      </button>
    </form>
  );
}

/* ─── DatasetCard ───────────────────────────────────────────── */

function DatasetCard({ ds, trainingId, onTrain, onDelete, onResult }) {
  const [deleting, setDeleting] = useState(false);
  const isTraining = trainingId === ds.id;

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${ds.company}" dataset? This cannot be undone.`)) return;
    setDeleting(true);
    try { await onDelete(ds.id); } catch { setDeleting(false); }
  };

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] hover:bg-[var(--c-surface2)] px-4 py-3 transition-colors">
      {/* icon + info */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-[var(--c-ghost)] border border-[var(--c-border)] flex items-center justify-center shrink-0">
          <ExtIcon ext={ds.ext} />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-[var(--c-text)] truncate">{ds.company}</p>
          <p className="text-[11px] text-[var(--c-muted)] truncate">{ds.filename}</p>
        </div>
      </div>

      {/* meta */}
      <div className="flex flex-wrap items-center gap-3 text-[11px] text-[var(--c-sub)]">
        <span>{ds.rows?.toLocaleString()} rows · {ds.col_count} cols</span>
        {ds.period_from && <span>{ds.period_from} – {ds.period_to || '…'}</span>}
        <Pill label={ds.trained ? '✓ Trained' : 'Untrained'} color={ds.trained ? 'emerald' : 'slate'} />
      </div>

      {/* actions */}
      <div className="flex items-center gap-2 shrink-0">
        {ds.trained && (
          <button onClick={() => onResult(ds.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-indigo-500/30 text-indigo-400 text-xs font-medium hover:bg-indigo-500/10 transition-colors">
            <Eye className="w-3.5 h-3.5" /> Results
          </button>
        )}
        <button onClick={() => onTrain(ds.id)} disabled={isTraining}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-500/30 text-emerald-400 text-xs font-medium hover:bg-emerald-500/10 transition-colors disabled:opacity-40">
          {isTraining
            ? <><Spinner size={3} /> Training…</>
            : <><Play className="w-3.5 h-3.5" /> {ds.trained ? 'Re-train' : 'Train'}</>}
        </button>
        <button onClick={handleDelete} disabled={deleting}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-500/20 text-red-400 text-xs font-medium hover:bg-red-500/10 transition-colors disabled:opacity-40">
          {deleting ? <Spinner size={3} /> : <Trash2 className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
}

/* ─── TrainingBanner ────────────────────────────────────────── */

function TrainingBanner({ status, onDismiss }) {
  if (!status || status.status === 'idle') return null;
  const running  = status.status === 'running';
  const complete = status.status === 'complete';
  return (
    <div className={cx('flex items-center gap-3 rounded-xl border p-3',
      running  ? 'border-indigo-500/30 bg-indigo-500/5' :
      complete ? 'border-emerald-500/30 bg-emerald-500/5' :
                 'border-red-500/30 bg-red-500/5')}>
      {running  && <Spinner size={4} />}
      {complete && <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />}
      {!running && !complete && <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
      <p className={cx('flex-1 text-xs',
        running ? 'text-indigo-300' : complete ? 'text-emerald-300' : 'text-red-300')}>
        {running  ? (status.progress || 'Training in progress…') :
         complete ? 'Training complete! Click Results to view.' :
                   `Error: ${status.error}`}
      </p>
      {!running && (
        <button onClick={onDismiss} className="text-[var(--c-dim)] hover:text-[var(--c-sub)] ml-2">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

/* ─── ResultModal ───────────────────────────────────────────── */

function ResultModal({ datasetId, onClose }) {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(true);
  const [err,     setErr]     = useState('');
  const [tab,     setTab]     = useState('overview');

  useEffect(() => {
    setLoading(true); setErr(''); setResult(null);
    fetchResult(datasetId)
      .then(data => { setResult(data); })
      .catch(e   => { setErr(e.message); })
      .finally(  () => setLoading(false));
  }, [datasetId]);

  const fmt = (v) => (v == null ? '—' : v);

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 overflow-y-auto flex items-start justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="w-full max-w-2xl mt-10 mb-10 rounded-2xl border border-[var(--c-border)] bg-[var(--c-surface)] shadow-2xl">

        {/* header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--c-border)]">
          <div className="flex items-center gap-3">
            <BarChart2 className="w-4 h-4 text-indigo-400" />
            <p className="font-bold text-[var(--c-text)]">
              {loading ? 'Loading results…' : result ? result.company : 'Results'}
            </p>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-[var(--c-ghost)] flex items-center justify-center text-[var(--c-muted)] hover:text-[var(--c-text)] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16"><Spinner size={8} /></div>
        )}

        {!loading && err && (
          <div className="m-6 flex gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">Failed to load results: {err}</p>
          </div>
        )}

        {!loading && !err && !result && (
          <div className="text-center py-16">
            <p className="text-[var(--c-sub)] text-sm">No results yet — run Training first.</p>
          </div>
        )}

        {!loading && !err && result && (
          <>
            {/* tabs */}
            <div className="flex gap-1 px-6 pt-4">
              {['overview','sentiment','prices'].map(t => (
                <button key={t} onClick={() => setTab(t)}
                  className={cx('px-4 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors',
                    tab === t
                      ? 'bg-indigo-500/10 border border-indigo-500/30 text-indigo-400'
                      : 'text-[var(--c-muted)] hover:text-[var(--c-sub)]')}>
                  {t}
                </button>
              ))}
            </div>

            <div className="p-6 space-y-4">

              {/* ── overview ── */}
              {tab === 'overview' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { k: 'Signal',     v: result.signal },
                      { k: 'Confidence', v: `${fmt(result.confidence)}%` },
                      { k: 'Score',      v: result.composite_score != null ? (result.composite_score >= 0 ? '+' : '') + result.composite_score : '—' },
                      { k: 'Total Rows', v: result.total_rows?.toLocaleString() ?? '—' },
                    ].map(({ k, v }) => (
                      <div key={k} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-bg)] p-4 text-center">
                        <p className="text-[10px] text-[var(--c-muted)] uppercase tracking-wide mb-1">{k}</p>
                        <p className={cx('text-base font-bold',
                          k === 'Signal'
                            ? v === 'BUY'  ? 'text-emerald-400'
                            : v === 'SELL' ? 'text-red-400'
                                           : 'text-amber-400'
                            : 'text-[var(--c-text)]')}>
                          {v}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* trained at */}
                  <div className="rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] px-4 py-3 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[var(--c-muted)] shrink-0" />
                    <p className="text-xs text-[var(--c-sub)]">Trained at: <span className="text-[var(--c-text)]">{result.trained_at}</span></p>
                    <span className="mx-2 text-[var(--c-border)]">·</span>
                    <p className="text-xs text-[var(--c-sub)]">{result.total_columns} columns</p>
                  </div>

                  {/* errors / warnings */}
                  {result.errors?.length > 0 && (
                    <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 space-y-1">
                      <p className="text-xs font-semibold text-amber-400">Warnings ({result.errors.length})</p>
                      {result.errors.map((e, i) => <p key={i} className="text-xs text-amber-300/70">• {e}</p>)}
                    </div>
                  )}
                </div>
              )}

              {/* ── sentiment ── */}
              {tab === 'sentiment' && (
                <div className="max-h-96 overflow-y-auto space-y-2 pr-1">
                  {!(result.sentiment_rows?.length)
                    ? (
                      <div className="text-center py-12">
                        <p className="text-[var(--c-muted)] text-sm">No text columns found in this dataset.</p>
                        <p className="text-[var(--c-dim)] text-xs mt-1">Sentiment analysis requires headline / text columns.</p>
                      </div>
                    )
                    : result.sentiment_rows.map(r => (
                      <div key={r.row} className="flex gap-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] p-3">
                        <span className="text-xs font-mono text-[var(--c-dim)] w-6 shrink-0 mt-0.5">#{r.row}</span>
                        <p className="flex-1 text-xs text-[var(--c-sub)] leading-relaxed">{r.text}</p>
                        <div className="shrink-0 text-right space-y-1">
                          <Pill label={r.label}
                            color={r.label === 'Positive' ? 'emerald' : r.label === 'Negative' ? 'red' : 'slate'} />
                          <p className={cx('text-[11px] font-mono',
                            r.score > 0 ? 'text-emerald-400' : r.score < 0 ? 'text-red-400' : 'text-[var(--c-muted)]')}>
                            {r.score > 0 ? '+' : ''}{r.score}
                          </p>
                        </div>
                      </div>
                    ))
                  }
                </div>
              )}

              {/* ── prices ── */}
              {tab === 'prices' && (
                <div className="space-y-3">
                  {!(result.price_analyses?.length)
                    ? (
                      <div className="text-center py-12">
                        <p className="text-[var(--c-muted)] text-sm">No numeric price columns found.</p>
                      </div>
                    )
                    : result.price_analyses.map(p => (
                      <div key={p.column} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-bg)] p-4">
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-sm font-semibold text-[var(--c-text)]">{p.column}</p>
                          <div className="flex items-center gap-1.5">
                            {p.trend === 'Uptrend'
                              ? <TrendingUp   className="w-4 h-4 text-emerald-400" />
                              : <TrendingDown className="w-4 h-4 text-red-400" />}
                            <span className={p.trend === 'Uptrend' ? 'text-xs text-emerald-400' : 'text-xs text-red-400'}>
                              {p.trend}
                            </span>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                          {[
                            ['First',      fmt(p.first)],
                            ['Last',       fmt(p.last)],
                            ['Min',        fmt(p.min)],
                            ['Max',        fmt(p.max)],
                            ['Return',     p.total_return_pct != null ? `${p.total_return_pct >= 0 ? '+' : ''}${p.total_return_pct}%` : '—'],
                            ['Volatility', p.volatility_pct   != null ? `${p.volatility_pct}%` : '—'],
                          ].map(([k, v]) => (
                            <div key={k} className="text-center">
                              <p className="text-[10px] text-[var(--c-muted)] uppercase tracking-wide">{k}</p>
                              <p className="text-sm font-bold text-[var(--c-text)] truncate">{v}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))
                  }
                </div>
              )}

            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ─── AdminPanel ────────────────────────────────────────────── */

export default function AdminPanel() {
  const navigate      = useNavigate();
  const { theme, toggle } = useTheme();
  const [ready,       setReady]       = useState(false);
  const [datasets,    setDatasets]    = useState([]);
  const [loadingDs,   setLoadingDs]   = useState(true);
  const [trainStatus, setTrainStatus] = useState(null);
  const [trainingId,  setTrainingId]  = useState(null);
  const [resultId,    setResultId]    = useState(null);
  const [globalErr,   setGlobalErr]   = useState('');
  const pollRef = useRef(null);

  const loadDatasets = useCallback(async () => {
    setLoadingDs(true);
    setGlobalErr('');
    try {
      const data = await fetchDatasets();
      setDatasets(data);
    } catch (e) {
      setGlobalErr('Failed to load datasets: ' + e.message);
    } finally {
      setLoadingDs(false);
    }
  }, []);

  /* auth guard — then load */
  useEffect(() => {
    adminVerify().then(ok => {
      if (!ok) { navigate('/admin/login'); return; }
      setReady(true);
      loadDatasets();
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /* poll training */
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
          loadDatasets();
        }
      } catch { /* ignore */ }
    }, 2000);
  }, [loadDatasets]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const handleUploaded = (meta) => setDatasets(prev => [meta, ...prev]);
  const handleDelete   = async (id) => { await deleteDataset(id); setDatasets(prev => prev.filter(d => d.id !== id)); };
  const handleTrain    = async (id) => {
    setTrainingId(id);
    setTrainStatus({ status: 'running', progress: 'Starting…', error: null });
    try   { await startTraining(id); startPoll(); }
    catch (e) { setTrainStatus({ status: 'error', error: e.message }); setTrainingId(null); }
  };
  const handleLogout = () => { adminLogout(); navigate('/admin/login'); };

  /* show spinner while verifying auth */
  if (!ready) return (
    <div className="min-h-screen bg-[var(--c-bg)] flex items-center justify-center">
      <Spinner size={8} />
    </div>
  );

  return (
    <div className="min-h-screen bg-[var(--c-bg)] transition-colors">

      {/* ── header ── */}
      <header className="sticky top-0 z-20 border-b border-[var(--c-border)] bg-[var(--c-bg)]/90 backdrop-blur-sm transition-colors">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 h-14 flex items-center justify-between">

          {/* brand */}
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-[15px] text-[var(--c-text)]">Admin Panel</span>
            <Pill label="SentXStock" color="indigo" />
          </div>

          {/* right */}
          <div className="flex items-center gap-2">
            {/* theme toggle */}
            <button
              onClick={toggle}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="w-8 h-8 flex items-center justify-center rounded-md border border-[var(--c-border)] text-[var(--c-muted)] hover:text-[var(--c-text)] hover:border-[var(--c-border2)] transition-colors"
            >
              {theme === 'dark'
                ? <Sun  className="w-3.5 h-3.5" />
                : <Moon className="w-3.5 h-3.5" />}
            </button>

            <a href="/" className="text-xs text-[var(--c-muted)] hover:text-indigo-400 transition-colors px-2">
              ← Public
            </a>

            <button onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--c-border)] text-xs text-[var(--c-muted)] hover:text-red-400 hover:border-red-500/30 transition-colors">
              <LogOut className="w-3.5 h-3.5" /> Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 space-y-8">

        {/* global error */}
        {globalErr && (
          <div className="flex gap-2 items-start rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">{globalErr}</p>
          </div>
        )}

        {/* training banner */}
        <TrainingBanner status={trainStatus} onDismiss={() => setTrainStatus(null)} />

        {/* ── stats ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Datasets',   value: datasets.length,                                         Icon: Database,    c: 'text-indigo-400' },
            { label: 'Trained',    value: datasets.filter(d => d.trained).length,                  Icon: CheckCircle, c: 'text-emerald-400' },
            { label: 'Pending',    value: datasets.filter(d => !d.trained).length,                 Icon: Clock,       c: 'text-amber-400' },
            { label: 'Total Rows', value: datasets.reduce((s, d) => s + (d.rows || 0), 0).toLocaleString(), Icon: BarChart2, c: 'text-[var(--c-muted)]' },
          ].map(({ label, value, Icon, c }) => (
            <div key={label} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={cx('w-4 h-4', c)} />
                <p className="text-[11px] text-[var(--c-muted)] uppercase tracking-wide">{label}</p>
              </div>
              <p className="text-2xl font-extrabold text-[var(--c-text)]">{value}</p>
            </div>
          ))}
        </div>

        {/* ── upload ── */}
        <section className="rounded-2xl border border-[var(--c-border)] bg-[var(--c-surface)] p-6">
          <div className="flex items-center gap-2.5 mb-5">
            <Upload className="w-4 h-4 text-indigo-400" />
            <p className="font-bold text-[15px] text-[var(--c-text)]">Upload Dataset</p>
            <span className="text-xs text-[var(--c-muted)]">CSV · XLSX · XLS · JSON · SQL</span>
          </div>
          <UploadForm onUploaded={handleUploaded} />
        </section>

        {/* ── datasets list ── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <Database className="w-4 h-4 text-indigo-400" />
              <p className="font-bold text-[15px] text-[var(--c-text)]">Datasets</p>
              <span className="text-xs text-[var(--c-muted)]">{datasets.length} total</span>
            </div>
            <button onClick={loadDatasets}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--c-border)] text-xs text-[var(--c-muted)] hover:text-indigo-400 transition-colors">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
          </div>

          {loadingDs ? (
            <div className="flex items-center justify-center py-16"><Spinner size={6} /></div>
          ) : datasets.length === 0 ? (
            <div className="text-center py-16 rounded-xl border border-dashed border-[var(--c-border)]">
              <Database className="w-10 h-10 text-[var(--c-dimmer)] mx-auto mb-3" />
              <p className="text-[var(--c-sub)] text-sm">No datasets uploaded yet.</p>
              <p className="text-[var(--c-dim)] text-xs mt-1">Use the form above to add your first one.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {datasets.map(ds => (
                <DatasetCard
                  key={ds.id}
                  ds={ds}
                  trainingId={trainingId}
                  onTrain={handleTrain}
                  onDelete={handleDelete}
                  onResult={setResultId}
                />
              ))}
            </div>
          )}
        </section>

      </main>

      {resultId && (
        <ResultModal datasetId={resultId} onClose={() => setResultId(null)} />
      )}
    </div>
  );
}
