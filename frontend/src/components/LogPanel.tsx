import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import type { LogEntry } from '../types';

interface LogPanelProps {
  runId: string;
  logs: LogEntry[];
  done: boolean;
}

export function LogPanel({ runId, logs, done }: LogPanelProps) {
  const navigate = useNavigate();

  return (
    <div className="w-full max-w-2xl mx-auto mt-6">
      <div className="rounded-lg border border-border bg-surface overflow-hidden">
        <div className="px-4 py-2 border-b border-border flex items-center justify-between">
          <span className="text-xs text-muted uppercase tracking-wide">Execution Log</span>
          <code className="text-xs text-muted">Run ID: {runId}</code>
        </div>
        <div className="px-4 py-3 font-mono text-sm space-y-1 max-h-64 overflow-y-auto">
          {logs.map((entry, i) => (
            <div key={i} className="text-text leading-relaxed">
              <span className="text-muted">[{entry.timestamp}]</span>{' '}
              {entry.message}
            </div>
          ))}
        </div>
        {done && (
          <div className="px-4 py-3 border-t border-border flex justify-center">
            <button
              onClick={() => navigate(`/dashboard/${runId}`)}
              className="flex items-center gap-2 px-5 py-2 bg-accent hover:bg-accent/90 text-white text-sm font-medium rounded-lg transition-colors"
            >
              View Dashboard <ArrowRight size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
