import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

const CFG = {
  high:   { icon: ShieldAlert,  color: '#ef4444', label: 'High',   tag: 'Aggressive' },
  medium: { icon: Shield,       color: '#3b82f6', label: 'Medium', tag: 'Balanced'   },
  low:    { icon: ShieldCheck,  color: '#22c55e', label: 'Low',    tag: 'Defensive'  },
  // Capitalize variants from backend
  High:   { icon: ShieldAlert,  color: '#ef4444', label: 'High',   tag: 'Aggressive' },
  Medium: { icon: Shield,       color: '#3b82f6', label: 'Medium', tag: 'Balanced'   },
  Low:    { icon: ShieldCheck,  color: '#22c55e', label: 'Low',    tag: 'Defensive'  },
};

export default function RiskLevel({ level = 'medium' }) {
  const c = CFG[level] || CFG.medium;
  const Icon = c.icon;

  return (
    <div className="card p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <span className="text-[11px] font-medium text-[var(--c-dim)] uppercase tracking-wide">
          Risk Level
        </span>
        <Icon className="w-4 h-4" style={{ color: c.color }} />
      </div>

      <div>
        <span className="text-[28px] font-bold text-[var(--c-text)] leading-none">{c.label}</span>
        <p className="text-[12px] mt-1.5" style={{ color: c.color }}>{c.tag}</p>
      </div>
    </div>
  );
}
