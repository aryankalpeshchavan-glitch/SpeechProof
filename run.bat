@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo        SpeechProof — Automated Judge Launch Script
echo ========================================================
echo.

:: 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ and ensure 'Add to PATH' is checked.
    pause
    exit /b 1
)

:: 2. Check / Create Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [1/5] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

:: 3. Install Python Dependencies
echo [2/5] Checking and installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Pip install had issues, continuing...
)

:: 4. Check Whisper Model Cache
if not exist "model_cache\models--Systran--faster-whisper-large-v3" (
    echo [3/5] Downloading offline Whisper large-v3 model to ./model_cache...
    python -m speechproof.asr --prepare-model
) else (
    echo [3/5] Whisper large-v3 model cache detected.
)

:: 5. Check Frontend Build
if not exist "web\dist\index.html" (
    echo [4/5] Building React 19 frontend bundle...
    where npm >nul 2>nul
    if %errorlevel% equ 0 (
        cd web
        call npm install
        call npm run build
        cd ..
    ) else (
        echo [WARNING] npm not found; will fallback to static assets.
    )
) else (
    echo [4/5] Frontend build already present in web\dist.
)

:: 6. Launch Server & Open Browser
echo [5/5] Launching SpeechProof server at http://localhost:8000 ...
echo.
echo ========================================================
echo Application URL : http://localhost:8000
echo API Docs (Swagger): http://localhost:8000/docs
echo Press Ctrl+C in this terminal to stop the server.
echo ========================================================
echo.

start "" "http://localhost:8000"
python -m uvicorn sp_platform.api:app --host 127.0.0.1 --port 8000

pause
