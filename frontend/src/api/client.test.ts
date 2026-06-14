import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from './client';

function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok,
    status,
    statusText: ok ? 'OK' : 'Internal Server Error',
    json: () => Promise.resolve(body),
  } as Response);
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => vi.restoreAllMocks());

describe('api.startRun', () => {
  it('POSTs to /run with JSON body and returns RunResponse', async () => {
    const spy = mockFetch({ run_id: 'abc', status: 'running', dashboard_url: '/dashboard/abc' });
    const result = await api.startRun({ url: 'https://ex.com', intent: 'test login' });
    expect(spy).toHaveBeenCalledWith('/run', expect.objectContaining({ method: 'POST' }));
    expect(result.run_id).toBe('abc');
  });

  it('throws when response is not ok', async () => {
    mockFetch({}, false, 422);
    await expect(api.startRun({ url: 'x', intent: 'y' })).rejects.toThrow('422');
  });
});

describe('api.getStatus', () => {
  it('GETs /status/{runId}', async () => {
    const spy = mockFetch({ status: 'running', progress: 40 });
    const result = await api.getStatus('abc');
    expect(spy).toHaveBeenCalledWith('/status/abc', undefined);
    expect(result.progress).toBe(40);
  });
});

describe('api.listRuns', () => {
  it('GETs /api/runs with default limit', async () => {
    const spy = mockFetch([]);
    await api.listRuns();
    expect(spy).toHaveBeenCalledWith('/api/runs?limit=50', undefined);
  });
});
