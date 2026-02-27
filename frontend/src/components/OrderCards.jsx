import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

export default function OrderCards({ orders = [] }) {
  if (!orders.length) {
    return (
      <div className="card p-5">
        <span className="text-[11px] font-medium text-[var(--c-dim)] uppercase tracking-wide">
          Orders
        </span>
        <p className="text-[13px] text-[var(--c-dimmer)] mt-3">No recommendations.</p>
      </div>
    );
  }

  const icon = (a) => {
    if (a === 'BUY')  return <ArrowUpRight  className="w-3.5 h-3.5" />;
    if (a === 'SELL') return <ArrowDownRight className="w-3.5 h-3.5" />;
    return <Minus className="w-3.5 h-3.5" />;
  };

  return (
    <div className="card p-5">
      <span className="text-[11px] font-medium text-[#4b5563] uppercase tracking-wide">
        Orders
      </span>

      <div className="mt-3 divide-y divide-[#151d2e]">
        {orders.map((o, i) => {
          const action = (o.action || 'HOLD').toUpperCase();
          const cls =
            action === 'BUY'  ? 'pill-buy' :
            action === 'SELL' ? 'pill-sell' : 'pill-hold';
          return (
            <div key={i} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
              <span className={`pill mt-0.5 ${cls}`}>
                {icon(action)}
                {action}
              </span>
              <div className="flex-1 min-w-0">
                <span className="text-[13px] font-semibold text-[var(--c-text)]">{o.asset}</span>
                <p className="text-[11px] text-[var(--c-dim)] leading-relaxed mt-0.5 line-clamp-2">
                  {o.reason}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
