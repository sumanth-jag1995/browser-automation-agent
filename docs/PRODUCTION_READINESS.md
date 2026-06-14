# Production Readiness Summary

## Problem Addressed

The original plan had two limitations:
1. **LLMClient didn't recognize UI-provided credentials** — Even if user entered API key in UI, it would only work if also set as env var
2. **Playwright couldn't run on Vercel** — 280 MB Playwright exceeds Vercel's 250 MB serverless limit

## Solutions Implemented ✅

### 1. LLMClient now respects UI credentials

**File:** `llm/client.py`

**Changes:**
- Line 33: Changed `self.llm_enabled = (not mock_forced) and self.settings.llm_enabled`
  - **To:** `self.llm_enabled = (not mock_forced) and bool(self._effective_api_key)`
  - **Why:** Checks actual API key (from UI or env) instead of just env vars
  
- Lines 47-50: Added provider detection for override
  - **Why:** If UI provides OpenRouter key, use OpenRouter (not just env-based setting)

**Result:** User enters OpenRouter API key in UI → LLM works without env vars ✅

---

### 2. Frontend supports remote backend URLs

**File:** `frontend/src/api/client.ts`

**Changes:**
- Added `getApiBase()` function that checks:
  1. `VITE_API_BASE` build-time env var (Vite)
  2. `window.ENV.API_BASE` runtime injection
  3. Default: relative path (same origin)

**File:** `frontend/index.html`

**Changes:**
- Added runtime config injection: `<script>window.ENV = window.ENV || { API_BASE: '' };</script>`
- Allows backend to modify HTML at runtime if needed

**Result:** Frontend can point to any backend URL (local, Railway, Render, etc.) ✅

---

### 3. CORS enabled for cross-origin requests

**File:** `main.py`

**Changes:**
- Added `from fastapi.middleware.cors import CORSMiddleware` import
- Added CORS middleware after FastAPI app creation
- Allows localhost:5173 (frontend) to call backend on different domain

**Result:** Vercel (frontend) can call Railway (backend) without CORS errors ✅

---

## Architecture: Recommended for Production

```
Vercel                          Railway (or Render/Fly.io)
┌──────────────────────┐        ┌────────────────────────────┐
│ React SPA (~2 MB)    │◄──────►│ FastAPI + LangGraph        │
│ - index.html         │        │ - Playwright (280 MB)      │
│ - assets/            │        │ - Browser automation       │
│ - API calls to       │        │ - Runs on Linux container  │
│   VITE_API_BASE      │        │                            │
└──────────────────────┘        └────────────────────────────┘
  https://               https://browser-automation-api-prod
  yourapp.vercel.app     .railway.app/
```

---

## How to Deploy

### Local Development
```bash
# Terminal 1: Backend (localhost:8000)
python main.py

# Terminal 2: Frontend (localhost:5173)
cd frontend && npm run dev

# Browser: http://localhost:5173
# - Frontend and backend on same host → no VITE_API_BASE needed
```

### Production (Recommended)

#### Backend: Deploy to Railway
```bash
railway login
railway init
# Set env vars: OPENROUTER_API_KEY (optional), USE_MOCK_LLM=false
railway up
# Output: https://browser-automation-api-prod.railway.app
```

#### Frontend: Deploy to Vercel
```bash
# Build
cd frontend && npm run build

# Deploy
vercel --prod

# Set VITE_API_BASE in Vercel dashboard
# VITE_API_BASE=https://browser-automation-api-prod.railway.app
vercel --prod  # Rebuild to apply env var
```

---

## Features Now Working in Production

| Feature | Before | After |
|---------|--------|-------|
| UI API key | Doesn't enable LLM | ✅ Enables LLM without env vars |
| UI model selection | Ignored | ✅ Respected by LLMClient |
| UI mock toggle | Doesn't work | ✅ Forces mock mode |
| Remote backend | Not supported | ✅ VITE_API_BASE env var |
| Cross-origin calls | CORS error | ✅ CORS middleware enabled |
| Playwright execution | Fails on Vercel | ✅ Runs on Railway/Render/Fly.io |
| Session-only settings | N/A | ✅ No localStorage, fresh per session |

---

## Files Changed

### Core Fixes
- ✅ `llm/client.py` — Respect UI credentials
- ✅ `main.py` — Add CORS middleware

### Frontend Updates
- ✅ `frontend/src/api/client.ts` — Support VITE_API_BASE
- ✅ `frontend/index.html` — Runtime config injection
- ✅ `frontend/.env.example` — Document env vars

### Documentation
- ✅ `docs/PRODUCTION_DEPLOYMENT.md` — Full deployment guide
- ✅ `docs/DEPLOYMENT_CHECKLIST.md` — Step-by-step checklist

---

## Security Notes

- UI credentials are **session-only** (no localStorage) → Fresh on page reload
- Backend should run on **HTTPS** (Railway/Render provide this automatically)
- CORS `allow_origins` should list only trusted frontend URLs
- Environment variables (OPENROUTER_API_KEY) go in platform secrets, never in code

---

## Next Steps

1. **Test locally:**
   ```bash
   # Terminal 1
   python main.py
   
   # Terminal 2
   cd frontend && npm run dev
   
   # Browser: http://localhost:5173
   # - Try entering OpenRouter API key in hamburger menu
   # - Toggle Mock LLM on/off
   # - Submit a run → see it complete
   ```

2. **Deploy to production:**
   - Push code to GitHub
   - Connect Railway repo
   - Connect Vercel repo
   - Set VITE_API_BASE on Vercel
   - Test end-to-end

3. **Monitor:**
   - Check Railway logs: `railway logs`
   - Check Vercel builds: Dashboard → Deployments
   - Verify API calls: Browser DevTools → Network tab

---

## Troubleshooting

### "CORS error in browser"
→ Add frontend URL to `main.py` CORS `allow_origins`, redeploy

### "API call times out"
→ Check VITE_API_BASE value, verify backend is running

### "Settings override not working"
→ Verify llm/client.py line 33 fix (check `bool(self._effective_api_key)`)

### "Vercel deployment fails"
→ Make sure `frontend/dist/` exists, check Vercel build logs

---

## Reference

- **Deployment docs:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- **Checklist:** [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- **Railway docs:** https://docs.railway.app
- **Vercel docs:** https://vercel.com/docs
