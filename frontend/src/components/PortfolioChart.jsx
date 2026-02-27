import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useTheme } from '../context/ThemeContext';

export default function PortfolioChart({ portfolio = {} }) {
  const { theme } = useTheme();
  const slices = [
    { name: 'Equity', value: portfolio.equity_pct || 0, color: '#3b82f6' },
    { name: 'Bonds',  value: portfolio.bonds_pct || 0,  color: '#8b5cf6' },
    { name: 'Cash',   value: portfolio.cash_pct || 0,   color: '#64748b' },
  ].filter((s) => s.value > 0);

  const total = portfolio.total_value || 0;

  return (
    <div className="card p-5">
      <span className="text-[11px] font-medium text-[var(--c-dim)] uppercase tracking-wide">
        Allocation
      </span>

      <div className="flex items-center gap-5 mt-3">
        {/* Donut */}
        <div className="w-[120px] h-[120px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={slices}
                cx="50%"
                cy="50%"
                innerRadius={38}
                outerRadius={55}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {slices.map((s, i) => (
                  <Cell key={i} fill={s.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: theme === 'light' ? '#ffffff' : '#0d1320',
                  border: `1px solid ${theme === 'light' ? '#e2e8f0' : '#151d2e'}`,
                  borderRadius: 6,
                  color: theme === 'light' ? '#0f172a' : '#c8d1dc',
                  fontSize: 12,
                  padding: '6px 10px',
                }}
                formatter={(v) => [`${v.toFixed(1)}%`]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2.5">
          <div className="mono text-xl font-bold text-[var(--c-text)] leading-none mb-3">
            ${total.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </div>
          {slices.map((s) => (
            <div key={s.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-sm" style={{ background: s.color }} />
                <span className="text-[12px] text-[#64748b]">{s.name}</span>
              </div>
              <span className="mono text-[12px] text-[#94a3b8] font-medium">
                {s.value.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
