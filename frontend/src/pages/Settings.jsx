import { useState, useEffect } from 'react';
import {
  Save,
  ShieldCheck,
  Shield,
  ShieldAlert,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { getSettings, setTickers, setPortfolio } from '../services/api';

const RISK = [
  { val: 'low',    label: 'Conservative', alloc: '25 / 35 / 40', icon: ShieldCheck, color: '#22c55e' },
  { val: 'medium', label: 'Moderate',     alloc: '50 / 30 / 20', icon: Shield,      color: '#3b82f6' },
  { val: 'high',   label: 'Aggressive',   alloc: '70 / 15 / 15', icon: ShieldAlert, color: '#ef4444' },
];

export default function SettingsPage({ onSaved }) {
  const [tks, setTks] = useState('');
  const [cash, setCash] = useState('100000');
  const [risk, setRisk] = useState('medium');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await getSettings();
        const s = r.data;
        if (s.tickers?.length) setTks(s.tickers.join(', '));
        if (s.cash) setCash(String(s.cash));
        if (s.risk_preference) setRisk(s.risk_preference);
      } catch {}
    })();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);

  const save = async () => {
    const list = tks.split(/[,\s]+/).map(t => t.trim().toUpperCase()).filter(Boolean);
    if (!list.length) return setToast({ ok: false, msg: 'Enter at least one ticker' });
    const n = parseFloat(cash);
    if (isNaN(n) || n <= 0) return setToast({ ok: false, msg: 'Enter a valid amount' });

    setSaving(true);
    try {
      await setTickers(list);
      await setPortfolio(n, risk);
      setToast({ ok: true, msg: 'Saved — run Analysis to refresh dashboard' });
      onSaved?.(); // clear stale dashboard data in App.jsx
    } catch (e) {
      setToast({ ok: false, msg: e.response?.data?.message || 'Failed' });
    } finally { setSaving(false); }
  };

  return (
    <div className="max-w-xl mx-auto space-y-5">
      <h1 className="text-[18px] font-semibold text-white">Settings</h1>

      {/* Tickers */}
      <div className="card p-5 space-y-3">
        <label className="text-[12px] font-medium text-[#64748b]">Tickers</label>
        <input
          type="text"
          value={tks}
          onChange={(e) => setTks(e.target.value)}
          placeholder="AAPL, TSLA, MSFT, GOOGL"
          className="w-full px-3 py-2.5 rounded-md bg-[#080c14] border border-[#151d2e] text-[13px] text-white placeholder-[#2a3344]"
        />
        <p className="text-[11px] text-[#374151]">Comma-separated stock symbols (max 10)</p>
      </div>

      {/* Cash */}
      <div className="card p-5 space-y-3">
        <label className="text-[12px] font-medium text-[#64748b]">Portfolio cash</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[13px] text-[#374151]">$</span>
          <input
            type="text"
            value={cash}
            onChange={(e) => setCash(e.target.value.replace(/[^0-9.]/g, ''))}
            className="w-full pl-7 pr-3 py-2.5 rounded-md bg-[#080c14] border border-[#151d2e] text-[13px] text-white mono placeholder-[#2a3344]"
          />
        </div>
      </div>

      {/* Risk */}
      <div className="card p-5 space-y-3">
        <label className="text-[12px] font-medium text-[#64748b]">Risk preference</label>
        <div className="grid grid-cols-3 gap-2">
          {RISK.map((r) => {
            const Icon = r.icon;
            const on = risk === r.val;
            return (
              <button
                key={r.val}
                onClick={() => setRisk(r.val)}
                className="p-3 rounded-md border text-left transition-colors"
                style={{
                  borderColor: on ? `${r.color}50` : '#151d2e',
                  background: on ? `${r.color}08` : 'transparent',
                }}
              >
                <Icon className="w-4 h-4 mb-1.5" style={{ color: on ? r.color : '#374151' }} />
                <p className="text-[12px] font-semibold" style={{ color: on ? r.color : '#64748b' }}>
                  {r.label}
                </p>
                <p className="text-[10px] text-[#374151] mt-0.5 mono">{r.alloc}</p>
              </button>
            );
          })}
        </div>
        <p className="text-[10px] text-[#374151]">Equity / Bonds / Cash percentages</p>
      </div>

      {/* Save button */}
      <button
        onClick={save}
        disabled={saving}
        className="w-full flex items-center justify-center gap-1.5 h-10 rounded-md text-[13px] font-semibold
          bg-[#2563eb] text-white hover:bg-[#1d4ed8] disabled:opacity-40 transition-colors"
      >
        {saving
          ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…</>
          : <><Save className="w-3.5 h-3.5" /> Save Settings</>}
      </button>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-5 right-5 toast-enter flex items-center gap-2 px-3.5 py-2.5 rounded-md text-[12px] font-medium border ${
          toast.ok
            ? 'bg-[#22c55e]/10 border-[#22c55e]/20 text-[#22c55e]'
            : 'bg-[#ef4444]/10 border-[#ef4444]/20 text-[#ef4444]'
        }`}>
          {toast.ok ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
          {toast.msg}
        </div>
      )}
    </div>
  );
}
