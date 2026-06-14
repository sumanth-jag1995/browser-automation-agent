import type { RunRequest, RunResponse, StatusResponse, Report, RunSummary } from '../types';

declare const __VITE_API_BASE__: string;

/**
 * API base URL. Supports (in order of precedence):
 * 1. Vite build-time define: __VITE_API_BASE__ (from VITE_API_BASE env)
 * 2. Runtime window injection: window.ENV?.API_BASE
 * 3. Default: relative path (same origin, works with dev proxy)
 */
function getApiBase(): string {
  // Try build-time Vite define first
  if (typeof __VITE_API_BASE__ !== 'undefined') {
    const base = (__VITE_API_BASE__ as string)?.trim?.() || '';
    if (base && base !== '' && !base.startsWith('${')) {
      console.debug('[API] Using build-time VITE_API_BASE:', base);
      return base;
    }
  }

  // Try Vite env var (fallback if define didn't work)
  const viteBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim?.() || '';
  if (viteBase && viteBase !== '' && !viteBase.startsWith('${')) {
    console.debug('[API] Using import.meta.env.VITE_API_BASE:', viteBase);
    return viteBase;
  }
  
  // Try runtime window var (runtime injection)
  if (typeof window !== 'undefined') {
    const runtimeBase = (window as any).ENV?.API_BASE?.trim?.() || '';
    if (runtimeBase && runtimeBase !== '') {
      console.debug('[API] Using runtime window.ENV.API_BASE:', runtimeBase);
      return runtimeBase;
    }
  }
  
  // Default: same origin (relative path)
  console.debug('[API] Using relative path (same origin)');
  return '';
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBase();
  const url = base ? `${base.replace(/\/$/, '')}${path}` : path;
  console.debug('[API]', init?.method || 'GET', url);
  
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  startRun: (req: RunRequest): Promise<RunResponse> =>
    json('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),

  getStatus: (runId: string): Promise<StatusResponse> =>
    json(`/status/${runId}`),

  getReport: (runId: string): Promise<Report> =>
    json(`/report/${runId}`),

  listRuns: (limit = 50): Promise<RunSummary[]> =>
    json(`/api/runs?limit=${limit}`),
};
