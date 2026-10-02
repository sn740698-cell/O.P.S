# O.P.S. Ambient AI Launcher (PowerShell)
$ErrorActionPreference = "SilentlyContinue"
$ROOT_DIR = $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Green
Write-Host "          O.P.S. (Over-Engineered Programmed System)                   " -ForegroundColor Green
Write-Host "        Local-First AI Operating System - Environment Launcher         " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""

# 0. Check & Start PostgreSQL 18
$pgListening = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue
if (-not $pgListening) {
    Write-Host "[0/4] Starting PostgreSQL 18 Engine (Port 5432)..." -ForegroundColor Yellow
    Start-Process -FilePath "D:\Program Files\program Files (postgreSQL)\18\bin\postgres.exe" -ArgumentList "-D `"D:\Program Files\program Files (postgreSQL)\18\data`"" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# 1. Start Django Backend Engine
Write-Host "[1/4] Starting Django Backend Engine (Port 8000)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ROOT_DIR\backend`" && call .\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"

# 2. Start React Desktop Dashboard
Write-Host "[2/4] Starting React Desktop Dashboard (Vite)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ROOT_DIR\frontend`" && npm run dev"

# 3. Start Desktop Overlay Daemon
Write-Host "[3/4] Starting System-Wide Desktop Overlay Daemon..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ROOT_DIR`" && call .\backend\venv\Scripts\activate.bat && python local_agent\desktop_overlay.py"

# 4. Wait & Open Browser
Write-Host "[4/4] Waiting for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Opening O.P.S. Ambient Overlay Dashboard in default browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " O.P.S. System-Wide Ambient Engine is ACTIVE EVERYWHERE!" -ForegroundColor Green
Write-Host " Press Ctrl+Alt anywhere to bring up the O.P.S. System-Wide Cockpit!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
