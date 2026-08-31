@echo off
TITLE RakshaVision AI — Edge Defense Launcher (SIH26187)
COLOR 0A

echo ==============================================================================
echo        RAKSHAVISION AI — EDGE PERIMETER DEFENSE & ANPR SYSTEM
echo               Smart India Hackathon Prototype (SIH26187)
echo ==============================================================================
echo.

:: 1. Navigate to Project Root
cd /d "%~dp0"

:: 2. Check Python Installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+ and re-run.
    pause
    exit /b 1
)

:: 3. Check Node.js Installation
node --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not found in PATH. Please install Node.js 18+ and re-run.
    pause
    exit /b 1
)

:: 4. Start Backend Server
echo [1/3] Starting FastAPI + YOLOv8 + EasyOCR Backend...
cd backend

IF NOT EXIST ".venv" (
    echo [INFO] Creating Python virtual environment in backend\.venv...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [INFO] Installing backend dependencies...
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

IF NOT EXIST ".env" (
    IF EXIST ".env.example" (
        copy .env.example .env >nul
    )
)

:: Launch FastAPI in a separate command window
start "RakshaVision AI Backend (FastAPI :8000)" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

:: 5. Start Frontend Server
echo [2/3] Starting React + Vite Frontend Dashboard...
cd /d "%~dp0frontend"

IF NOT EXIST "node_modules" (
    echo [INFO] Installing frontend npm packages...
    call npm install
)

IF NOT EXIST ".env" (
    IF EXIST ".env.example" (
        copy .env.example .env >nul
    )
)

:: Launch Vite Dev Server in a separate command window
start "RakshaVision AI Frontend (Vite :5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

:: 6. Launch Browser
echo [3/3] Opening Surveillance Command Center in default browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo ==============================================================================
echo [SUCCESS] RakshaVision AI is live!
echo   * Frontend Dashboard:   http://localhost:5173
echo   * Interactive Swagger:  http://localhost:8000/docs
echo   * Live Webcam Stream:   ws://localhost:8000/ws/live/cam_live
echo ==============================================================================
echo Press any key to exit launcher (Servers will keep running in their windows).
pause >nul
