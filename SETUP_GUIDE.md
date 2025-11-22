# Quick Setup Guide

Follow these steps to get the Datamicron AI News Assistant running on your machine.

## Step-by-Step Instructions

### 1. Prerequisites Check

Make sure you have:
- ✅ Python 3.9 or higher (`python3 --version`)
- ✅ Node.js 18 or higher (`node --version`)
- ✅ OpenAI API key (get from https://platform.openai.com)

### 2. Backend Setup (5 minutes)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Open .env in your text editor and replace:
# OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Build Indexes (2-3 minutes)

**Important**: This step is required before running the server for the first time.

```bash
# Still in backend/ directory with venv activated
python build_indexes.py
```

You should see:
```
Loading news data...
Loaded 90 documents
Creating embeddings for 90 texts...
Building FAISS index...
Building BM25 index...
✓ All indexes built successfully!
```

### 4. Start Backend Server

```bash
# In backend/ directory
python run_server.py
```

Server will start at: http://localhost:8000

You should see:
```
Starting Datamicron AI News Assistant
Loading indexes...
✓ FAISS index loaded
✓ BM25 index loaded
✓ Documents loaded
✓ Application startup complete
```

**Keep this terminal open!**

### 5. Frontend Setup (2 minutes)

Open a **new terminal** window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will start at: http://localhost:5173

### 6. Open the Application

Open your browser and go to: **http://localhost:5173**

You should see the Datamicron AI News Assistant interface with:
- ✅ "All systems operational" in the top right
- ✅ Two tabs: "News Q&A" and "Analytics"

### 7. Test It Out!

Try asking:
- "What are some initiatives launched by MCMC?"
- "How many positive news are there?"

## Troubleshooting

### Problem: "Indexes not found" error

**Solution**: You forgot to build indexes. Run:
```bash
cd backend
source venv/bin/activate  # Activate venv first
python build_indexes.py
```

### Problem: "OPENAI_API_KEY not found"

**Solution**:
1. Make sure you created `.env` file in `backend/` directory
2. Open it and add: `OPENAI_API_KEY=sk-...` (your actual key)

### Problem: Frontend can't connect to backend

**Solution**:
1. Make sure backend is running on http://localhost:8000
2. Check if CORS is enabled (it should be by default)
3. Try restarting both servers

### Problem: "Module not found" errors

**Solution**:
- Backend: Make sure venv is activated before running
- Frontend: Run `npm install` again

## Quick Commands Reference

### Backend
```bash
cd backend
source venv/bin/activate  # Activate venv
python build_indexes.py   # Build indexes (first time only)
python run_server.py      # Start server
```

### Frontend
```bash
cd frontend
npm run dev              # Start dev server
npm run build            # Build for production
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API docs at http://localhost:8000/docs
- Try the test questions from the assessment
- Check out the evaluation & improvement strategies

## Need Help?

Check the main README.md for:
- Architecture details
- API endpoint documentation
- Evaluation methods
- Improvement strategies

---

**Estimated Total Setup Time**: ~10 minutes

**Estimated Cost**: ~$0.01 for building indexes (one-time)
