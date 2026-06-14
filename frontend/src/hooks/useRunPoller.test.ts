import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useRunPoller } from './useRunPoller';

vi.useFakeTimers();

function mockStatus(progress: number, status = 'running') {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ status, progress }),
  } as Response);
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => vi.restoreAllMocks());

describe('useRunPoller', () => {
  it('emits "Run started" immediately when runId is set', () => {
    mockStatus(0);
    const { result } = renderHook(() => useRunPoller('run-1'));
    expect(result.current.logs[0]?.message).toBe('Run started');
  });

  it('emits log line when progress crosses 20%', async () => {
    mockStatus(25);
    const { result } = renderHook(() => useRunPoller('run-1'));
    await act(async () => {
      vi.advanceTimersByTime(2100);
      await Promise.resolve();
    });
    const messages = result.current.logs.map(l => l.message);
    expect(messages).toContain('Discovering user flows…');
  });

  it('sets done=true when progress reaches 100', async () => {
    mockStatus(100, 'success');
    const { result } = renderHook(() => useRunPoller('run-1'));
    await act(async () => {
      vi.advanceTimersByTime(2100);
      await Promise.resolve();
    });
    expect(result.current.done).toBe(true);
    const messages = result.current.logs.map(l => l.message);
    expect(messages.some(m => m.includes('Complete'))).toBe(true);
  });

  it('returns empty logs when runId is null', () => {
    const { result } = renderHook(() => useRunPoller(null));
    expect(result.current.logs).toHaveLength(0);
    expect(result.current.done).toBe(false);
  });
});
