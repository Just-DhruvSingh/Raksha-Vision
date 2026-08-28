#!/bin/bash

# ==============================================================================
# RakshaVision AI — Hackathon Prototype Launcher for macOS/Linux (SIH26187)
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================================================="
echo "       RAKSHAVISION AI — EDGE PERIMETER DEFENSE SYSTEM (SIH26187)"
echo "=============================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed. Please install Python 3.10+."
    exit 1
fi

# 2. Check Node
if ! command -v node &> /dev/null; then
    echo "[ERROR] node is not installed. Please install Node.js 18+."
    exit 1
fi

# 3. Setup & Run Backend
echo "[1/3] Setting up FastAPI + YOLOv8 Backend..."
cd "$PROJECT_ROOT/backend"

if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment (.venv)..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

echo "[INFO] Starting Backend Server on http://127.0.0.1:8000..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 4. Setup & Run Frontend
echo "[2/3] Setting up React + Vite Frontend..."
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo "[INFO] Installing npm packages..."
    npm install
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

echo "[INFO] Starting Frontend Dev Server on http://localhost:5173..."
npm run dev &
FRONTEND_PID=$!

# 5. Open Browser
sleep 3
echo "[3/3] Opening Surveillance Dashboard in browser..."
if which xdg-open > /dev/null; then
    xdg-open http://localhost:5173
elif which open > /dev/null; then
    open http://localhost:5173
fi

echo ""
echo "=============================================================================="
echo "[SUCCESS] RakshaVision AI is running!"
echo "  * Frontend Dashboard:   http://localhost:5173"
echo "  * Interactive Swagger:  http://localhost:8000/docs"
echo "  * Press Ctrl+C in this terminal to stop all servers."
echo "=============================================================================="

# Trap SIGINT to kill background servers gracefully
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT
wait
