# VulnAI X - Windows Setup Script
# Installs backend virtualenv, Python dependencies, and frontend packages.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       VulnAI X - Automated Windows Setup         " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Python & Node
Write-Host "`n[*] Checking system prerequisites..." -ForegroundColor Yellow
if (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "[+] Found Python Launcher (py)" -ForegroundColor Green
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[+] Found Python (python)" -ForegroundColor Green
} else {
    Write-Error "Python is not installed. Please install Python 3.11+."
}

if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVer = node --version
    Write-Host "[+] Found Node.js: $nodeVer" -ForegroundColor Green
} else {
    Write-Error "Node.js is not installed. Please install Node.js 18+."
}

# 2. Setup Virtual Environment
Write-Host "`n[*] Configuring Python virtual environment..." -ForegroundColor Yellow
if (!(Test-Path ".venv")) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv .venv
    } else {
        py -3.11 -m venv .venv
    }
    Write-Host "[+] Created virtual environment at .venv" -ForegroundColor Green
} else {
    Write-Host "[+] Virtual environment already exists." -ForegroundColor Green
}

# 3. Install Backend Dependencies
Write-Host "`n[*] Installing backend security dependencies..." -ForegroundColor Yellow
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install -r backend/requirements.txt --python .\.venv\Scripts\python.exe
} else {
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
}
Write-Host "[+] Backend dependencies installed." -ForegroundColor Green

# 4. Install Frontend Dependencies
Write-Host "`n[*] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install --no-audit --no-fund
Pop-Location
Write-Host "[+] Frontend packages installed." -ForegroundColor Green

# 5. Initialize Database & Seed Default Admin
Write-Host "`n[*] Initializing database and default authorized programs..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -c "from app.main import app; print('[+] Database initialized.')"
Write-Host "[+] Seeded initial admin account: admin / VulnAI-X-Admin-2026!" -ForegroundColor Green

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " Setup complete! Run .\scripts\run-windows.ps1 to start." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
