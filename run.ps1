# SpeechProof — 1-Click Launch Script for PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       SpeechProof — Automated Judge Launch Script       " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# 2. Check/Create Venv
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[1/5] Creating Python virtual environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
}

& ".\venv\Scripts\Activate.ps1"

# 3. Install Python Dependencies
Write-Host "[2/5] Checking and installing Python dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 4. Check Whisper Model Cache
if (-not (Test-Path "model_cache\models--Systran--faster-whisper-large-v3")) {
    Write-Host "[3/5] Downloading offline Whisper large-v3 model to ./model_cache..." -ForegroundColor Yellow
    python -m speechproof.asr --prepare-model
} else {
    Write-Host "[3/5] Whisper large-v3 model cache detected." -ForegroundColor Green
}

# 5. Check Frontend Build
if (-not (Test-Path "web\dist\index.html")) {
    Write-Host "[4/5] Building React 19 frontend bundle..." -ForegroundColor Yellow
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Push-Location web
        npm install
        npm run build
        Pop-Location
    }
} else {
    Write-Host "[4/5] Frontend build already present in web\dist." -ForegroundColor Green
}

# 6. Launch Server & Open Browser
Write-Host "[5/5] Launching SpeechProof server at http://localhost:8000 ..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Application URL : http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs (Swagger): http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:8000"
python -m uvicorn sp_platform.api:app --host 127.0.0.1 --port 8000
