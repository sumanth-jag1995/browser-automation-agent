import type { ExecutionResult } from '../../types';
import { Badge } from './badge';

interface FlowTableProps {
  results: ExecutionResult[];
}

export function FlowTable({ results }: FlowTableProps) {
  if (!results.length) {
    return (
      <p className="text-muted text-sm text-center py-4 border border-dashed border-border rounded-lg">
        No flow results yet.
      </p>
    );
  }

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr>
          {['Flow', 'Status', 'Home Page', 'Error'].map(h => (
            <th key={h} className="text-left text-xs text-muted uppercase tracking-wide py-2 px-2 border-b border-border">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {results.map((r, i) => (
          <tr key={i} className="border-b border-border last:border-0">
            <td className="py-2.5 px-2 font-semibold text-text">{r.flow ?? '—'}</td>
            <td className="py-2.5 px-2"><Badge status={r.status} /></td>
            <td className="py-2.5 px-2 text-muted text-xs">{r.home_page_verified ? '✓ Verified' : '—'}</td>
            <td className="py-2.5 px-2 text-fail text-xs">{r.error ?? ''}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
