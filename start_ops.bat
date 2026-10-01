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

echo [1/3] Starting Django Backend Engine (Port 8000)...
start /min "O.P.S Backend (Django)" cmd /c "cd /d %ROOT_DIR%backend && call .\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"

echo [2/3] Starting React Desktop Dashboard (Vite)...
start /min "O.P.S Frontend (Vite)" cmd /c "cd /d %ROOT_DIR%frontend && npm run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening O.P.S. Ambient Overlay Dashboard in default browser...
start http://localhost:3000

echo.
echo ======================================================================
echo  O.P.S. is now running in the BACKGROUND! 
echo  Press Ctrl+Windows anytime and say "Hey OPS" to bring up pop-up face.
echo ======================================================================
echo.
timeout /t 3 /nobreak >nul
exit

:BACKGROUND_MODE
start /min "O.P.S Backend (Django)" cmd /c "cd /d %ROOT_DIR%backend && call .\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"
start /min "O.P.S Frontend (Vite)" cmd /c "cd /d %ROOT_DIR%frontend && npm run dev"
timeout /t 4 /nobreak >nul
start http://localhost:3000
exit
