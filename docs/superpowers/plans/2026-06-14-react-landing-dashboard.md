# React Landing Page & Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Vite + React + TypeScript frontend (landing page + dashboard) to the existing FastAPI project, plus minimal backend changes to support per-request settings overrides, deployable as a single Vercel package.

**Architecture:** A `frontend/` directory holds the entire React SPA (Vite build). FastAPI serves the built assets via a static mount and SPA catch-all route. All API calls from the React app are relative (same origin), so no CORS setup is needed. A thin `api/index.py` adapter exposes the FastAPI `app` to Vercel's Python runtime.

**Tech Stack:** Vite 5, React 18, TypeScript, React Router v6, Tailwind CSS v3, lucide-react, Vitest + @testing-library/react, FastAPI (existing)

---

## File Map

### New Files — Frontend

| File | Responsibility |
|------|---------------|
| `frontend/package.json` | Node deps + build/dev/test scripts |
| `frontend/index.html` | Vite entry HTML |
| `frontend/vite.config.ts` | Vite + dev proxy to :8000 + Vitest config |
| `frontend/tailwind.config.ts` | Custom color palette matching existing dashboard |
| `frontend/postcss.config.js` | Tailwind + autoprefixer PostCSS plugins |
| `frontend/tsconfig.json` | TypeScript compiler config |
| `frontend/src/index.css` | Tailwind directives |
| `frontend/src/test-setup.ts` | @testing-library/jest-dom matchers |
| `frontend/src/types/index.ts` | All shared TypeScript types |
| `frontend/src/api/client.ts` | Typed fetch wrappers for all backend endpoints |
| `frontend/src/hooks/useSettings.ts` | Session-only settings React context + hook |
| `frontend/src/hooks/useRunPoller.ts` | Polls /status/{runId}, emits simulated log lines |
| `frontend/src/components/HamburgerMenu.tsx` | Left-side settings drawer |
| `frontend/src/components/RunForm.tsx` | Prompt textarea + URL input + submit button |
| `frontend/src/components/LogPanel.tsx` | Log output, run_id display, View Dashboard button |
| `frontend/src/components/dashboard/RunList.tsx` | Sidebar list of recent runs |
| `frontend/src/components/dashboard/MetricCards.tsx` | Metric cards grid |
| `frontend/src/components/dashboard/FlowTable.tsx` | Flow execution results table |
| `frontend/src/components/dashboard/ScreenshotGrid.tsx` | Screenshot gallery |
| `frontend/src/pages/LandingPage.tsx` | Landing page (header + form + log panel) |
| `frontend/src/pages/DashboardPage.tsx` | Dashboard page (sidebar + report view) |
| `frontend/src/App.tsx` | React Router routes + SettingsProvider wrapper |
| `frontend/src/main.tsx` | React DOM entry point |

### New Files — Deployment

| File | Responsibility |
|------|---------------|
| `api/index.py` | Thin adapter: imports FastAPI `app` for Vercel's Python runtime |
| `vercel.json` | Build config + route rewrites for single Vercel deployment |

### Modified Files — Backend

| File | Change |
|------|--------|
| `state/schema.py` | Add `settings_override: Optional[dict[str, Any]]` to `AgentState` |
| `llm/client.py` | Accept `override: dict \| None` in `__init__`; expose `llm_enabled` attribute; use effective values in OpenRouter calls |
| `agents/flow_discovery.py` | Pass `state.get("settings_override")` to `LLMClient`; use `client.llm_enabled` |
| `agents/error_diagnosis.py` | Same as above |
| `agents/adaptive_repair.py` | Same as above |
| `agents/script_generator.py` | Thread `settings_override` through `generate_scripts` → `_resolve_scripts_for_flows` → `build_script` → `_generate_script_with_llm`; use `client.llm_enabled` |
| `orchestrator/graph.py` | `run_pipeline` accepts `settings_override`; `_route_after_execute` reads retry/repair limits from state override first |
| `main.py` | Extend `RunRequest`; remove `/dashboard` routes; mount `frontend/dist`; add SPA catch-all |

---

## Task 1: Frontend project scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/index.css`
- Create: `frontend/src/test-setup.ts`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "browser-automation-agent-ui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "lucide-react": "^0.462.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.1",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.2",
    "vite": "^5.4.10",
    "vitest": "^2.1.4"
  }
}
```

- [ ] **Step 2: Create `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/run': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/report': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/screenshots': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
});
```

- [ ] **Step 3: Create `frontend/tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0f1419',
        surface: '#1a2332',
        surface2: '#243044',
        border: '#2d3a4f',
        text: '#e8edf4',
        muted: '#8b9cb3',
        accent: '#3b82f6',
        success: '#22c55e',
        fail: '#ef4444',
        warn: '#f59e0b',
      },
    },
  },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 4: Create `frontend/postcss.config.js`**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 5: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src", "vite.config.ts", "tailwind.config.ts"]
}
```

- [ ] **Step 6: Create `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Browser Automation AI Agent</title>
  </head>
  <body class="bg-bg text-text">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Create `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 8: Create `frontend/src/test-setup.ts`**

```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 9: Install dependencies**

From the `frontend/` directory:

```bash
cd frontend && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 10: Verify Vite starts (needs a placeholder main.tsx)**

Create `frontend/src/main.tsx` with just:

```tsx
export {};
```

Then run:

```bash
cd frontend && npm run build
```

Expected: build succeeds and `frontend/dist/` is created. (It will have minimal output since main.tsx is empty.)

- [ ] **Step 11: Commit scaffolding**

```bash
git add frontend/
git commit -m "feat: scaffold Vite + React + Tailwind frontend"
```

---

## Task 2: Types and API client

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Create `frontend/src/types/index.ts`**

```typescript
export interface Settings {
  openrouterApiKey: string;
  openrouterModel: string;
  useMockLlm: boolean;
  maxRetries: number;
  maxRepairBeforeRegenerate: number;
}

export const DEFAULT_SETTINGS: Settings = {
  openrouterApiKey: '',
  openrouterModel: 'anthropic/claude-haiku-4-5',
  useMockLlm: false,
  maxRetries: 3,
  maxRepairBeforeRegenerate: 2,
};

export interface RunRequest {
  url: string;
  intent: string;
  openrouter_api_key?: string;
  openrouter_model?: string;
  use_mock_llm?: boolean;
  max_retries?: number;
  max_repair_before_regenerate?: number;
}

export interface RunResponse {
  run_id: string;
  status: string;
  dashboard_url: string;
}

export interface StatusResponse {
  status: string;
  progress: number;
}

export interface ExecutionResult {
  flow: string;
  status: string;
  home_page_verified?: boolean;
  error?: string;
}

export interface Report {
  run_id: string;
  url: string;
  intent: string;
  status: string;
  flows_total?: number;
  flows_passed?: number;
  auto_repairs?: number;
  retries_used?: number;
  regressions?: number;
  execution_results?: ExecutionResult[];
  screenshots?: string[];
  generated_at?: string;
  dashboard_url?: string;
  human_escalation?: boolean;
}

export interface RunSummary {
  run_id: string;
  intent: string;
  status: string;
  flows_total: number;
  flows_passed: number;
  generated_at: string;
}

export interface LogEntry {
  timestamp: string;
  message: string;
}
```

- [ ] **Step 2: Create `frontend/src/api/client.ts`**

```typescript
import type { RunRequest, RunResponse, StatusResponse, Report, RunSummary } from '../types';

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
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
```

- [ ] **Step 3: Write failing tests for `client.ts`**

Create `frontend/src/api/client.test.ts`:

```typescript
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
```

- [ ] **Step 4: Run tests — expect PASS (client is already written)**

```bash
cd frontend && npm test -- --reporter=verbose src/api/client.test.ts
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/ frontend/src/api/
git commit -m "feat: add TypeScript types and typed API client"
```

---

## Task 3: Settings context hook

**Files:**
- Create: `frontend/src/hooks/useSettings.ts`

- [ ] **Step 1: Create `frontend/src/hooks/useSettings.ts`**

```typescript
import { createContext, useContext, useState, type ReactNode } from 'react';
import { DEFAULT_SETTINGS, type Settings } from '../types';

interface SettingsContextValue {
  settings: Settings;
  updateSettings: (patch: Partial<Settings>) => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const updateSettings = (patch: Partial<Settings>) =>
    setSettings(prev => ({ ...prev, ...patch }));
  return (
    <SettingsContext.Provider value={{ settings, updateSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used inside SettingsProvider');
  return ctx;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useSettings.ts
git commit -m "feat: add session-only settings context"
```

---

## Task 4: Run poller hook

**Files:**
- Create: `frontend/src/hooks/useRunPoller.ts`
- Create: `frontend/src/hooks/useRunPoller.test.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/hooks/useRunPoller.test.ts`:

```typescript
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
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd frontend && npm test -- src/hooks/useRunPoller.test.ts
```

Expected: FAIL — `useRunPoller` not found.

- [ ] **Step 3: Create `frontend/src/hooks/useRunPoller.ts`**

```typescript
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd frontend && npm test -- src/hooks/useRunPoller.test.ts
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add useRunPoller hook with simulated log lines"
```

---

## Task 5: HamburgerMenu component

**Files:**
- Create: `frontend/src/components/HamburgerMenu.tsx`

- [ ] **Step 1: Create `frontend/src/components/HamburgerMenu.tsx`**

```tsx
import { X, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { useSettings } from '../hooks/useSettings';

const MODELS = [
  { value: 'anthropic/claude-haiku-4-5', label: 'Claude Haiku 4.5' },
  { value: 'anthropic/claude-sonnet-4', label: 'Claude Sonnet 4' },
];

interface HamburgerMenuProps {
  open: boolean;
  onClose: () => void;
}

export function HamburgerMenu({ open, onClose }: HamburgerMenuProps) {
  const { settings, updateSettings } = useSettings();
  const [showKey, setShowKey] = useState(false);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <aside className="fixed top-0 left-0 h-full w-72 bg-surface border-r border-border z-50 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-text font-semibold text-lg">Settings</h2>
          <button onClick={onClose} className="text-muted hover:text-text" aria-label="Close settings">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-5">
          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              OpenRouter API Key
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={settings.openrouterApiKey}
                onChange={e => updateSettings({ openrouterApiKey: e.target.value })}
                placeholder="sk-or-v1-…"
                className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm pr-9 focus:outline-none focus:border-accent"
              />
              <button
                type="button"
                onClick={() => setShowKey(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-text"
                aria-label={showKey ? 'Hide key' : 'Show key'}
              >
                {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              Model
            </label>
            <select
              value={settings.openrouterModel}
              onChange={e => updateSettings({ openrouterModel: e.target.value })}
              className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm focus:outline-none focus:border-accent"
            >
              {MODELS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-xs text-muted uppercase tracking-wide">Use Mock LLM</label>
            <button
              type="button"
              role="switch"
              aria-checked={settings.useMockLlm}
              onClick={() => updateSettings({ useMockLlm: !settings.useMockLlm })}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                settings.useMockLlm ? 'bg-accent' : 'bg-border'
              }`}
            >
              <span
                className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  settings.useMockLlm ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              Max Retries
            </label>
            <input
              type="number"
              min={0}
              max={10}
              value={settings.maxRetries}
              onChange={e => updateSettings({ maxRetries: Number(e.target.value) })}
              className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="block text-xs text-muted uppercase tracking-wide mb-1">
              Max Repairs Before Regenerate
            </label>
            <input
              type="number"
              min={0}
              max={10}
              value={settings.maxRepairBeforeRegenerate}
              onChange={e => updateSettings({ maxRepairBeforeRegenerate: Number(e.target.value) })}
              className="w-full bg-bg border border-border rounded px-3 py-2 text-text text-sm focus:outline-none focus:border-accent"
            />
          </div>
        </div>
      </aside>
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/HamburgerMenu.tsx
git commit -m "feat: add HamburgerMenu settings drawer"
```

---

## Task 6: RunForm component

**Files:**
- Create: `frontend/src/components/RunForm.tsx`

- [ ] **Step 1: Create `frontend/src/components/RunForm.tsx`**

```tsx
import { useState, type FormEvent } from 'react';
import { Play } from 'lucide-react';
import { api } from '../api/client';
import { useSettings } from '../hooks/useSettings';

interface RunFormProps {
  onRunStarted: (runId: string) => void;
}

export function RunForm({ onRunStarted }: RunFormProps) {
  const { settings } = useSettings();
  const [intent, setIntent] = useState('');
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.startRun({
        url,
        intent,
        openrouter_api_key: settings.openrouterApiKey || undefined,
        openrouter_model: settings.openrouterModel,
        use_mock_llm: settings.useMockLlm,
        max_retries: settings.maxRetries,
        max_repair_before_regenerate: settings.maxRepairBeforeRegenerate,
      });
      onRunStarted(res.run_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start run');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="rounded-lg border border-border overflow-hidden">
        <textarea
          value={intent}
          onChange={e => setIntent(e.target.value)}
          placeholder="Describe what you want to test…"
          rows={4}
          required
          className="w-full bg-surface px-4 py-3 text-text placeholder:text-muted text-sm resize-none focus:outline-none border-b border-border"
        />
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://example.com"
          required
          className="w-full bg-surface px-4 py-3 text-text placeholder:text-muted text-sm focus:outline-none"
        />
      </div>
      {error && <p className="mt-2 text-fail text-sm">{error}</p>}
      <div className="mt-4 flex justify-center">
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent/90 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
        >
          <Play size={16} />
          {loading ? 'Starting…' : 'Run Automation'}
        </button>
      </div>
    </form>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/RunForm.tsx
git commit -m "feat: add RunForm component"
```

---

## Task 7: LogPanel component

**Files:**
- Create: `frontend/src/components/LogPanel.tsx`

- [ ] **Step 1: Create `frontend/src/components/LogPanel.tsx`**

```tsx
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/LogPanel.tsx
git commit -m "feat: add LogPanel component"
```

---

## Task 8: Dashboard sub-components

**Files:**
- Create: `frontend/src/components/dashboard/RunList.tsx`
- Create: `frontend/src/components/dashboard/MetricCards.tsx`
- Create: `frontend/src/components/dashboard/FlowTable.tsx`
- Create: `frontend/src/components/dashboard/ScreenshotGrid.tsx`

- [ ] **Step 1: Create a shared `badge` helper — add to `frontend/src/components/dashboard/badge.tsx`**

```tsx
const STATUS_CLASSES: Record<string, string> = {
  success: 'bg-success/20 text-success',
  failed: 'bg-fail/20 text-fail',
  fail: 'bg-fail/20 text-fail',
  escalated: 'bg-warn/20 text-warn',
  regression: 'bg-warn/20 text-warn',
  running: 'bg-accent/20 text-accent',
};

export function Badge({ status }: { status: string }) {
  const cls = STATUS_CLASSES[status?.toLowerCase()] ?? 'bg-border/40 text-muted';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${cls}`}>
      {status ?? 'unknown'}
    </span>
  );
}
```

- [ ] **Step 2: Create `frontend/src/components/dashboard/RunList.tsx`**

```tsx
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
```

- [ ] **Step 3: Create `frontend/src/components/dashboard/MetricCards.tsx`**

```tsx
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
```

- [ ] **Step 4: Create `frontend/src/components/dashboard/FlowTable.tsx`**

```tsx
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
```

- [ ] **Step 5: Create `frontend/src/components/dashboard/ScreenshotGrid.tsx`**

```tsx
function screenshotUrl(path: string): string {
  const normalized = path.replace(/^\/+/, '');
  return '/' + normalized.split('/').map(encodeURIComponent).join('/');
}

interface ScreenshotGridProps {
  screenshots: string[];
}

export function ScreenshotGrid({ screenshots }: ScreenshotGridProps) {
  if (!screenshots.length) {
    return (
      <p className="text-muted text-sm text-center py-4 border border-dashed border-border rounded-lg">
        No screenshots captured.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {screenshots.map((s, i) => (
        <figure key={i} className="border border-border rounded-lg overflow-hidden bg-bg">
          <a href={screenshotUrl(s)} target="_blank" rel="noopener noreferrer">
            <img src={screenshotUrl(s)} alt={s} loading="lazy" className="w-full block bg-black" />
          </a>
          <figcaption className="px-3 py-2 text-xs text-muted truncate">{s}</figcaption>
        </figure>
      ))}
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/dashboard/
git commit -m "feat: add dashboard sub-components (RunList, MetricCards, FlowTable, ScreenshotGrid)"
```

---

## Task 9: App.tsx, main.tsx, index.css wiring

**Files:**
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SettingsProvider } from './hooks/useSettings';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';

export function App() {
  return (
    <SettingsProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/:runId" element={<DashboardPage />} />
        </Routes>
      </BrowserRouter>
    </SettingsProvider>
  );
}
```

- [ ] **Step 2: Replace `frontend/src/main.tsx` (full content)**

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { App } from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: wire up React Router and SettingsProvider in App"
```

---

## Task 10: LandingPage

**Files:**
- Create: `frontend/src/pages/LandingPage.tsx`

- [ ] **Step 1: Create `frontend/src/pages/LandingPage.tsx`**

```tsx
import { useState } from 'react';
import { Menu } from 'lucide-react';
import { HamburgerMenu } from '../components/HamburgerMenu';
import { RunForm } from '../components/RunForm';
import { LogPanel } from '../components/LogPanel';
import { useRunPoller } from '../hooks/useRunPoller';

export function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const { logs, done } = useRunPoller(activeRunId);

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col">
      <header className="px-6 py-4 border-b border-border bg-surface flex items-center gap-4">
        <button
          onClick={() => setMenuOpen(true)}
          className="text-muted hover:text-text"
          aria-label="Open settings"
        >
          <Menu size={22} />
        </button>
        <h1 className="font-semibold text-base">Browser Automation AI Agent</h1>
      </header>

      <HamburgerMenu open={menuOpen} onClose={() => setMenuOpen(false)} />

      <main className="flex-1 flex flex-col items-center justify-start px-4 pt-16 pb-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-text mb-2">Browser Automation AI Agent</h2>
          <p className="text-muted">Describe a flow. We'll automate and test it.</p>
        </div>

        <RunForm onRunStarted={setActiveRunId} />

        {activeRunId && (
          <LogPanel runId={activeRunId} logs={logs} done={done} />
        )}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/LandingPage.tsx
git commit -m "feat: add LandingPage"
```

---

## Task 11: DashboardPage

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Create `frontend/src/pages/DashboardPage.tsx`**

```tsx
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
```

- [ ] **Step 2: Build and verify no TypeScript errors**

```bash
cd frontend && npm run typecheck
```

Expected: no errors.

```bash
cd frontend && npm run build
```

Expected: `frontend/dist/` created with `index.html`, `assets/` folder containing JS and CSS bundles.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add DashboardPage — React port of existing dashboard HTML"
```

---

## Task 12: Backend — AgentState schema

**Files:**
- Modify: `state/schema.py`

- [ ] **Step 1: Add `settings_override` field to `AgentState`**

In `state/schema.py`, add the import for `Any` (already present) and the new field. The complete updated file:

```python
"""Agent state schema for LangGraph orchestration."""

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between agents in the orchestration graph."""

    url: str
    intent: str
    discovered_flows: list[str]
    generated_scripts: list[str]
    execution_results: list[dict[str, Any]]
    diagnosis: Optional[dict[str, Any]]
    repaired_script: Optional[str]
    retry_count: int
    screenshots: list[str]
    regression_diff: Optional[dict[str, Any]]
    final_report: Optional[dict[str, Any]]
    status: str
    run_id: str
    current_script_index: int
    auto_repairs: int
    human_escalation: bool
    flow_repair_counts: dict[str, int]
    script_sources: dict[str, str]
    flows_reused: list[str]
    flows_generated: list[str]
    flows_regenerated: list[str]
    settings_override: Optional[dict[str, Any]]
```

- [ ] **Step 2: Commit**

```bash
git add state/schema.py
git commit -m "feat: add settings_override to AgentState"
```

---

## Task 13: Backend — LLMClient override support

**Files:**
- Modify: `llm/client.py`

- [ ] **Step 1: Update `LLMClient.__init__` and `complete` method**

The full updated `llm/client.py`:

```python
"""LLM client (Anthropic or OpenRouter) with deterministic mock fallback for offline/CI runs."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper around Anthropic or OpenRouter APIs with mock responses when no API key is set."""

    def __init__(self, override: dict[str, Any] | None = None) -> None:
        self.settings = get_settings()
        self._override = override or {}
        self._anthropic_client: Any = None

        # Effective values — override takes precedence over env-based settings
        eff_api_key = self._override.get("openrouter_api_key") or self.settings.openrouter_api_key
        eff_model = self._override.get("openrouter_model") or self.settings.openrouter_model
        mock_forced = bool(self._override.get("use_mock_llm", False))

        self._effective_api_key: str = eff_api_key or ""
        self._effective_model: str = eff_model or ""
        # llm_enabled: False if mock is forced OR if the base settings have no key
        self.llm_enabled: bool = (not mock_forced) and self.settings.llm_enabled

        if self.settings.resolved_llm_provider == "anthropic" and self.llm_enabled:
            from anthropic import Anthropic
            self._anthropic_client = Anthropic(api_key=self.settings.anthropic_api_key)

    def complete(self, prompt: str, system: str = "") -> str:
        if not self.llm_enabled:
            logger.info("Using mock LLM response (no API key or mock mode enabled)")
            return self._mock_response(prompt)

        provider = self.settings.resolved_llm_provider
        if provider == "anthropic":
            return self._complete_anthropic(prompt, system)
        if provider == "openrouter":
            return self._complete_openrouter(prompt, system)
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    def _complete_anthropic(self, prompt: str, system: str) -> str:
        assert self._anthropic_client is not None
        message = self._anthropic_client.messages.create(
            model=self.settings.llm_model,
            max_tokens=4096,
            system=system or "You are a browser automation expert. Respond concisely.",
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [block.text for block in message.content if block.type == "text"]
        return "\n".join(text_blocks)

    def _complete_openrouter(self, prompt: str, system: str) -> str:
        url = f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions"
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        else:
            messages.append(
                {
                    "role": "system",
                    "content": "You are a browser automation expert. Respond concisely.",
                }
            )
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {self._effective_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._effective_model,
                "messages": messages,
                "max_tokens": 4096,
            },
            timeout=120.0,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter request failed ({response.status_code}): {response.text}"
            )

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected OpenRouter response: {data}") from exc

    def complete_json(self, prompt: str, system: str = "") -> dict[str, Any]:
        raw = self.complete(prompt, system=system)
        return self._parse_json(raw)

    @staticmethod
    def load_prompt(name: str) -> str:
        path = Path(__file__).resolve().parent.parent / "prompts" / f"{name}.txt"
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        return json.loads(cleaned)

    @staticmethod
    def _mock_response(prompt: str) -> str:
        lower = prompt.lower()
        if "user journeys" in lower or "discover" in lower:
            return json.dumps(
                ["login", "browse_products", "add_to_cart", "checkout", "payment"]
            )
        if "diagnos" in lower or "failure" in lower or "root cause" in lower:
            return json.dumps(
                {
                    "failure_type": "selector",
                    "severity": "critical",
                    "root_cause": "checkout button selector changed",
                    "fix_strategy": "use data-testid locator",
                }
            )
        if "repair" in lower or "fix" in lower:
            return json.dumps(
                {
                    "repaired_script": (
                        'async def run(page, url: str, screenshot_dir: str) -> dict:\n'
                        '    import os\n'
                        '    result = {"status": "success", "screenshots": []}\n'
                        '    try:\n'
                        '        await page.goto(url, wait_until="domcontentloaded", timeout=60000)\n'
                        '        await page.wait_for_load_state("networkidle", timeout=30000)\n'
                        '        os.makedirs(screenshot_dir, exist_ok=True)\n'
                        '        path = os.path.join(screenshot_dir, "repaired_flow.png")\n'
                        '        await page.screenshot(path=path, full_page=True)\n'
                        '        result["screenshots"].append(path)\n'
                        '    except Exception as exc:\n'
                        '        result = {"status": "fail", "error": type(exc).__name__ + ": " + str(exc)}\n'
                        '    return result\n'
                    )
                }
            )
        if "generate a playwright automation script" in lower:
            return json.dumps({"scripts": []})
        if "playwright" in lower or "script" in lower:
            return json.dumps({"scripts": []})
        return json.dumps({"status": "ok"})
```

- [ ] **Step 2: Commit**

```bash
git add llm/client.py
git commit -m "feat: LLMClient accepts per-run override (api_key, model, mock flag)"
```

---

## Task 14: Backend — Agent files

**Files:**
- Modify: `agents/flow_discovery.py` (line 43)
- Modify: `agents/error_diagnosis.py` (line 65)
- Modify: `agents/adaptive_repair.py` (line 87)
- Modify: `agents/script_generator.py` (lines 166–194)

All four agents call `LLMClient()` and check `client.settings.llm_enabled`. Change both to use the override.

- [ ] **Step 1: Update `agents/flow_discovery.py`**

Find line 43 (`client = LLMClient()`) and line 48 (`if client.settings.llm_enabled:`). Replace both:

```python
    client = LLMClient(state.get("settings_override"))
```

```python
        if client.llm_enabled:
```

The two edited lines in context (showing surrounding lines for clarity):

```python
    # line ~42
    client = LLMClient(state.get("settings_override"))
    system = client.load_prompt("flow_discovery")
    prompt = f"URL: {url}\nIntent: {intent}\n\nReturn 3-5 critical user journeys as a JSON array."

    try:
        if client.llm_enabled:
```

- [ ] **Step 2: Update `agents/error_diagnosis.py`**

Find line 65 (`client = LLMClient()`) and line 73 (`if client.settings.llm_enabled:`). Apply the same two substitutions:

```python
    client = LLMClient(state.get("settings_override"))
```

```python
        if client.llm_enabled:
```

- [ ] **Step 3: Update `agents/adaptive_repair.py`**

Find line 87 (`client = LLMClient()`) and line 96 (`if client.settings.llm_enabled:`). Apply the same two substitutions:

```python
    client = LLMClient(state.get("settings_override"))
```

```python
        if client.settings.llm_enabled:  →  if client.llm_enabled:
```

- [ ] **Step 4: Update `agents/script_generator.py`**

`_generate_script_with_llm` is a helper that doesn't receive `state`. Thread the override through the call chain.

**4a.** Change `_generate_script_with_llm` signature and its `LLMClient()` call and `llm_enabled` check:

```python
def _generate_script_with_llm(
    flow: str, url: str, intent: str, settings_override: dict | None = None
) -> str | None:
    client = LLMClient(settings_override)
    if not client.llm_enabled:
        return None
```

**4b.** Change `build_script` to accept and pass override:

```python
def build_script(flow: str, url: str, intent: str = "", settings_override: dict | None = None) -> str:
    """Build a Playwright script string for a single flow."""
    script = _generate_script_with_llm(flow, url, intent, settings_override)
    if script:
        return script
    return _build_fallback_script(flow, url)
```

**4c.** Change `_resolve_scripts_for_flows` to accept and pass override (add `settings_override: dict | None = None` parameter, pass it to `build_script` on line 236):

```python
def _resolve_scripts_for_flows(
    url: str,
    intent: str,
    flows: list[str],
    *,
    force_flows: set[str] | None = None,
    settings_override: dict | None = None,
) -> tuple[list[str], dict[str, str], list[str], list[str], list[str]]:
```

In the `for flow in flows:` loop, change the `build_script` call (line ~236):

```python
        script = build_script(flow, url, intent, settings_override)
```

**4d.** In `generate_scripts`, pass the override to `_resolve_scripts_for_flows`:

```python
def generate_scripts(state: AgentState) -> dict[str, Any]:
    flows = state.get("discovered_flows", [])
    url = state["url"]
    intent = state["intent"]
    logger.info("Resolving scripts for %d flows (hybrid/local storage)", len(flows))

    scripts, script_sources, flows_reused, flows_generated, flows_regenerated = _resolve_scripts_for_flows(
        url, intent, flows, settings_override=state.get("settings_override")
    )
    ...
```

**4e.** In `regenerate_current_flow` (line ~281), find any call to `build_script` and add `settings_override=state.get("settings_override")`.

- [ ] **Step 5: Verify Python syntax**

```bash
python -c "import agents.flow_discovery, agents.error_diagnosis, agents.adaptive_repair, agents.script_generator; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add agents/flow_discovery.py agents/error_diagnosis.py agents/adaptive_repair.py agents/script_generator.py
git commit -m "feat: pass settings_override to LLMClient in all agents"
```

---

## Task 15: Backend — Orchestrator

**Files:**
- Modify: `orchestrator/graph.py`

- [ ] **Step 1: Update `_route_after_execute` to read limits from state override**

Replace the body of `_route_after_execute` (keeping the same signature):

```python
def _route_after_execute(
    state: AgentState,
) -> Literal["executor", "regression_monitor", "error_diagnosis", "regenerate_flow", "escalate"]:
    status = state.get("status", "")
    settings = get_settings()
    override = state.get("settings_override") or {}

    max_retries = int(override["max_retries"]) if "max_retries" in override else settings.max_retries
    max_repair = (
        int(override["max_repair_before_regenerate"])
        if "max_repair_before_regenerate" in override
        else settings.max_repair_before_regenerate
    )

    if status == "executing":
        return "executor"
    if status == "execution_success":
        return "regression_monitor"
    if status == "execution_failed":
        if state.get("retry_count", 0) >= max_retries:
            return "escalate"
        flow = _current_flow(state)
        repair_attempts = state.get("flow_repair_counts", {}).get(flow, 0)
        if repair_attempts >= max_repair:
            logger.info(
                "Flow %s exceeded repair threshold (%d); regenerating script",
                flow,
                max_repair,
            )
            return "regenerate_flow"
        return "error_diagnosis"
    logger.warning("Unexpected status after execute: %s", status)
    return "regression_monitor"
```

- [ ] **Step 2: Update `run_pipeline` to accept and store override**

```python
def run_pipeline(
    url: str, intent: str, run_id: str, settings_override: dict | None = None
) -> AgentState:
    logger.info("Starting pipeline run_id=%s url=%s", run_id, url)
    app = compile_graph()
    initial_state: AgentState = {
        "url": url,
        "intent": intent,
        "run_id": run_id,
        "settings_override": settings_override,
        "discovered_flows": [],
        "generated_scripts": [],
        "execution_results": [],
        "diagnosis": None,
        "repaired_script": None,
        "retry_count": 0,
        "auto_repairs": 0,
        "screenshots": [],
        "regression_diff": None,
        "final_report": None,
        "status": "starting",
        "current_script_index": 0,
        "human_escalation": False,
        "flow_repair_counts": {},
        "script_sources": {},
        "flows_reused": [],
        "flows_generated": [],
        "flows_regenerated": [],
    }
    result = app.invoke(initial_state)
    logger.info("Pipeline complete run_id=%s status=%s", run_id, result.get("status"))
    return result
```

- [ ] **Step 3: Verify syntax**

```bash
python -c "from orchestrator.graph import run_pipeline; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add orchestrator/graph.py
git commit -m "feat: thread settings_override through pipeline; honour per-run retry limits"
```

---

## Task 16: Backend — main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Extend `RunRequest` with optional settings fields**

Replace the existing `RunRequest` class:

```python
class RunRequest(BaseModel):
    url: HttpUrl
    intent: str = Field(min_length=1, examples=["Test checkout flow"])
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    use_mock_llm: bool | None = None
    max_retries: int | None = None
    max_repair_before_regenerate: int | None = None
```

- [ ] **Step 2: Build `settings_override` dict in `start_run` and pass it to `_execute_run`**

Replace the `start_run` function:

```python
@app.post("/run", response_model=RunResponse)
def start_run(request: RunRequest, background_tasks: BackgroundTasks) -> RunResponse:
    run_id = str(uuid.uuid4())
    run_store.set_status(run_id, "running", progress=0)

    override: dict = {}
    if request.openrouter_api_key is not None:
        override["openrouter_api_key"] = request.openrouter_api_key
    if request.openrouter_model is not None:
        override["openrouter_model"] = request.openrouter_model
    if request.use_mock_llm is not None:
        override["use_mock_llm"] = request.use_mock_llm
    if request.max_retries is not None:
        override["max_retries"] = request.max_retries
    if request.max_repair_before_regenerate is not None:
        override["max_repair_before_regenerate"] = request.max_repair_before_regenerate

    background_tasks.add_task(
        _execute_run,
        run_id,
        str(request.url),
        request.intent,
        override or None,
    )
    return RunResponse(
        run_id=run_id,
        status="running",
        dashboard_url=f"/dashboard/{run_id}",
    )
```

- [ ] **Step 3: Update `_execute_run` to accept and pass `settings_override`**

```python
def _execute_run(run_id: str, url: str, intent: str, settings_override: dict | None = None) -> None:
    run_store.set_status(run_id, "running", progress=10)
    try:
        result = run_pipeline(url=url, intent=intent, run_id=run_id, settings_override=settings_override)
        report = result.get("final_report") or {}
        run_store.set_report(run_id, report)
        final_status = report.get("status", result.get("status", "success"))
        run_store.set_status(run_id, final_status, progress=100)
    except Exception as exc:
        logger.exception("Run failed run_id=%s", run_id)
        run_store.set_status(run_id, "failed", progress=100)
        run_store.set_report(
            run_id,
            {"run_id": run_id, "status": "failed", "error": str(exc)},
        )
```

- [ ] **Step 4: Remove the old `/dashboard` routes and add SPA static serving**

Remove these two route handlers completely:

```python
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/dashboard/{run_id}", response_class=HTMLResponse)
def dashboard(run_id: str | None = None) -> HTMLResponse:
    ...
```

Also remove the `DASHBOARD_HTML` constant at the top of the file (it's no longer needed):

```python
DASHBOARD_HTML = Path(__file__).resolve().parent / "dashboard" / "index.html"
```

Then add static asset mount and SPA catch-all. These must be added **after** all API routes. Add at the bottom of the route definitions, just before the `_execute_run` and `__main__` block:

```python
# Serve the built React frontend — must come AFTER all API routes
_FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    def serve_spa(full_path: str) -> HTMLResponse:
        index = _FRONTEND_DIST / "index.html"
        return HTMLResponse(index.read_text(encoding="utf-8"))
```

- [ ] **Step 5: Remove unused import `HTMLResponse` if still needed (it's used by `serve_spa`)**

Verify the import line still has `HTMLResponse`:

```python
from fastapi.responses import HTMLResponse, RedirectResponse
```

It should already be there — no change needed.

- [ ] **Step 6: Verify FastAPI starts**

```bash
python -c "from main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add main.py
git commit -m "feat: extend RunRequest with settings; serve React SPA from FastAPI"
```

---

## Task 17: Deployment files

**Files:**
- Create: `api/index.py`
- Create: `vercel.json`

- [ ] **Step 1: Create `api/index.py`**

```python
"""Vercel Python serverless entry point — imports the FastAPI app from main.py."""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from main import app` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app  # noqa: F401, E402
```

- [ ] **Step 2: Create `vercel.json`**

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": null,
  "functions": {
    "api/index.py": {
      "runtime": "python3.12",
      "maxDuration": 60
    }
  },
  "rewrites": [
    { "source": "/run", "destination": "/api/index.py" },
    { "source": "/status/:path*", "destination": "/api/index.py" },
    { "source": "/report/:path*", "destination": "/api/index.py" },
    { "source": "/api/runs", "destination": "/api/index.py" },
    { "source": "/health", "destination": "/api/index.py" },
    { "source": "/screenshots/:path*", "destination": "/api/index.py" },
    { "source": "/:path*", "destination": "/index.html" }
  ]
}
```

> **Note:** Playwright's headless Chromium (~280 MB) exceeds Vercel's 250 MB serverless function limit. The UI and all read-only API endpoints work on Vercel, but actual browser execution (`/run`) will fail at the Playwright step on Vercel. For full execution, host the FastAPI backend on Railway/Render/Fly.io and point the React app's API calls there via an env var (`VITE_API_BASE`).

- [ ] **Step 3: Commit**

```bash
git add api/index.py vercel.json
git commit -m "feat: add Vercel deployment config and api/index.py adapter"
```

---

## Task 18: End-to-end smoke test (local)

- [ ] **Step 1: Start the FastAPI backend**

In one terminal, from the project root:

```bash
pip install -r requirements.txt
python main.py
```

Expected: `Uvicorn running on http://0.0.0.0:8000`

- [ ] **Step 2: Start the React dev server**

In a second terminal:

```bash
cd frontend && npm run dev
```

Expected: `Local: http://localhost:5173/`

- [ ] **Step 3: Verify landing page loads**

Open `http://localhost:5173/` in a browser.

Expected:
- Dark background (#0f1419)
- Header shows "Browser Automation AI Agent" with hamburger icon
- Title "Browser Automation AI Agent" in center
- Prompt textarea and URL input visible
- "Run Automation" button

- [ ] **Step 4: Verify hamburger menu**

Click the hamburger icon (☰ top-left).

Expected:
- Drawer slides in from the left
- 5 settings fields: API Key (password), Model dropdown, Mock LLM toggle, Max Retries, Max Repairs
- Clicking outside closes the drawer

- [ ] **Step 5: Submit a run with mock LLM**

1. Open hamburger menu → toggle "Use Mock LLM" ON → close menu
2. Enter any text in the prompt textarea
3. Enter `https://example.com` in the URL field
4. Click "Run Automation"

Expected:
- Button shows "Starting…" then execution log appears
- Log panel shows "Run ID: …" with a UUID
- Log lines appear: "Run started", "Initializing pipeline…", "Discovering user flows…", etc.
- After ~30 seconds, final line appears: "✓ Complete — status: success" (or similar)
- "View Dashboard →" button appears

- [ ] **Step 6: Navigate to dashboard**

Click "View Dashboard →"

Expected:
- Navigates to `/dashboard/<run_id>`
- Left sidebar shows the run with its intent text and status badge
- Right panel shows: Run ID, target URL, metric cards (Flows Passed, Auto Repairs, Retries, Regressions), Flow Execution table, Screenshots section
- "Raw JSON" link at bottom

- [ ] **Step 7: Verify production build serves from FastAPI**

```bash
cd frontend && npm run build
```

Then open `http://localhost:8000/` in a browser (FastAPI server must be running).

Expected: same landing page served from the FastAPI server (React SPA via static mount + catch-all route).

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "feat: complete React landing page + dashboard with settings override support"
```

---

## Self-Review Checklist

| Spec requirement | Task covering it |
|---|---|
| Landing page title "Browser Automation AI Agent" | Tasks 10, 11 |
| Hamburger menu on the left | Task 5 |
| OpenRouter API Key as secret field with eye toggle | Task 5 |
| Model dropdown (Haiku 4.5, Sonnet 4) | Task 5 |
| Mock LLM toggle | Task 5 |
| Max Retries numeric field | Task 5 |
| Max Repairs Before Regenerate numeric field | Task 5 |
| Settings map to env vars / backend config | Tasks 13–16 |
| Free-format prompt + URL field + submit button | Task 6 |
| Logs at bottom after submit with run_id | Task 7 |
| Simulated log lines from progress % | Task 4 |
| View Dashboard button after completion | Task 7 |
| Dashboard uses existing UI (dark theme, same layout) | Tasks 8, 11 |
| Dashboard is React-compliant (hooks, router, components) | Tasks 8–11 |
| Session-only settings (no localStorage) | Task 3 |
| Deployable on Vercel as one package | Task 17 |
| Vite + React + TypeScript in `frontend/` | Task 1 |
| `api/index.py` + `vercel.json` | Task 17 |
| FastAPI serves React SPA | Task 16 |
| Backend RunRequest accepts override fields | Task 16 |
| AgentState carries settings_override | Task 12 |
| LLMClient respects per-run override | Task 13 |
| All 4 agents pass override to LLMClient | Task 14 |
| Retry/repair limits respect override | Task 15 |
