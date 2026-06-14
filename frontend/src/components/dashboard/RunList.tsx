import type { RunSummary } from '../../types';
import { Badge } from './badge';

function formatTime(iso?: string) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

interface RunListProps {
  runs: RunSummary[];
  activeRunId?: string;
  onSelect: (runId: string) => void;
}

export function RunList({ runs, activeRunId, onSelect }: RunListProps) {
  if (!runs.length) {
    return <p className="text-muted text-sm text-center p-4 border border-dashed border-border rounded-lg">No runs yet.</p>;
  }

  return (
    <div className="space-y-2">
      {runs.map(r => (
        <button
          key={r.run_id}
          onClick={() => onSelect(r.run_id)}
          className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors ${
            r.run_id === activeRunId
              ? 'border-accent bg-surface2'
              : 'border-border bg-bg hover:border-accent hover:bg-surface2'
          }`}
        >
          <p className="font-semibold text-sm text-text truncate">{r.intent || 'Untitled run'}</p>
          <div className="flex items-center gap-2 mt-1">
            <Badge status={r.status} />
            <span className="text-xs text-muted">{r.flows_passed}/{r.flows_total} flows</span>
          </div>
          <p className="text-xs text-muted mt-0.5">{formatTime(r.generated_at)}</p>
        </button>
      ))}
    </div>
  );
}
