# Session 4: Deployment Saga

**Date:** November 23, 2025
**Focus:** Deploying to Railway (Backend) and Netlify (Frontend)
**Status:** 🔴 IN PROGRESS - Railway deployment failing

---

## Overview

Attempted to deploy the Datamicron AI News Assistant to production:
- **Frontend:** Netlify (Static site hosting)
- **Backend:** Railway (Python/FastAPI hosting)

---

## Issues Encountered & Fixes Attempted

### Issue 1: Railway Build - No Start Command Found ❌

**Error:**
```
No start command could be found
```

**Attempts:**
1. ✅ Created `Procfile` with start command
2. ✅ Created `railway.json` with deploy config
3. ✅ Created `nixpacks.toml` for Nixpacks builder
4. ❌ Railway didn't auto-detect the configs

**Fix:** Manually added start command in Railway dashboard

---

### Issue 2: Python 3.12 Incompatibility ❌

**Error:**
```
ERROR: Could not find a version that satisfies the requirement faiss-cpu==1.7.4
```

**Root Cause:** Railway uses Python 3.12, but `faiss-cpu==1.7.4` only supports Python 3.7-3.10

**Fix:**
```diff
- faiss-cpu==1.7.4
+ faiss-cpu>=1.8.0
```

---

### Issue 3: Build Timeout (10+ minutes) ❌

**Error:**
```
Build timed out
```

**Root Cause:** PyTorch GPU version (4GB) took too long to download and install

**Fix:** Switched to CPU-only PyTorch
```python
# Updated requirements.txt
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.5.0+cpu
torchvision==0.20.0+cpu
```

**Result:** Build time reduced from 10+ min to ~7 min ✅

---

### Issue 4: Directory Structure - "backend" Not Found ❌

**Error:**
```bash
/bin/bash: line 1: cd: backend: No such file or directory
```

**Attempts:**

1. **Attempt 1:** Use `cd backend` in start command
   ```bash
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   ❌ Failed - `backend/` directory doesn't exist in container

2. **Attempt 2:** Use Python module path
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
   ❌ Failed - `ModuleNotFoundError: No module named 'backend'`

3. **Attempt 3:** Add PYTHONPATH
   ```bash
   cd /app && PYTHONPATH=/app uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
   ❌ Failed - Still can't find 'backend' module

4. **Attempt 4:** Add `backend/__init__.py` to make it a package
   ```bash
   touch backend/__init__.py
   ```
   ❌ Failed - Module still not found

5. **Attempt 5 (Current):** Set Railway Root Directory to `backend`
   - Railway Settings → Root Directory: `backend`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - ❌ **STILL FAILING** - Getting `ModuleNotFoundError: No module named 'backend'`

---

## Current Railway Configuration

### Railway Dashboard Settings:
```yaml
Root Directory: backend
Custom Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Builder: Nixpacks
Port: 8000
Region: Southeast Asia (Singapore)
```

### Files in Repository:
- ✅ `Procfile`
- ✅ `railway.json`
- ✅ `nixpacks.toml`
- ✅ `requirements.txt` (root and backend/)
- ✅ `backend/__init__.py`

---

## The Problem

Railway's Docker container structure is inconsistent:
1. During **build phase**: Railway copies everything to `/app/`
2. During **runtime**: The module paths are broken
3. The `backend/` directory either:
   - Doesn't exist as a subdirectory, OR
   - Exists but isn't in Python's module search path

**Current Error:**
```
ModuleNotFoundError: No module named 'backend'
```

This suggests Railway is still trying to import `backend.app.main` even though we changed the root directory and start command.

---

## Files Modified

### 1. `requirements.txt` (backend/)
```python
# Updated for Python 3.12 compatibility
faiss-cpu>=1.8.0  # Changed from ==1.7.4

# CPU-only PyTorch for faster builds
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.5.0+cpu
torchvision==0.20.0+cpu
```

### 2. `backend/app/main.py`
```python
# Added Netlify CORS
allow_origins=[
    # ... local origins
    "https://timely-tulumba-ac41cb.netlify.app",  # Production
]
```

### 3. `frontend/src/api/client.ts`
```typescript
// Use environment variable for API URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
```

### 4. `netlify.toml`
```toml
[build]
  base = "frontend"
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## Netlify Configuration

### Status: ⏸️ Waiting for Backend

**Frontend URL:** https://timely-tulumba-ac41cb.netlify.app

**Environment Variable Needed:**
```
VITE_API_BASE_URL=https://hospitalcanvas-production.up.railway.app/api
```

**CORS Already Updated:** Backend allows requests from Netlify domain ✅

---

## Next Steps / Potential Solutions

### Option A: Debug Railway Container
1. Use Railway's shell access to inspect the container
2. Check actual directory structure
3. Verify where files are actually located

### Option B: Switch to Render.com
Railway is being difficult. Render.com might be easier:
- Longer build timeout (15 min vs 10 min)
- Better support for subdirectory projects
- Simpler configuration

### Option C: Restructure Project
Move everything from `backend/` to root:
```
datamicron-assessment/
├── app/              # Move from backend/app/
├── data/             # Move from backend/data/
├── indexes/          # Move from backend/indexes/
├── requirements.txt  # Already exists
└── frontend/         # Keep as is
```

Then use simple start command: `uvicorn app.main:app`

---

## Environment Variables

### Backend (Railway):
```bash
OPENAI_API_KEY=sk-proj-...
EXA_API_KEY=498370d1-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4-turbo-preview
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
PORT=8000
```

### Frontend (Netlify):
```bash
VITE_API_BASE_URL=https://hospitalcanvas-production.up.railway.app/api
```

---

## Lessons Learned

1. **Railway + subdirectories = pain** 🤕
   - Railway expects apps at root level
   - Subdirectory support is inconsistent

2. **Always use CPU-only ML libraries for deployment**
   - GPU versions are 5x larger
   - Free tier has limited build time

3. **Test deployment early**
   - Don't wait until the end to deploy
   - Deployment issues can be complex

4. **Platform-specific quirks exist**
   - What works locally may not work on platform
   - Each platform (Railway, Render, Heroku) has different requirements

---

## Time Spent

- Setting up deployment configs: 30 min
- Debugging Railway issues: 2+ hours
- Still not deployed: 🤦‍♂️

---

## Deployment URLs

- **Frontend (Netlify):** https://timely-tulumba-ac41cb.netlify.app ⏸️ Waiting
- **Backend (Railway):** https://hospitalcanvas-production.up.railway.app ❌ Failing

---

## Status: BLOCKED

Need to either:
1. Figure out Railway's exact directory structure
2. Switch to Render.com
3. Restructure the entire project

**Current recommendation:** Try Render.com - it's designed for Python apps with better subdirectory support.
