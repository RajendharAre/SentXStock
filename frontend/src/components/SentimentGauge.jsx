import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function SentimentGauge({ score = 0, label = 'Neutral' }) {
  const pct = ((score + 1) / 2) * 100;

  const color =
    score > 0.05 ? '#22c55e' : score < -0.05 ? '#ef4444' : '#64748b';

  const Icon =
    score > 0.05 ? TrendingUp : score < -0.05 ? TrendingDown : Minus;

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-[11px] font-medium text-[var(--c-dim)] uppercase tracking-wide">
          Sentiment
        </span>
        <span className="pill" style={{ color, background: `${color}14` }}>
          <Icon className="w-3 h-3" />
          {label}
        </span>
      </div>

      {/* Big number */}
      <div className="flex items-baseline gap-1.5 mb-5">
        <span className="mono text-[32px] font-bold leading-none" style={{ color }}>
          {score > 0 ? '+' : ''}{score.toFixed(3)}
        </span>
      </div>

      {/* Gauge */}
      <div className="gauge-track">
        <div
          className="gauge-thumb"
          style={{ left: `calc(${pct}% - 6px)`, background: color }}
        />
      </div>
      <div className="flex justify-between mt-1.5">
        <span className="text-[10px] text-[var(--c-dimmer)]">-1.0</span>
        <span className="text-[10px] text-[var(--c-dimmer)]">0</span>
        <span className="text-[10px] text-[var(--c-dimmer)]">+1.0</span>
      </div>
    </div>
  );
}
