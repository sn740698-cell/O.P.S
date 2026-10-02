@echo off
TITLE O.P.S. Ambient AI Launcher
COLOR 0A
CLS

SET ROOT_DIR=%~dp0

if "%1"=="/background" goto BACKGROUND_MODE

echo ======================================================================
echo           O.P.S. (Over-Engineered Programmed System)                   
echo         Local-First AI Operating System - Environment Launcher       
echo ======================================================================
echo.

netstat -ano | findstr 127.0.0.1:5432 >nul
if errorlevel 1 (
    echo [0/4] Starting PostgreSQL 18 Engine (Port 5432)...
    start "O.P.S PostgreSQL" /min "D:\Program Files\program Files (postgreSQL)\18\bin\postgres.exe" -D "D:\Program Files\program Files (postgreSQL)\18\data"
    ping 127.0.0.1 -n 3 >nul
)

echo [1/4] Starting Django Backend Engine (Port 8000)...
start "O.P.S Backend (Django)" cmd /c "cd /d "%ROOT_DIR%backend" && call .\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"

echo [2/4] Starting React Desktop Dashboard (Vite)...
start "O.P.S Frontend (Vite)" cmd /c "cd /d "%ROOT_DIR%frontend" && npm run dev"

echo [3/4] Starting System-Wide Desktop Overlay Daemon (Works everywhere: WhatsApp, Games, Apps)...
start "O.P.S Desktop Overlay" cmd /c "cd /d "%ROOT_DIR%" && call .\backend\venv\Scripts\activate.bat && python local_agent\desktop_overlay.py"

echo [4/4] Waiting for servers to initialize...
ping 127.0.0.1 -n 4 >nul

echo Opening O.P.S. Ambient Overlay Dashboard in default browser...
start http://localhost:3000

echo.
echo ======================================================================
echo  O.P.S. System-Wide Ambient Engine is ACTIVE EVERYWHERE! 
echo  Press Ctrl+Alt anywhere (over WhatsApp, Chrome, Games, Home Screen)
echo  to bring up the O.P.S. System-Wide Pop-Up Cockpit!
echo ======================================================================

echo.
exit

:BACKGROUND_MODE
netstat -ano | findstr 127.0.0.1:5432 >nul
if errorlevel 1 (
    start "O.P.S PostgreSQL" /min "D:\Program Files\program Files (postgreSQL)\18\bin\postgres.exe" -D "D:\Program Files\program Files (postgreSQL)\18\data"
    ping 127.0.0.1 -n 3 >nul
)
start /min "O.P.S Backend (Django)" cmd /c "cd /d "%ROOT_DIR%backend" && call .\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"
start /min "O.P.S Frontend (Vite)" cmd /c "cd /d "%ROOT_DIR%frontend" && npm run dev"
start "O.P.S Desktop Overlay" cmd /c "cd /d "%ROOT_DIR%" && call .\backend\venv\Scripts\activate.bat && python local_agent\desktop_overlay.py"
ping 127.0.0.1 -n 4 >nul
start http://localhost:3000
exit
