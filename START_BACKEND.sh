#!/bin/bash

# Datamicron AI News Assistant - Backend Startup Script

echo "=========================================="
echo "Datamicron AI News Assistant - Backend"
echo "=========================================="
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup first:"
    echo "  cd backend"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env from .env.example and add your OpenAI API key"
    exit 1
fi

# Check if indexes exist
if [ ! -d "indexes" ] || [ ! -f "indexes/faiss.index" ]; then
    echo "⚠️  Indexes not found! Building indexes..."
    echo "This will take 2-3 minutes and make ~90 OpenAI API calls (~$0.01)"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python build_indexes.py
    else
        echo "❌ Indexes are required to run the server. Exiting."
        exit 1
    fi
fi

# Start server
echo ""
echo "🚀 Starting backend server on http://localhost:8000"
echo "📚 API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python run_server.py
