# VulnAI X - Standalone Autonomous Worker Script
# Runs the polling worker loop with crash recovery and heartbeat monitoring.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "     VulnAI X Autonomous Research Worker Loop     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\backend"

& "$root\.venv\Scripts\python.exe" -m app.worker.worker
