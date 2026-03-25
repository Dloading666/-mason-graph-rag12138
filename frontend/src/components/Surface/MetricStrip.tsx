import type { ReactNode } from 'react';

interface MetricItem {
  label: string;
  value: ReactNode;
  detail: string;
  tone?: 'neutral' | 'teal' | 'amber' | 'danger';
}

interface MetricStripProps {
  items: MetricItem[];
  className?: string;
}

export default function MetricStrip({ items, className }: MetricStripProps) {
  return (
    <section className={['metric-strip', className].filter(Boolean).join(' ')}>
      {items.map((item) => (
        <div key={item.label} className={`metric-cell metric-cell-${item.tone ?? 'neutral'}`}>
          <div className="metric-label">{item.label}</div>
          <div className="metric-value">{item.value}</div>
          <div className="metric-detail">{item.detail}</div>
        </div>
      ))}
    </section>
  );
}
