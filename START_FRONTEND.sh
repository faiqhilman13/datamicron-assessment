#!/bin/bash

# Datamicron AI News Assistant - Frontend Startup Script

echo "=========================================="
echo "Datamicron AI News Assistant - Frontend"
echo "=========================================="
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start development server
echo ""
echo "🚀 Starting frontend development server"
echo "🌐 Application will be available at http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
