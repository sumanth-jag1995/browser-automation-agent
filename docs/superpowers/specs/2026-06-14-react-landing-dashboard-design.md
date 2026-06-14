# React Landing Page & Dashboard Design

**Date:** 2026-06-14  
**Project:** Browser Automation AI Agent  
**Scope:** Add a Vite + React frontend (landing page + dashboard) to the existing FastAPI project, deployable as a single Vercel package.

---

## Goals

- Replace the vanilla JS `dashboard/index.html` with a proper React SPA
- Add a new landing page where users submit automation runs
- Surface session-scoped settings (API key, model, flags) via a hamburger drawer
- Keep the entire app deployable as one Vercel project (FastAPI backend + React frontend)

---

## Architecture

### Deployment Model

Single Vercel deployment. `vercel.json` defines two builds:

1. **Frontend** — Vite builds `frontend/` → `frontend/dist/`
2. **Backend** — `@vercel/python` serves `main.py` as a serverless function

Routes in `vercel.json`:
- `/run`, `/status/*`, `/report/*`, `/api/*`, `/health`, `/screenshots/*` → Python function
- `/*` → SPA catch-all (serves `frontend/dist/index.html`)

In local dev, Vite's dev server proxies API calls to `localhost:8000`.

### Folder Structure

```
browser-automation-agent/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts          # typed fetch wrappers
│   │   ├── types/
│   │   │   └── index.ts           # RunRequest, RunResponse, Report, Status
│   │   ├── hooks/
│   │   │   ├── useSettings.ts     # session state (React context) for drawer fields
│   │   │   └── useRunPoller.ts    # polls /status + /report, emits log events
│   │   ├── components/
│   │   │   ├── HamburgerMenu.tsx  # left-side settings drawer
│   │   │   ├── RunForm.tsx        # prompt textarea + URL input + submit button
│   │   │   ├── LogPanel.tsx       # log output, run_id display, dashboard button
│   │   │   └── dashboard/
│   │   │       ├── RunList.tsx    # sidebar list of recent runs
│   │   │       ├── MetricCards.tsx
│   │   │       ├── FlowTable.tsx
│   │   │       └── ScreenshotGrid.tsx
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   ├── App.tsx                # React Router: / and /dashboard/:runId?
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── vercel.json                    # NEW
├── main.py                        # MODIFIED (RunRequest + static serve)
└── ... (all other files unchanged)
```

---

## Settings (Hamburger Drawer)

All settings are **session-only** — held in React context, lost on page refresh. They are sent with every POST `/run` request as optional body fields and override the server's env-based config for that run.

| UI Label | Field in RunRequest | Env var | Default |
|---|---|---|---|
| OpenRouter API Key | `openrouter_api_key` | `OPENROUTER_API_KEY` | — |
| Model | `openrouter_model` | `OPENROUTER_MODEL` | `anthropic/claude-haiku-4-5` |
| Use Mock LLM | `use_mock_llm` | `USE_MOCK_LLM` | `false` |
| Max Retries | `max_retries` | `MAX_RETRIES` | `3` |
| Max Repairs Before Regenerate | `max_repair_before_regenerate` | `MAX_REPAIR_BEFORE_REGENERATE` | `2` |

**Model dropdown options:**
- `anthropic/claude-haiku-4-5` → display label "Claude Haiku 4.5"
- `anthropic/claude-sonnet-4` → display label "Claude Sonnet 4"

**API Key field:** `<input type="password">` with an eye-icon toggle to reveal/hide. No persistence to localStorage.

**Drawer behaviour:** Opens from the left on hamburger click. Clicking outside or pressing Escape closes it. Does not block the page (overlay with click-away).

---

## Landing Page

### Layout

```
┌──────────────────────────────────────────────────────────┐
│ ☰   Browser Automation AI Agent                          │  header
├──────────────────────────────────────────────────────────┤
│                                                          │
│           Browser Automation AI Agent                   │
│     Describe a flow. We'll automate and test it.        │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Prompt                                            │ │
│  │  (free-form textarea, min 3 rows)                  │ │
│  ├────────────────────────────────────────────────────┤ │
│  │  URL    https://example.com                        │ │
│  └────────────────────────────────────────────────────┘ │
│                 [ ▶  Run Automation ]                    │
│                                                          │
│  ┌── Execution Log ──────────────────────── (hidden    │ │
│  │  until first submit)                                │ │
│  │  Run ID: a3f2-bc91-…                               │ │
│  │  [HH:MM:SS] Run started                             │ │
│  │  [HH:MM:SS] …log lines…                             │ │
│  │  [HH:MM:SS] ✓ Complete — status: success            │ │
│  │              [ View Dashboard → ]                   │ │
│  └──────────────────────────────────────────────────── ┘ │
└──────────────────────────────────────────────────────────┘
```

### Submit Flow

1. User fills prompt + URL, clicks **Run Automation**
2. Button becomes disabled/loading spinner
3. POST `/run` with `{ url, intent, ...settings }` → returns `{ run_id, status, dashboard_url }`
4. Log panel appears, showing Run ID
5. `useRunPoller` begins polling `GET /status/{run_id}` every 2 seconds
6. Each progress threshold crossed appends a new log line (see table below)
7. When `progress === 100`: polling stops, final status line added, **View Dashboard** button appears
8. Clicking **View Dashboard** navigates to `/dashboard/{run_id}` via React Router

### Log Line Mapping

| Progress threshold | Log message |
|---|---|
| Run submitted | `Run started` |
| ≥ 10% | `Initializing pipeline…` |
| ≥ 20% | `Discovering user flows…` |
| ≥ 40% | `Generating Playwright scripts…` |
| ≥ 60% | `Executing automation scripts…` |
| ≥ 75% | `Diagnosing errors / repairing scripts…` |
| ≥ 85% | `Running regression checks…` |
| ≥ 95% | `Generating report…` |
| 100% + success | `✓ Complete — status: success` |
| 100% + failed/escalated | `✗ Run ended — status: <status>` |

Each line is prefixed with a `[HH:MM:SS]` client-side timestamp. Lines are only emitted once per threshold (tracked in a ref so re-renders don't duplicate them).

---

## Dashboard Page

Route: `/dashboard` and `/dashboard/:runId`

### Layout

```
┌──────────────────────────────────────────────────────────┐
│ ←  Browser Automation AI Agent — Dashboard               │  ← "/" link in header
├────────────────┬─────────────────────────────────────────┤
│  Recent Runs   │  <intent>                    ● <status> │
│  ──────────── │  Target: <url>                           │
│  run items…   │  Run ID: <id>  ·  <timestamp>            │
│               │                                          │
│               │  [Flows Passed] [Auto Repairs]           │
│               │  [Retries]      [Regressions]            │
│               │                                          │
│               │  Flow Execution                          │
│               │  ┌──────┬────────┬──────────┬────────┐  │
│               │  │Flow  │Status  │Homepage  │Error   │  │
│               │  └──────┴────────┴──────────┴────────┘  │
│               │                                          │
│               │  Screenshots                             │
│               │  [img grid…]                             │
│               │                                          │
│               │  Raw JSON: /report/<id>                  │
└────────────────┴─────────────────────────────────────────┘
```

### Behaviour

- On mount: `GET /api/runs` populates `RunList` sidebar
- `useParams()` extracts `runId`; if absent, defaults to first run from the list
- Clicking a sidebar run → `useNavigate(/dashboard/:runId)`
- If `status.progress < 100`, poll `GET /status/{runId}` + `GET /report/{runId}` every 2 seconds; clean up interval on unmount or when `runId` changes
- Color palette reuses the existing CSS variables mapped to Tailwind config:
  - `bg`: `#0f1419`, `surface`: `#1a2332`, `surface2`: `#243044`, `border`: `#2d3a4f`
  - `accent`: `#3b82f6`, `success`: `#22c55e`, `fail`: `#ef4444`, `warn`: `#f59e0b`

---

## Backend Changes

Four files need changes. All changes are additive or small modifications — no agent or storage files are touched.

### 1. main.py — Extend RunRequest + serve SPA

```python
class RunRequest(BaseModel):
    url: HttpUrl
    intent: str = Field(min_length=1)
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    use_mock_llm: bool | None = None
    max_retries: int | None = None
    max_repair_before_regenerate: int | None = None
```

`_execute_run` passes these optional fields as a `settings_override` dict into `run_pipeline`. The existing `/dashboard` and `/dashboard/{run_id}` GET routes are **removed** — the React Router SPA handles those URLs. A catch-all is added last (must come after all API routes):

```python
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}", response_class=HTMLResponse)
def serve_spa(full_path: str) -> HTMLResponse:
    index = Path("frontend/dist/index.html")
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not built")
    return HTMLResponse(index.read_text(encoding="utf-8"))
```

### 2. state/schema.py — Add settings override fields to AgentState

```python
# Optional per-run overrides forwarded from the frontend
settings_override: dict[str, Any] | None  # keys mirror RunRequest optional fields
```

This allows override values to travel through the LangGraph pipeline without coupling agents to the HTTP layer.

### 3. orchestrator/graph.py — Accept and thread override into pipeline

`run_pipeline` gains an optional `settings_override: dict | None = None` parameter. It stores the dict in the initial `AgentState`. `_route_after_execute` checks `state.get("settings_override", {})` for `max_retries` and `max_repair_before_regenerate` before falling back to `get_settings()`.

### 4. llm/client.py — Accept override in constructor

`LLMClient.__init__` accepts an optional `override: dict | None = None`. When present, it uses override values for `openrouter_api_key`, `openrouter_model`, and `use_mock_llm` instead of the env-based settings. Each agent that instantiates `LLMClient` passes `state.get("settings_override")` to it.

---

## vercel.json

Vercel's Python runtime requires the entry point to live under `api/`. A thin `api/index.py` file is added that imports the FastAPI `app` from `main.py` — this is the only new file outside `frontend/`.

```python
# api/index.py  (new file, ~3 lines)
from main import app  # noqa: F401  — Vercel ASGI handler picks up `app`
```

```json
{
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/static-build",
      "config": { "distDir": "dist" } },
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/run",              "dest": "/api/index.py" },
    { "src": "/status/(.*)",      "dest": "/api/index.py" },
    { "src": "/report/(.*)",      "dest": "/api/index.py" },
    { "src": "/api/(.*)",         "dest": "/api/index.py" },
    { "src": "/health",           "dest": "/api/index.py" },
    { "src": "/screenshots/(.*)", "dest": "/api/index.py" },
    { "src": "/(.*)",             "dest": "/frontend/dist/index.html" }
  ]
}
```

> **Note:** Playwright's headless Chromium (~280 MB) exceeds Vercel's 250 MB serverless function limit. For actual browser execution the pipeline will need a separate long-running host (e.g. Railway, Render, or a self-hosted VM). The React UI and all non-execution API endpoints (status, report, runs list) work fine on Vercel. This is an infrastructure concern outside the scope of this spec.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Bundler | Vite 5 |
| Framework | React 18 + TypeScript |
| Routing | React Router v6 |
| Styling | Tailwind CSS v3 (custom colors matching existing palette) |
| HTTP | native `fetch` (no extra library) |
| State | React context for settings, `useState`/`useEffect` for data |
| Icons | `lucide-react` (hamburger, eye, arrow) |

---

## Out of Scope

- Authentication / API key validation on the server
- Real server-side log streaming (SSE/WebSockets)
- Storing settings across sessions (no localStorage)
- Changing any agent, orchestrator, or storage files
