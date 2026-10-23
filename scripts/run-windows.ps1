# VulnAI X - Windows Local Development Runner
# Launches FastAPI backend on port 8000 and Vite frontend on port 5173.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       Launching VulnAI X Platform (Windows)      " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$root = Split-Path -Parent $PSScriptRoot

# 1. Start FastAPI Backend in background job
Write-Host "[*] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
$backendJob = Start-Process -FilePath "$root\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" `
    -WorkingDirectory "$root\backend" `
    -PassThru

# 2. Start Autonomous Background Worker in background job
Write-Host "[*] Starting Autonomous Background Worker..." -ForegroundColor Green
$workerJob = Start-Process -FilePath "$root\.venv\Scripts\python.exe" `
    -ArgumentList "-m app.worker.worker" `
    -WorkingDirectory "$root\backend" `
    -PassThru

# 3. Start Frontend Dev Server
Write-Host "[*] Starting Vite React Frontend on http://localhost:5173 ..." -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop all servers.`n" -ForegroundColor Yellow

try {
    Set-Location "$root\frontend"
    npm run dev
} finally {
    Write-Host "`n[*] Stopping backend and worker processes..." -ForegroundColor Yellow
    if ($backendJob -and !$backendJob.HasExited) { Stop-Process -Id $backendJob.Id -Force }
    if ($workerJob -and !$workerJob.HasExited) { Stop-Process -Id $workerJob.Id -Force }
    Write-Host "[+] All servers stopped." -ForegroundColor Green
}
