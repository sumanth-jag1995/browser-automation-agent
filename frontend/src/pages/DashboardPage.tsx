import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { api } from '../api/client';
import { RunList } from '../components/dashboard/RunList';
import { MetricCards } from '../components/dashboard/MetricCards';
import { FlowTable } from '../components/dashboard/FlowTable';
import { ScreenshotGrid } from '../components/dashboard/ScreenshotGrid';
import { Badge } from '../components/dashboard/badge';
import type { Report, RunSummary, StatusResponse } from '../types';

function formatTime(iso?: string) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

export function DashboardPage() {
  const { runId } = useParams<{ runId?: string }>();
  const navigate = useNavigate();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    api.listRuns().then(setRuns).catch(() => setRuns([]));
  }, []);

  useEffect(() => {
    if (!runId && runs.length) {
      navigate(`/dashboard/${runs[0].run_id}`, { replace: true });
    }
  }, [runId, runs, navigate]);

  useEffect(() => {
    if (!runId) return;
    if (pollRef.current) clearInterval(pollRef.current);
    setReport(null);
    setError(null);

    async function load() {
      try {
        const [r, s] = await Promise.all([
          api.getReport(runId!),
          api.getStatus(runId!),
        ]);
        setReport(r);
        setStatus(s);
        if (s.progress < 100) {
          pollRef.current = setInterval(load, 2000);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report');
      }
    }

    load();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [runId]);

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col">
      <header className="px-6 py-4 border-b border-border bg-surface flex items-center gap-3">
        <Link to="/" className="text-muted hover:text-text flex items-center gap-1 text-sm">
          <ChevronLeft size={18} /> Back
        </Link>
        <h1 className="font-semibold text-base">Browser Automation AI Agent — Dashboard</h1>
      </header>

      <div className="flex flex-1 overflow-hidden" style={{ minHeight: 'calc(100vh - 57px)' }}>
        <aside className="w-72 shrink-0 border-r border-border bg-surface p-4 overflow-y-auto">
          <p className="text-xs text-muted uppercase tracking-wide mb-3">Recent Runs</p>
          <RunList
            runs={runs}
            activeRunId={runId}
            onSelect={id => navigate(`/dashboard/${id}`)}
          />
        </aside>

        <main className="flex-1 p-6 overflow-y-auto">
          {error && <p className="text-fail text-sm">{error}</p>}
          {!report && !error && <p className="text-muted text-sm">Loading…</p>}
          {report && (
            <>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-bold">{report.intent || 'Test run'}</h2>
                {report.status && <Badge status={report.status} />}
              </div>
              <p className="text-muted text-sm mb-1">
                Target:{' '}
                <a href={report.url} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                  {report.url}
                </a>
              </p>
              <p className="text-muted text-sm mb-4">
                Run ID: <code className="text-text text-xs">{report.run_id}</code>
                {report.generated_at && ` · ${formatTime(report.generated_at)}`}
              </p>

              {status && status.progress < 100 && (
                <div className="bg-surface border border-border rounded-lg p-4 mb-5">
                  <p className="text-sm text-accent">Run in progress… ({status.progress}%)</p>
                </div>
              )}

              <MetricCards report={report} />

              <div className="bg-surface border border-border rounded-lg p-5 mb-5">
                <h3 className="font-semibold text-base mb-4">Flow Execution</h3>
                <FlowTable results={report.execution_results ?? []} />
              </div>

              <div className="bg-surface border border-border rounded-lg p-5 mb-5">
                <h3 className="font-semibold text-base mb-4">Screenshots</h3>
                <ScreenshotGrid screenshots={report.screenshots ?? []} />
              </div>

              <p className="text-xs text-muted">
                Raw JSON:{' '}
                <a href={`/report/${report.run_id}`} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                  /report/{report.run_id}
                </a>
              </p>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
