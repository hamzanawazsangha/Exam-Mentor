# CSS/PMS Exam Preparation Portal - Run Script (Windows PowerShell)

Write-Host "=================================="  -ForegroundColor Cyan
Write-Host "CSS/PMS Exam Preparation Portal"   -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if venv exists
$venvPath = Join-Path $scriptDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Set OpenAI API key from .env
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    $content = Get-Content $envFile | Select-String "OPENAI_API_KEY"
    if ($content) {
        $key = $content -replace 'OPENAI_API_KEY=', ''
        $env:OPENAI_API_KEY = $key
        Write-Host "[OK] OpenAI API key loaded from .env" -ForegroundColor Green
    }
}

# Navigate to backend
Push-Location (Join-Path $scriptDir "backend")

# Display startup information
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Starting Flask Server..."         -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server running at:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:5000 (Home)" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:5000/dashboard (Dashboard)" -ForegroundColor Yellow
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Green
Write-Host "  POST   /api/auth/register" -ForegroundColor Yellow
Write-Host "  POST   /api/auth/login" -ForegroundColor Yellow
Write-Host "  GET    /api/dashboard/metrics/<user_id>" -ForegroundColor Yellow
Write-Host "  POST   /api/preparation/select-exam" -ForegroundColor Yellow
Write-Host "  POST   /api/preparation/generate-paper/<user_id>/<subject_id>" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Start Flask server
python main.py

# Return to original location
Pop-Location
