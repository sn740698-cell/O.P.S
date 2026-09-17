@echo off
TITLE O.P.S. Ambient AI Launcher
COLOR 0A
CLS

echo ======================================================================
echo           O.P.S. (Over-Engineered Programmed System)                   
echo         Local-First AI Operating System - Environment Launcher       
echo ======================================================================
echo.

SET ROOT_DIR=%~dp0

echo [1/3] Starting Django Backend Engine (Port 8000)...
start "O.P.S Backend (Django)" cmd /k "cd /d %ROOT_DIR%backend && call .\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"

echo [2/3] Starting React Desktop Dashboard (Vite)...
start "O.P.S Frontend (Vite)" cmd /k "cd /d %ROOT_DIR%frontend && npm run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening O.P.S. Ambient Overlay Dashboard in default browser...
start http://localhost:3000

echo.
echo ======================================================================
echo  O.P.S. is now active! Both Backend & Frontend are running.
echo  Keep the opened terminal windows running in the background.
echo ======================================================================
echo.
pause
