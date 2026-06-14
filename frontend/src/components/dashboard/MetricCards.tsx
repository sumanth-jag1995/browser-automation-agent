import type { Report } from '../../types';

interface MetricCardsProps {
  report: Report;
}

export function MetricCards({ report }: MetricCardsProps) {
  const cards = [
    { label: 'Flows Passed', value: `${report.flows_passed ?? 0}/${report.flows_total ?? 0}` },
    { label: 'Auto Repairs', value: String(report.auto_repairs ?? 0) },
    { label: 'Retries', value: String(report.retries_used ?? 0) },
    { label: 'Regressions', value: String(report.regressions ?? 0) },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
      {cards.map(c => (
        <div key={c.label} className="bg-surface border border-border rounded-lg p-4">
          <p className="text-xs text-muted uppercase tracking-wide mb-1">{c.label}</p>
          <p className="text-2xl font-bold text-text">{c.value}</p>
        </div>
      ))}
    </div>
  );
}
