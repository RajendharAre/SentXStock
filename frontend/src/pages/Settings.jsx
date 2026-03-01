/**
 * Settings Page — Module 6
 *
 * Sections:
 *  1. Appearance   — Dark / Light / System theme switcher
 *  2. Portfolio    — Starting capital (INR), risk preference
 *  3. Data         — Mock mode toggle, live re-analysis trigger
 *  4. Admin        — Gated behind credentials; CSV upload + company list
 *
 * Admin credentials (demo only — no real security implied):
 *   Username: admin_sentxstock
 *   Password: Admin@33*
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Save, Sun, Moon, Monitor,
  ShieldCheck, Shield, ShieldAlert,
  Loader2, CheckCircle2, XCircle,
  Lock, Unlock, Eye, EyeOff,
  RefreshCw, Database, AlertTriangle,
  Upload, Users, LogOut,
} from 'lucide-react';
import {
  getSettings, setPortfolio, runAnalysis, getAllCompanies,
} from '../services/api';

// ── Admin credentials (demo only) ────────────────────────────
const ADMIN_USER = 'admin';
const ADMIN_PASS = 'sentxadmin123';

// ── Theme helpers ─────────────────────────────────────────────
function applyTheme(mode) {
  const html = document.documentElement;
  if (mode === 'light') {
    html.classList.add('light');
  } else if (mode === 'dark') {
    html.classList.remove('light');
  } else {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    prefersDark ? html.classList.remove('light') : html.classList.add('light');
  }
  localStorage.setItem('theme', mode);
}

// ── Risk options ──────────────────────────────────────────────
const RISK_OPTIONS = [
  { val: 'low',    label: 'Conservative', note: '25% Equity · 35% Bonds · 40% Cash', Icon: ShieldCheck, color: '#22c55e' },
  { val: 'medium', label: 'Moderate',     note: '50% Equity · 30% Bonds · 20% Cash', Icon: Shield,      color: '#3b82f6' },
  { val: 'high',   label: 'Aggressive',   note: '70% Equity · 15% Bonds · 15% Cash', Icon: ShieldAlert, color: '#ef4444' },
];

// ── Reusable section card ─────────────────────────────────────
function Section({ title, icon: Icon, iconColor, children }) {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${iconColor || 'text-[var(--c-sub)]'}`} />
        <span className="text-[13px] font-bold text-[var(--c-text)]">{title}</span>
      </div>
      {children}
    </div>
  );
}

// ── Toast notification ────────────────────────────────────────
function Toast({ toast }) {
  if (!toast) return null;
  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl text-[12px] font-medium border shadow-xl ${
        toast.ok
          ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400'
          : 'bg-rose-500/10 border-rose-500/25 text-rose-400'
      }`}
    >
      {toast.ok
        ? <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
        : <XCircle className="w-3.5 h-3.5 flex-shrink-0" />}
      {toast.msg}
    </div>
  );
}

// ── Chevron helper ────────────────────────────────────────────
function ChevronIcon({ open }) {
  return (
    <svg
      className={`w-4 h-4 text-[var(--c-dim)] transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

// ── Admin Panel (shown only after login) ──────────────────────
function AdminPanel({ showToast }) {
  const [companies, setCompanies]       = useState([]);
  const [compLoading, setCompLoading]   = useState(false);
  const [sectorFilter, setSectorFilter] = useState('All');
  const [uploading, setUploading]       = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileRef = useRef(null);

  const loadCompanies = useCallback(async () => {
    setCompLoading(true);
    try {
      const r = await getAllCompanies();
      setCompanies(r.data?.companies || r.data || []);
    } catch {
      setCompanies([]);
    } finally {
      setCompLoading(false);
    }
  }, []);

  useEffect(() => { loadCompanies(); }, [loadCompanies]);

  const sectors = ['All', ...Array.from(new Set(companies.map(c => c.sector))).sort()];
  const visible  = sectorFilter === 'All' ? companies : companies.filter(c => c.sector === sectorFilter);

  const handleCSV = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      showToast({ ok: false, msg: 'Please upload a .csv file' });
      return;
    }
    setUploading(true);
    setUploadResult(null);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const lines = ev.target.result.trim().split('\n');
      const hasHeader = lines[0].toLowerCase().replace(/\s/g, '').includes('ticker');
      const parsed = (hasHeader ? lines.slice(1) : lines)
        .map(line => {
          const cols = line.split(',').map(c => c.trim().replace(/^"|"$/g, ''));
          if (cols.length < 2 || !cols[0]) return null;
          const ticker = cols[0].toUpperCase().endsWith('.NS')
            ? cols[0].toUpperCase()
            : cols[0].toUpperCase() + '.NS';
          return { ticker, name: cols[1] || cols[0], sector: cols[2] || 'Other' };
        })
        .filter(Boolean);
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
      if (!parsed.length) {
        showToast({ ok: false, msg: 'No valid rows found. Format: ticker, name, sector' });
        return;
      }
      setUploadResult({ count: parsed.length, preview: parsed.slice(0, 5) });
      showToast({ ok: true, msg: `${parsed.length} companies parsed successfully` });
    };
    reader.readAsText(file);
  };

  return (
    <div className="space-y-5">

      {/* Company viewer */}
      <div className="card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-[12px] font-bold text-[var(--c-text)]">Company Universe</span>
            {companies.length > 0 && (
              <span className="mono text-[10px] px-1.5 py-0.5 rounded border border-indigo-500/25 bg-indigo-500/10 text-indigo-400">
                {companies.length}
              </span>
            )}
          </div>
          <button
            onClick={loadCompanies}
            disabled={compLoading}
            className="flex items-center gap-1 text-[11px] text-[var(--c-dim)] hover:text-[var(--c-sub)] transition-colors"
          >
            <RefreshCw className={`w-3 h-3 ${compLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Sector filter chips */}
        <div className="flex flex-wrap gap-1.5">
          {sectors.map(s => (
            <button
              key={s}
              onClick={() => setSectorFilter(s)}
              className={`px-2.5 py-1 rounded text-[10px] font-medium border transition-colors ${
                sectorFilter === s
                  ? 'bg-indigo-500/15 border-indigo-500/30 text-indigo-400'
                  : 'bg-transparent border-[var(--c-border)] text-[var(--c-dim)] hover:border-[var(--c-border2)]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="max-h-60 overflow-y-auto rounded-lg border border-[var(--c-border)]">
          {compLoading ? (
            <div className="flex items-center justify-center py-8 gap-2 text-[12px] text-[var(--c-dim)]">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading…
            </div>
          ) : (
            <table className="w-full text-[11px]">
              <thead className="sticky top-0 bg-[var(--c-surface2)] border-b border-[var(--c-border)]">
                <tr>
                  <th className="text-left px-3 py-1.5 text-[var(--c-dimmer)] font-semibold uppercase tracking-wide">Ticker</th>
                  <th className="text-left px-3 py-1.5 text-[var(--c-dimmer)] font-semibold uppercase tracking-wide">Company</th>
                  <th className="text-left px-3 py-1.5 text-[var(--c-dimmer)] font-semibold uppercase tracking-wide hidden sm:table-cell">Sector</th>
                </tr>
              </thead>
              <tbody>
                {visible.slice(0, 100).map((c, i) => (
                  <tr key={c.ticker + i} className="border-b border-[var(--c-border)] last:border-none hover:bg-[var(--c-ghost)] transition-colors">
                    <td className="px-3 py-1.5 mono text-indigo-400 font-medium">{c.ticker}</td>
                    <td className="px-3 py-1.5 text-[var(--c-text)]">{c.name}</td>
                    <td className="px-3 py-1.5 text-[var(--c-muted)] hidden sm:table-cell">{c.sector}</td>
                  </tr>
                ))}
                {visible.length > 100 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-2 text-center text-[var(--c-dimmer)] text-[10px]">
                      Showing 100 of {visible.length} — filter by sector to see all
                    </td>
                  </tr>
                )}
                {visible.length === 0 && !compLoading && (
                  <tr>
                    <td colSpan={3} className="px-3 py-4 text-center text-[var(--c-dim)] text-[11px]">No companies found</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* CSV Upload */}
      <div className="card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Upload className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-[12px] font-bold text-[var(--c-text)]">Upload Custom Company List</span>
        </div>
        <p className="text-[11px] text-[var(--c-dim)]">
          CSV format: <span className="mono text-amber-400">ticker, company_name, sector</span> — one company per row. Header row is optional.
        </p>

        <label
          htmlFor="csv-upload"
          className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-[var(--c-border2)] rounded-xl py-8 cursor-pointer hover:border-indigo-500/40 hover:bg-indigo-500/5 transition-all"
        >
          <Upload className="w-5 h-5 text-[var(--c-dim)]" />
          <span className="text-[12px] font-medium text-[var(--c-sub)]">Click to select a .csv file</span>
          <span className="text-[10px] text-[var(--c-dimmer)]">ticker · name · sector columns required</span>
        </label>
        <input id="csv-upload" ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleCSV} />

        {uploading && (
          <div className="flex items-center gap-2 text-[12px] text-[var(--c-dim)]">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Parsing CSV…
          </div>
        )}

        {uploadResult && !uploading && (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 space-y-2">
            <p className="text-[12px] font-bold text-emerald-400">{uploadResult.count} companies parsed successfully</p>
            <div className="space-y-1">
              {uploadResult.preview.map((c, i) => (
                <p key={i} className="text-[10px] mono text-[var(--c-dim)]">{c.ticker} · {c.name} · {c.sector}</p>
              ))}
              {uploadResult.count > 5 && (
                <p className="text-[10px] text-[var(--c-dimmer)]">… and {uploadResult.count - 5} more</p>
              )}
            </div>
            <p className="text-[10px] text-[var(--c-dimmer)] border-t border-emerald-500/10 pt-2">
              Companies parsed and ready. Backend ingestion merges them into the live NSE universe.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Settings Page ────────────────────────────────────────
export default function SettingsPage({ onSaved }) {
  // Theme
  const [theme, setTheme]   = useState(() => localStorage.getItem('theme') || 'dark');
  // Portfolio
  const [cash, setCash]     = useState('50000');
  const [risk, setRisk]     = useState('medium');
  const [saving, setSaving] = useState(false);
  // Data
  const [mockMode, setMockMode] = useState(false);
  const [updating, setUpdating] = useState(false);
  // Admin
  const [adminOpen, setAdminOpen]       = useState(false);
  const [adminUser, setAdminUser]       = useState('');
  const [adminPass, setAdminPass]       = useState('');
  const [showPass, setShowPass]         = useState(false);
  const [adminAuth, setAdminAuth]       = useState(() => sessionStorage.getItem('_adm') === '1');
  const [loginErr, setLoginErr]         = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  // Toast
  const [toast, setToast] = useState(null);

  const showToast = useCallback((t) => setToast(t), []);

  // Load settings on mount + apply saved theme
  useEffect(() => {
    (async () => {
      try {
        const r = await getSettings();
        const s = r.data;
        if (s.cash)            setCash(String(s.cash));
        if (s.risk_preference) setRisk(s.risk_preference.toLowerCase());
      } catch {}
    })();
    applyTheme(localStorage.getItem('theme') || 'dark');
  }, []);

  // OS theme change listener (for system mode)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onchange = () => { if (theme === 'system') applyTheme('system'); };
    mq.addEventListener('change', onchange);
    return () => mq.removeEventListener('change', onchange);
  }, [theme]);

  // Toast auto-dismiss
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  const handleTheme = (mode) => { setTheme(mode); applyTheme(mode); };

  const handleSave = async () => {
    const n = parseFloat(cash.replace(/,/g, ''));
    if (isNaN(n) || n <= 0) { showToast({ ok: false, msg: 'Enter a valid starting capital in INR' }); return; }
    setSaving(true);
    try {
      await setPortfolio(n, risk);
      showToast({ ok: true, msg: 'Portfolio settings saved' });
      onSaved?.();
    } catch (e) {
      showToast({ ok: false, msg: e.response?.data?.message || 'Failed to save' });
    } finally { setSaving(false); }
  };

  const handleUpdateData = async () => {
    setUpdating(true);
    try {
      await runAnalysis(mockMode);
      showToast({ ok: true, msg: mockMode ? 'Mock analysis started — check Dashboard shortly' : 'Live data fetch started — check Dashboard shortly' });
    } catch (e) {
      showToast({ ok: false, msg: e.response?.data?.error || 'Update failed' });
    } finally { setUpdating(false); }
  };

  const handleAdminLogin = async () => {
    setLoginLoading(true);
    setLoginErr('');
    await new Promise(r => setTimeout(r, 700));
    if (adminUser === ADMIN_USER && adminPass === ADMIN_PASS) {
      sessionStorage.setItem('_adm', '1');
      setAdminAuth(true);
      setAdminUser('');
      setAdminPass('');
    } else {
      setLoginErr('Invalid credentials. Access denied.');
    }
    setLoginLoading(false);
  };

  const handleAdminLogout = () => {
    sessionStorage.removeItem('_adm');
    setAdminAuth(false);
  };

  const THEMES = [
    { id: 'dark',   label: 'Dark',   Icon: Moon    },
    { id: 'light',  label: 'Light',  Icon: Sun     },
    { id: 'system', label: 'System', Icon: Monitor },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-5 pb-12">

      {/* Page header */}
      <div>
        <h1 className="text-[20px] font-bold text-[var(--c-text)]">Settings</h1>
        <p className="text-[12px] text-[var(--c-dim)] mt-0.5">
          Appearance, portfolio defaults, data preferences and admin controls.
        </p>
      </div>

      {/* ── 1. Appearance ── */}
      <Section title="Appearance" icon={Sun} iconColor="text-amber-400">
        <p className="text-[11px] text-[var(--c-dim)] -mt-2">
          Choose your preferred colour theme. Changes apply instantly across the entire app.
        </p>
        <div className="grid grid-cols-3 gap-3">
          {THEMES.map(({ id, label, Icon }) => {
            const active = theme === id;
            return (
              <button
                key={id}
                onClick={() => handleTheme(id)}
                className={`flex flex-col items-center gap-2.5 py-5 px-3 rounded-xl border transition-all ${
                  active
                    ? 'border-[#2563eb]/50 bg-[#2563eb]/10'
                    : 'border-[var(--c-border)] hover:border-[var(--c-border2)]'
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-[#60a5fa]' : 'text-[var(--c-muted)]'}`} />
                <span className={`text-[11px] font-semibold ${active ? 'text-[#60a5fa]' : 'text-[var(--c-muted)]'}`}>
                  {label}
                </span>
                {active && (
                  <span className="text-[9px] font-bold uppercase tracking-wider text-[#60a5fa] opacity-80">Active</span>
                )}
              </button>
            );
          })}
        </div>
      </Section>

      {/* ── 2. Portfolio Defaults ── */}
      <Section title="Portfolio Defaults" icon={ShieldCheck} iconColor="text-emerald-400">
        <p className="text-[11px] text-[var(--c-dim)] -mt-2">
          Starting capital and risk profile used by the sentiment-driven allocation engine.
        </p>

        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-[var(--c-muted)] uppercase tracking-wide">
            Starting Capital (INR)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[14px] font-bold text-[var(--c-dim)]">₹</span>
            <input
              type="text"
              value={cash}
              onChange={(e) => setCash(e.target.value.replace(/[^0-9.]/g, ''))}
              placeholder="50000"
              className="w-full pl-8 pr-3 py-2.5 rounded-lg bg-[var(--c-bg)] border border-[var(--c-border)] text-[13px] text-[var(--c-text)] mono placeholder-[var(--c-placeholder)] focus:outline-none focus:border-[#2563eb]/50 transition-colors"
            />
          </div>
          <p className="text-[10px] text-[var(--c-dimmer)]">
            Default ₹50,000 · Maximum single position capped at 20% of total capital
          </p>
        </div>

        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-[var(--c-muted)] uppercase tracking-wide">Risk Preference</label>
          <div className="grid grid-cols-3 gap-2">
            {RISK_OPTIONS.map(({ val, label, note, Icon, color }) => {
              const active = risk === val;
              return (
                <button
                  key={val}
                  onClick={() => setRisk(val)}
                  className="p-4 rounded-xl border text-left transition-all"
                  style={{
                    borderColor: active ? `${color}45` : 'var(--c-border)',
                    background:  active ? `${color}09` : 'transparent',
                  }}
                >
                  <Icon className="w-4 h-4 mb-2" style={{ color: active ? color : 'var(--c-dimmer)' }} />
                  <p className="text-[12px] font-bold" style={{ color: active ? color : 'var(--c-muted)' }}>{label}</p>
                  <p className="text-[9px] mono text-[var(--c-dimmer)] mt-0.5 leading-relaxed">{note}</p>
                </button>
              );
            })}
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 h-10 rounded-lg text-[13px] font-semibold bg-[#2563eb] text-white hover:bg-[#1d4ed8] disabled:opacity-40 transition-colors"
        >
          {saving
            ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…</>
            : <><Save className="w-3.5 h-3.5" /> Save Portfolio Settings</>}
        </button>
      </Section>

      {/* ── 3. Data Preferences ── */}
      <Section title="Data Preferences" icon={Database} iconColor="text-sky-400">
        <p className="text-[11px] text-[var(--c-dim)] -mt-2">
          Control how the analysis engine fetches and processes NSE market data.
        </p>

        {/* Mock mode toggle */}
        <div className="flex items-center justify-between p-4 rounded-xl border border-[var(--c-border)] bg-[var(--c-bg)]">
          <div>
            <p className="text-[12px] font-semibold text-[var(--c-text)]">Mock Mode</p>
            <p className="text-[10px] text-[var(--c-dimmer)] mt-0.5 max-w-xs">
              Use synthetic data instead of live NSE feeds. Useful for offline testing or demos.
            </p>
          </div>
          <button
            onClick={() => setMockMode(v => !v)}
            aria-label="Toggle mock mode"
            className={`relative flex-shrink-0 ml-4 w-11 h-6 rounded-full transition-colors duration-200 ${mockMode ? 'bg-amber-500' : 'bg-[var(--c-ghost)]'}`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${mockMode ? 'translate-x-5' : 'translate-x-0'}`}
            />
          </button>
        </div>

        {mockMode && (
          <div className="flex items-start gap-2 px-3.5 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5 text-[11px] text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>Mock Mode is ON — analysis will use synthetic data, not live NSE prices or news feeds.</span>
          </div>
        )}

        <button
          onClick={handleUpdateData}
          disabled={updating}
          className={`w-full flex items-center justify-center gap-2 h-10 rounded-lg text-[13px] font-semibold border transition-colors disabled:opacity-40 ${
            mockMode
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20'
              : 'border-sky-500/30 bg-sky-500/10 text-sky-400 hover:bg-sky-500/20'
          }`}
        >
          {updating
            ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Starting…</>
            : <><RefreshCw className="w-3.5 h-3.5" /> {mockMode ? 'Run Mock Analysis' : 'Fetch Live Data & Re-analyse'}</>}
        </button>
      </Section>

      {/* ── 4. Admin ── */}
      <div className="card overflow-hidden">

        {/* Header always visible */}
        <button
          onClick={() => setAdminOpen(v => !v)}
          className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[var(--c-ghost)] transition-colors"
        >
          <div className="flex items-center gap-2.5">
            {adminAuth
              ? <Unlock className="w-4 h-4 text-rose-400" />
              : <Lock className="w-4 h-4 text-[var(--c-dim)]" />}
            <span className={`text-[13px] font-bold ${adminAuth ? 'text-rose-400' : 'text-[var(--c-text)]'}`}>
              Admin Controls
            </span>
            {adminAuth && (
              <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border border-rose-500/25 bg-rose-500/10 text-rose-400">
                Authenticated
              </span>
            )}
          </div>
          <ChevronIcon open={adminOpen} />
        </button>

        {adminOpen && (
          <div className="border-t border-[var(--c-border)] px-5 py-5 space-y-4">
            {!adminAuth ? (
              /* Login gate */
              <div className="space-y-4">
                <div className="flex items-start gap-2.5 px-3.5 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-[11px] text-[var(--c-dim)] leading-relaxed">
                    Admin area is restricted to authorised personnel only.
                    Unauthorised access attempts are logged and may result in account suspension.
                  </p>
                </div>

                <div className="space-y-2.5">
                  <input
                    type="text"
                    value={adminUser}
                    onChange={e => { setAdminUser(e.target.value); setLoginErr(''); }}
                    placeholder="Username"
                    autoComplete="off"
                    className="w-full px-3.5 py-2.5 rounded-lg bg-[var(--c-bg)] border border-[var(--c-border)] text-[13px] text-[var(--c-text)] placeholder-[var(--c-placeholder)] focus:outline-none focus:border-[#2563eb]/50 transition-colors"
                  />
                  <div className="relative">
                    <input
                      type={showPass ? 'text' : 'password'}
                      value={adminPass}
                      onChange={e => { setAdminPass(e.target.value); setLoginErr(''); }}
                      onKeyDown={e => e.key === 'Enter' && !loginLoading && adminUser && adminPass && handleAdminLogin()}
                      placeholder="Password"
                      autoComplete="new-password"
                      className="w-full px-3.5 pr-10 py-2.5 rounded-lg bg-[var(--c-bg)] border border-[var(--c-border)] text-[13px] text-[var(--c-text)] placeholder-[var(--c-placeholder)] focus:outline-none focus:border-[#2563eb]/50 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPass(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--c-dim)] hover:text-[var(--c-sub)] transition-colors"
                    >
                      {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {loginErr && (
                  <div className="flex items-center gap-2 text-[11px] text-rose-400">
                    <XCircle className="w-3.5 h-3.5 flex-shrink-0" /> {loginErr}
                  </div>
                )}

                <button
                  onClick={handleAdminLogin}
                  disabled={loginLoading || !adminUser || !adminPass}
                  className="w-full flex items-center justify-center gap-2 h-10 rounded-lg text-[13px] font-semibold border border-rose-500/30 bg-rose-600/15 text-rose-400 hover:bg-rose-600/25 disabled:opacity-40 transition-colors"
                >
                  {loginLoading
                    ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Verifying…</>
                    : <><Lock className="w-3.5 h-3.5" /> Sign In to Admin</>}
                </button>
              </div>

            ) : (
              /* Admin content */
              <div className="space-y-5">
                <div className="flex items-center justify-between px-3.5 py-2.5 rounded-lg border border-rose-500/20 bg-rose-500/5">
                  <p className="text-[11px] text-[var(--c-dim)]">
                    Signed in as&nbsp;<span className="mono font-semibold text-rose-400">{ADMIN_USER}</span>
                  </p>
                  <button
                    onClick={handleAdminLogout}
                    className="flex items-center gap-1.5 text-[11px] text-[var(--c-dim)] hover:text-rose-400 transition-colors"
                  >
                    <LogOut className="w-3 h-3" /> Sign out
                  </button>
                </div>
                <AdminPanel showToast={showToast} />
              </div>
            )}
          </div>
        )}
      </div>

      <Toast toast={toast} />
    </div>
  );
}
