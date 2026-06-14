# Production Deployment Guide: Browser Automation Agent

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ Frontend (Vercel - Static + API calls)                  │
│ - React + Vite (build: ~2 MB)                           │
│ - Points to backend via VITE_API_BASE env var           │
└──────────────────────┬──────────────────────────────────┘
                       │ (HTTP/REST API calls)
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Backend (Railway/Render/Fly.io - Always runs)           │
│ - FastAPI + LangGraph                                   │
│ - Playwright (280 MB, runs headless in Linux container) │
│ - Serves both API endpoints + SPA fallback              │
└─────────────────────────────────────────────────────────┘
```

## Key Changes for Production

### 1. **LLMClient now respects UI-provided credentials** ✅
   - Fixed: `llm/client.py` now checks `self._effective_api_key` instead of env vars only
   - UI-provided OpenRouter API key now enables LLM even without `OPENROUTER_API_KEY` env var
   - Provider detection respects override (checks if `openrouter_api_key` in override)

### 2. **Frontend API client supports remote backend** ✅
   - `frontend/src/api/client.ts` now supports `VITE_API_BASE` env var
   - Supports both build-time and runtime configuration
   - Default: relative path (works when frontend + backend on same host)

---

## Deployment Scenarios

### Scenario A: Local Development (Frontend + Backend on same machine)

```bash
# Terminal 1: Backend on localhost:8000
cd browser-automation-agent
pip install -r requirements.txt
python main.py
# Uvicorn running on http://127.0.0.1:8000

# Terminal 2: Frontend on localhost:5173
cd frontend
npm run dev
# Local: http://localhost:5173/

# Browser: Open http://localhost:5173/
# - Frontend calls backend at http://localhost:8000 (relative path)
```

**No config needed** — frontend and backend communicate via relative paths.

---

### Scenario B: Vercel (Frontend) + Railway (Backend) — **Recommended for Production**

#### Backend Setup (Railway)

1. **Create Railway project:**
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   ```

2. **Add environment variables in Railway dashboard:**
   ```
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx  # Or leave empty for UI-only mode
   USE_MOCK_LLM=false
   PLAYWRIGHT_HEADLESS=true
   LOG_LEVEL=INFO
   ```

3. **Deploy:**
   ```bash
   railway up
   ```
   
   Railway generates a URL like: `https://browser-automation-api-prod.railway.app`

4. **Verify backend is running:**
   ```bash
   curl https://browser-automation-api-prod.railway.app/health
   # Expected: {"status": "ok"}
   ```

#### Frontend Setup (Vercel)

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   # Output: dist/ folder with index.html, assets/
   ```

2. **Create `vercel.json` (already created, verify):**
   ```json
   {
     "buildCommand": "cd frontend && npm install && npm run build",
     "outputDirectory": "frontend/dist",
     "framework": null,
     "env": {
       "VITE_API_BASE": "@vite-api-base"
     },
     "rewrites": [
       { "source": "/run", "destination": "/api/index.py" },
       { "source": "/status/:path*", "destination": "/api/index.py" },
       { "source": "/report/:path*", "destination": "/api/index.py" },
       { "source": "/api/runs", "destination": "/api/index.py" },
       { "source": "/:path*", "destination": "/index.html" }
     ]
   }
   ```

3. **Deploy to Vercel:**
   ```bash
   npm install -g vercel
   vercel --prod
   ```

4. **Set environment variable in Vercel dashboard:**
   - Go to Settings → Environment Variables
   - Add `VITE_API_BASE` = `https://browser-automation-api-prod.railway.app`

5. **Redeploy to apply env var:**
   ```bash
   vercel --prod
   ```

6. **Verify frontend loads:**
   - Open https://your-vercel-domain.vercel.app
   - Open browser DevTools → Network tab
   - Submit a run → see API calls go to `https://browser-automation-api-prod.railway.app/run` ✓

---

### Scenario C: All-in-one on Single Host (Railway/Render)

If you prefer to host everything on one platform:

1. **Deploy FastAPI + React SPA on Railway:**
   - Push code to GitHub
   - Connect repo to Railway
   - Railway builds with `npm run build` (frontend) + runs `python main.py`
   - Single URL: `https://your-app.railway.app`
   - Frontend + Backend on same origin → no `VITE_API_BASE` needed

2. **Verify:**
   ```bash
   curl https://your-app.railway.app/health
   open https://your-app.railway.app  # React SPA loads
   ```

---

## Troubleshooting Production Issues

### Issue: "API calls failing" / "CORS errors"

**Cause:** Frontend and backend are on different domains, CORS not configured.

**Fix:**
```python
# In main.py, add CORS middleware (before routes)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-domain.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Settings override not working" / "API key not recognized"

**Cause:** UI-provided API key is not reaching the backend, or `LLMClient` is still checking only env vars.

**Check:**
1. Verify fix in `llm/client.py` (line 33): should check `bool(self._effective_api_key)`
2. Verify `main.py` is passing `settings_override` to `_execute_run()`
3. In browser, open DevTools → Network → POST `/run` → check request body includes `openrouter_api_key`

### Issue: "Playwright execution fails on Vercel"

**Expected behavior** — Vercel serverless functions don't support Playwright. This is **by design**.

**Fix:** Use separate backend (Railway/Render/Fly.io) for Playwright execution. Frontend-only on Vercel.

### Issue: "Mock LLM not being used when expected"

**Cause:** `use_mock_llm` is not being set in override, or env var `USE_MOCK_LLM=true` is set on backend.

**Fix:**
1. Verify UI hamburger menu "Use Mock LLM" toggle is ON
2. Check request body in DevTools: should have `"use_mock_llm": true`
3. On backend, check logs: `LLMClient(settings_override={'use_mock_llm': True})` should show

---

## Environment Variables Reference

### Backend (Railway/Docker)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `` | OpenRouter API key (optional if UI provides it) |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4` | Default OpenRouter model |
| `USE_MOCK_LLM` | `false` | Force mock LLM responses (no API calls) |
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser headless (always true in prod) |
| `MAX_RETRIES` | `3` | Max retries per flow (can be overridden by UI) |
| `MAX_REPAIR_BEFORE_REGENERATE` | `2` | Max repair attempts (can be overridden by UI) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Frontend (Vite)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE` | `` | Backend URL (e.g., `https://api.example.com`) |

---

## Local Development with Different Backend

If you want to point a **local frontend** to a **remote backend**:

```bash
# frontend/.env.local
VITE_API_BASE=https://your-railway-backend.railway.app

# Then
cd frontend && npm run dev
# Frontend on localhost:5173 calls backend on Railway
```

---

## Security Checklist

- [ ] Set `OPENROUTER_API_KEY` in Railway secrets (never in code)
- [ ] Set `VITE_API_BASE` in Vercel env vars (frontend rebuild required)
- [ ] Enable CORS middleware to allow cross-origin calls
- [ ] Run Playwright with `PLAYWRIGHT_HEADLESS=true` (always)
- [ ] Use `.env.production` / secrets for sensitive credentials
- [ ] Verify `/health` endpoint returns 200 on backend
- [ ] Test end-to-end: UI settings → backend receives override → LLM responds

---

## Summary: What Changed for Production

1. **`llm/client.py`**: Now respects UI-provided credentials (line 33 fix)
2. **`frontend/src/api/client.ts`**: Now supports `VITE_API_BASE` env var
3. **`frontend/index.html`**: Added runtime config injection support
4. **`frontend/.env.example`**: Added environment variable documentation

**Result:**
- ✅ UI credentials work without env vars
- ✅ Frontend can point to remote backend
- ✅ Playwright runs on backend (not Vercel)
- ✅ Deployable on Vercel + Railway as separate services
