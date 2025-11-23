# Deployment Guide

This guide will help you deploy the Datamicron AI News Assistant to production.

## Architecture

- **Frontend**: React + Vite (Deploy to Netlify/Vercel)
- **Backend**: FastAPI + Python (Deploy to Railway/Render/Heroku)

---

## Option 1: Deploy Backend to Railway (Recommended)

Railway is free for hobbyists and easy to set up.

### Step 1: Deploy Backend to Railway

1. Go to [Railway.app](https://railway.app/) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `datamicron-assessment` repository
4. Railway will auto-detect the Python app

### Step 2: Configure Backend Environment Variables

In Railway dashboard, add these environment variables:

```
OPENAI_API_KEY=your-openai-api-key-here
EXA_API_KEY=your-exa-api-key-here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4-turbo-preview
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
PORT=8000
```

**Note**: Replace `your-openai-api-key-here` with your actual OpenAI API key from https://platform.openai.com/api-keys

### Step 3: Add Railway Configuration

Create `railway.json` in the backend directory (already configured):

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Get Your Backend URL

After deployment, Railway will give you a URL like:
`https://your-app-name.up.railway.app`

---

## Option 2: Deploy Backend to Render

1. Go to [Render.com](https://render.com/) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: datamicron-backend
   - **Root Directory**: backend
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)

---

## Deploy Frontend to Netlify

### Step 1: Build Configuration

Create `netlify.toml` in the root directory:

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

### Step 2: Deploy to Netlify

1. Go to [Netlify.com](https://www.netlify.com/) and sign up
2. Click "Add new site" → "Import an existing project"
3. Connect your GitHub repository
4. Netlify will auto-detect the build settings

### Step 3: Configure Frontend Environment Variables

In Netlify dashboard → Site settings → Environment variables, add:

```
VITE_API_BASE_URL=https://your-backend-url.up.railway.app/api
```

Replace `your-backend-url.up.railway.app` with your actual backend URL from Railway/Render.

### Step 4: Enable CORS on Backend

Make sure your backend (`app/main.py`) has CORS configured to allow your Netlify domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://your-netlify-site.netlify.app"  # Add your Netlify URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Alternative: Deploy Frontend to Vercel

1. Go to [Vercel.com](https://vercel.com/) and sign up
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: frontend
   - **Build Command**: `npm run build`
   - **Output Directory**: dist
5. Add environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend-url.up.railway.app/api
   ```

---

## Important Notes

### Backend Files

Make sure these files exist in your `backend/` directory:
- `requirements.txt` - Python dependencies
- `data/news.csv` - Your news dataset
- `indexes/` - Pre-built FAISS/BM25 indexes

### Build Indexes Before Deployment

If indexes don't exist, run locally before deploying:

```bash
cd backend
python build_indexes.py
```

Then commit the `indexes/` folder to Git.

### Environment Variables Security

**IMPORTANT**: Never commit `.env` files to Git. Use:
- Railway/Render dashboard for backend env vars
- Netlify/Vercel dashboard for frontend env vars

---

## Testing Your Deployment

1. **Test Backend**:
   ```bash
   curl https://your-backend-url.up.railway.app/api/health
   ```

2. **Test Frontend**:
   Open your Netlify/Vercel URL in browser

3. **Check CORS**:
   - Open browser console
   - Try sending a query
   - Should see no CORS errors

---

## Troubleshooting

### Backend won't start
- Check Railway/Render logs
- Verify all environment variables are set
- Ensure `indexes/` folder is in Git

### Frontend can't connect to backend
- Check `VITE_API_BASE_URL` is set correctly
- Verify CORS is configured
- Check network tab in browser dev tools

### FAISS/ML models failing
- These libraries need system dependencies
- Railway/Render should handle automatically
- If issues, try deploying to Docker-based platform

---

## Cost Estimates

- **Railway**: Free tier (500 hours/month)
- **Render**: Free tier with limitations
- **Netlify**: Free tier (100GB bandwidth)
- **Vercel**: Free tier (100GB bandwidth)

Total: **$0/month** on free tiers!
