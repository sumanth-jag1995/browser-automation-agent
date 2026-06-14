# Frontend Environment Variable Setup Guide

## Quick Start

### Local Development (Frontend + Backend on localhost)

**No setup required** — everything works by default with dev proxy.

```bash
cd frontend
npm run dev
# Visits http://localhost:5173
# API calls auto-proxy to http://localhost:8000 (dev proxy in vite.config.ts)
```

Browser DevTools → Network → See `/run`, `/status` requests? They go to `localhost:8000` ✓

---

## Environment Variable Precedence

The frontend resolves `VITE_API_BASE` in this order:

1. **Build-time define** (`__VITE_API_BASE__` from Vite config)
   - Set in `.env`, `.env.local`, `.env.production`, or CLI
2. **Runtime injection** (`window.ENV?.API_BASE`)
   - Backend can inject into HTML (for future use)
3. **Default: relative path**
   - Same origin (works with dev proxy in dev mode)

---

## Setup by Scenario

### Scenario 1: Local Dev (Backend separate on port 8000)

No .env changes needed. Dev proxy handles it automatically.

**Verify:**
```bash
cd frontend && npm run dev
# Open browser
# DevTools → Network → Submit run
# See POST http://localhost:5173/run (proxied to 8000)
```

---

### Scenario 2: Production Build (Backend on Railway)

**Backend URL:** `https://browser-automation-api-prod.railway.app`

#### Option A: Set at build time

```bash
# Build with env var
VITE_API_BASE=https://browser-automation-api-prod.railway.app npm run build

# Or edit .env.production
```

**frontend/.env.production:**
```
VITE_API_BASE=https://browser-automation-api-prod.railway.app
```

Then build:
```bash
npm run build
# dist/index.html will have __VITE_API_BASE__ hardcoded
```

#### Option B: Deploy on Vercel (recommended)

Set env var in Vercel dashboard:

```
Name: VITE_API_BASE
Value: https://browser-automation-api-prod.railway.app
```

Vercel will:
1. Load `.env` from repo (base value)
2. Override with Vercel env var
3. Build with `npm run build`
4. Vite substitutes `__VITE_API_BASE__` in HTML/JS

---

## Testing

### Test 1: Verify env var is loaded

```bash
cd frontend
npm run build

# Check dist/index.html for __VITE_API_BASE__
grep -i "vite_api_base" dist/index.html || echo "not hardcoded (uses relative path)"
```

### Test 2: Verify at runtime

1. Open built site
2. DevTools → Console
3. Type: `localStorage.getItem('debug')` or manually check Network tab
4. Submit a run → check API call URL in Network tab

---

## Troubleshooting

### Problem: API calls fail, showing localhost:5173/run

**Cause:** API base URL not set, using relative path.

**Solution:**
- Check if backend is running (`http://localhost:8000/health`)
- For dev: `npm run dev` uses proxy → should work
- For prod build: Set `VITE_API_BASE` before build

### Problem: API calls show wrong URL in Network tab

**Cause:** `VITE_API_BASE` is set but incorrect.

**Solution:**
```bash
# Check what was built in
grep __VITE_API_BASE__ dist/index.html

# Or in browser console after load:
console.log(import.meta.env.VITE_API_BASE)
```

### Problem: TypeScript error "Cannot find name '__VITE_API_BASE__"

**Cause:** `vite-env.d.ts` not found or not declaring global.

**Solution:**
- Ensure `frontend/src/vite-env.d.ts` exists
- Ensure it has: `declare const __VITE_API_BASE__: string;`

---

## .env File Reference

### `.env` (committed, shared defaults)
```
VITE_API_BASE=
```

### `.env.local` (local dev, git-ignored)
```
# Developers override here for local changes
# Leave empty for dev proxy, or set to custom backend
VITE_API_BASE=
```

### `.env.production` (production build defaults)
```
# Production defaults (can be overridden by CI/CD)
VITE_API_BASE=
```

### Vercel Dashboard (runtime)
```
Environment Variable: VITE_API_BASE
Value: https://your-backend.railway.app
```

---

## How Vite Loads Env Vars

1. **Load base file:** `.env`
2. **Load mode file:** `.env.{mode}` (e.g., `.env.production`)
3. **Load local file:** `.env.local` (overrides step 1)
4. **Load mode+local:** `.env.{mode}.local` (overrides steps 1-3)
5. **CLI override:** `VITE_API_BASE=xxx npm run build` (overrides 1-4)
6. **CI/CD override:** Platform env vars (Vercel, GitHub Actions, etc.)

---

## Production Deployment Checklist

- [ ] `.env` file exists (empty `VITE_API_BASE=` is OK)
- [ ] `.env.local` is git-ignored (contains local overrides)
- [ ] `vite-env.d.ts` declares `__VITE_API_BASE__`
- [ ] Vite config uses `loadEnv()` and `define`
- [ ] Backend URL is correct (test with `curl https://your-api/health`)
- [ ] On Vercel: Set `VITE_API_BASE` env var in dashboard
- [ ] After setting env var: Trigger rebuild on Vercel
- [ ] Test end-to-end: Submit run → check Network tab for correct API URL

---

## Console Debugging

When things go wrong, check the browser console:

```javascript
// In DevTools Console
console.debug = console.log;  // Enable debug logs
location.reload();  // Reload to see [API] logs

// Then submit a run and look for:
// [API] Using build-time VITE_API_BASE: ...
// [API] Using relative path (same origin)
// [API] POST http://... 

// Or check the actual URL being called:
fetch('/run', {method: 'POST', body: '{}'})
  .then(r => r.json())
  .catch(e => console.log('Error:', e));
```

---

## Summary

| Scenario | Setup | Result |
|----------|-------|--------|
| Local dev | None | Proxy to localhost:8000 ✓ |
| Prod (manual) | Edit `.env.production` | Build-time hardcoded URL |
| Prod (Vercel) | Set env var in dashboard | Vercel injects at build time |
| Custom backend | `VITE_API_BASE=https://...` | All API calls go there |
