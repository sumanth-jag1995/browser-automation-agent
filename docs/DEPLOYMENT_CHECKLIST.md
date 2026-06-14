# Production Deployment Checklist

## Pre-Deployment: Code Changes

### Backend (FastAPI)

- [x] Fix `llm/client.py` line 33: Check `bool(self._effective_api_key)` instead of `self.settings.llm_enabled`
  - **Why:** UI-provided credentials now enable LLM even without env vars
- [x] Fix `llm/client.py` line 47: Check override for provider detection
  - **Why:** Respect UI-selected OpenRouter key
- [x] Add CORS middleware to `main.py`
  - **Why:** Allow cross-origin API calls (Vercel frontend → Railway backend)

### Frontend (React)

- [x] Update `frontend/src/api/client.ts`: Add `VITE_API_BASE` support
  - **Why:** Point frontend to different backend URL in production
- [x] Update `frontend/index.html`: Add runtime config injection
  - **Why:** Support dynamic API_BASE at runtime
- [x] Create `frontend/.env.example`: Document env vars
  - **Why:** Guide developers on configuration

---

## Deployment Flow

### Step 1: Deploy Backend to Railway (or Render/Fly.io)

```bash
# 1. Create Railway project
railway login
railway init

# 2. Set environment variables in Railway dashboard
# OPENROUTER_API_KEY = sk-or-v1-xxxxx (optional, can use UI)
# USE_MOCK_LLM = false
# PLAYWRIGHT_HEADLESS = true

# 3. Connect repo and auto-deploy
railway up

# 4. Get backend URL
# Example: https://browser-automation-api-prod.railway.app
```

**Verify:**
```bash
curl https://browser-automation-api-prod.railway.app/health
# Expected: {"status": "ok"}
```

### Step 2: Update CORS Allowlist (Optional)

If frontend URL is known, add to `main.py` CORS middleware:

```python
allow_origins=[
    "https://your-vercel-domain.vercel.app",  # Your Vercel frontend
    "http://localhost:5173",  # Local dev
],
```

### Step 3: Deploy Frontend to Vercel

```bash
# 1. Build locally to test
cd frontend && npm run build

# 2. Deploy to Vercel
vercel --prod

# 3. Set VITE_API_BASE environment variable in Vercel dashboard
# VITE_API_BASE = https://browser-automation-api-prod.railway.app

# 4. Redeploy to apply env var
vercel --prod
```

**Verify:**
```bash
# Open browser DevTools → Network tab
# Submit a run → see API calls to Railway backend ✓
```

---

## Testing Checklist (Post-Deployment)

- [ ] Backend `/health` endpoint responds
- [ ] Frontend loads from Vercel
- [ ] Landing page renders (dark theme, title, form)
- [ ] Hamburger menu opens with all settings fields
- [ ] Can enter OpenRouter API key in UI
- [ ] Submit run with mock LLM: see logs and completion
- [ ] Dashboard loads and shows run details
- [ ] Browser DevTools shows API calls going to correct backend URL

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "CORS error in browser console" | Frontend and backend different origins | Add frontend URL to CORS `allow_origins` in `main.py` + redeploy backend |
| "API call timeout or 404" | `VITE_API_BASE` not set or incorrect | Check Vercel env var, rebuild (`vercel --prod`) |
| "Settings override not working" | Override not passed to agents | Verify `llm/client.py` line 33 fix applied |
| "Playwright fails on Vercel" | Expected — Vercel doesn't support Playwright | Backend must run elsewhere (Railway/Render/Fly) |
| "Mock LLM not used" | `use_mock_llm` not in override | Toggle "Use Mock LLM" in UI hamburger menu |

---

## Environment Variables for Production

### Backend (Railway Settings)

```
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=anthropic/claude-sonnet-4
USE_MOCK_LLM=false
PLAYWRIGHT_HEADLESS=true
LOG_LEVEL=INFO
MAX_RETRIES=3
MAX_REPAIR_BEFORE_REGENERATE=2
```

### Frontend (Vercel Settings)

```
VITE_API_BASE=https://browser-automation-api-prod.railway.app
```

---

## Optional: Railway Deployment Script

Save as `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying to Railway..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Push to Railway
echo "🚂 Pushing to Railway..."
railway up

echo "✅ Deployment complete!"
echo "Check: https://your-railway-domain.railway.app/health"
```

---

## Production Notes

- **Playwright runs on backend only** — Vercel is for static React SPA only
- **Settings override is session-only** — No localStorage, fresh on page reload
- **UI credentials don't persist** — Users must enter API key each session (security feature)
- **Mock LLM is fast** — Use for testing without API costs
- **Max retries/repairs can be overridden per run** — Frontend sends them in request body
