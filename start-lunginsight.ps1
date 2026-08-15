# LungInsight AI — starts all 4 services in separate windows, one command.
#
# Usage: from D:\Internship\LungInsight, run:  .\start-lunginsight.ps1
#
# Requires (same as manual setup):
#   - PostgreSQL already running as a Windows service
#   - Each module's venv already created with dependencies installed
#   - Each module's .env file already filled in

$root = "D:\Internship\LungInsight"

function Start-Service-Window {
    param(
        [string]$Title,
        [string]$WorkDir,
        [string]$Command
    )
    Write-Host "Starting $Title..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkDir'; `$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
    Start-Sleep -Seconds 2
}

# 1. Check Postgres is running first — nothing else works without it
$pg = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if (-not $pg -or $pg.Status -ne "Running") {
    Write-Host "WARNING: PostgreSQL service is not running. Starting it..." -ForegroundColor Yellow
    if ($pg) { Start-Service $pg.Name }
    Start-Sleep -Seconds 3
}

# 2. AI model-serving service (port 8500)
Start-Service-Window -Title "LungInsight - AI Service (8500)" `
    -WorkDir "$root\LungInsight-AI" `
    -Command ".\venv\Scripts\Activate; uvicorn service.main:app --host 0.0.0.0 --port 8500"

# 3. RAG chat service (port 8600)
Start-Service-Window -Title "LungInsight - RAG Service (8600)" `
    -WorkDir "$root\lunginsight-rag" `
    -Command ".\venv\Scripts\Activate; uvicorn api:app --host 0.0.0.0 --port 8600"

# 4. Backend (port 8000) — started last of the Python services since it
#    calls the two above at request time, not at startup, so order isn't
#    strictly required, but this keeps logs easier to read as they start.
Start-Service-Window -Title "LungInsight - Backend (8000)" `
    -WorkDir "$root\LungInsight-Backend" `
    -Command ".\venv\Scripts\Activate; uvicorn app.main:app --host 0.0.0.0 --port 8000"

# 5. Frontend (port 5173)
Start-Service-Window -Title "LungInsight - Frontend (5173)" `
    -WorkDir "$root\LungInsight-Frontend" `
    -Command "npm run dev"

Write-Host ""
Write-Host "All 4 services launching in separate windows." -ForegroundColor Green
Write-Host "Give the AI and RAG services 10-20 seconds to finish loading their models before using the app." -ForegroundColor Yellow
Write-Host "Frontend will be at http://localhost:5173" -ForegroundColor Green
