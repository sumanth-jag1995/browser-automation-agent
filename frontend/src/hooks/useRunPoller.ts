import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api/client';
import type { LogEntry, StatusResponse } from '../types';

const LOG_STEPS: Array<{ threshold: number; message: string }> = [
  { threshold: 10, message: 'Initializing pipeline…' },
  { threshold: 20, message: 'Discovering user flows…' },
  { threshold: 40, message: 'Generating Playwright scripts…' },
  { threshold: 60, message: 'Executing automation scripts…' },
  { threshold: 75, message: 'Diagnosing errors / repairing scripts…' },
  { threshold: 85, message: 'Running regression checks…' },
  { threshold: 95, message: 'Generating report…' },
];

function timestamp(): string {
  return new Date().toLocaleTimeString('en-GB', { hour12: false });
}

interface UseRunPollerResult {
  logs: LogEntry[];
  status: StatusResponse | null;
  done: boolean;
}

export function useRunPoller(runId: string | null): UseRunPollerResult {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [done, setDone] = useState(false);
  const emitted = useRef<Set<number>>(new Set());

  const appendLog = useCallback((message: string) => {
    setLogs(prev => [...prev, { timestamp: timestamp(), message }]);
  }, []);

  useEffect(() => {
    if (!runId) return;
    setLogs([{ timestamp: timestamp(), message: 'Run started' }]);
    setStatus(null);
    setDone(false);
    emitted.current = new Set([0]);

    const interval = setInterval(async () => {
      try {
        const s = await api.getStatus(runId);
        setStatus(s);

        for (const step of LOG_STEPS) {
          if (s.progress >= step.threshold && !emitted.current.has(step.threshold)) {
            appendLog(step.message);
            emitted.current.add(step.threshold);
          }
        }

        if (s.progress >= 100) {
          clearInterval(interval);
          const finalMsg =
            s.status === 'success'
              ? `✓ Complete — status: ${s.status}`
              : `✗ Run ended — status: ${s.status}`;
          appendLog(finalMsg);
          setDone(true);
        }
      } catch {
        // silently retry on transient network errors
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [runId, appendLog]);

  return { logs, status, done };
}
