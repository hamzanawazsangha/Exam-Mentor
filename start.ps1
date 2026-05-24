# ============================================================
#  PPSC & CSS AI Portal — One-Click Launch Script
#  Run from e:\css directory: .\start.ps1
# ============================================================

$Host.UI.RawUI.WindowTitle = "PPSC & CSS AI Portal"

Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "   PPSC & CSS AI Portal - Launcher     " -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check if Ollama is installed
if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Ollama is not installed or not on PATH." -ForegroundColor Red
    Write-Host "  Download from: https://ollama.com/download" -ForegroundColor Yellow
    exit 1
}

# 2. Check if mistral model is pulled
Write-Host "[1/3] Checking Mistral model..." -ForegroundColor Yellow
$models = ollama list 2>&1
if ($models -notmatch "mistral") {
    Write-Host "  Mistral not found. Pulling now (this may take a few minutes)..." -ForegroundColor Yellow
    ollama pull mistral
} else {
    Write-Host "  Mistral model ready." -ForegroundColor Green
}

# 3. Start Ollama server in background
Write-Host "[2/3] Starting Ollama server..." -ForegroundColor Yellow
$ollamaProcess = Start-Process "ollama" -ArgumentList "serve" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2
Write-Host "  Ollama running (PID: $($ollamaProcess.Id))" -ForegroundColor Green

# 4. Check OpenAI API Key (for Expert Mentor chatbot)
Write-Host "[3/3] Checking OpenAI API Key..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "  .env file not found. Expert Mentor chatbot will not work without OPENAI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "  .env file found." -ForegroundColor Green
}

# 5. Start Flask Portal
Write-Host "[4/4] Starting Flask Portal..." -ForegroundColor Yellow
$env:PYTHONPATH = "backend"
Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "  Portal ready at http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop.               " -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

try {
    python backend/main.py
} finally {
    # Cleanup: kill Ollama on exit
    Write-Host "`nShutting down Ollama..." -ForegroundColor Yellow
    Stop-Process -Id $ollamaProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Goodbye." -ForegroundColor Cyan
}
