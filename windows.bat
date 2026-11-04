@echo off
TITLE O.P.S. 2.0 - System Launcher
COLOR 0A
CLS

SET "ROOT_DIR=%~dp0"
CD /D "%ROOT_DIR%"

echo ======================================================================
echo           O.P.S. 2.0 [Over-Engineered Programmed System]              
echo      Unified Launcher: LangGraph Web Research ^& Cockpit UI            
echo ======================================================================
echo.

:: ----------------------------------------------------------------------
:: 0. Check Core Prerequisites (Python & Node.js)
:: ----------------------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on your system PATH!
    echo Please install Python 3.11+ and ensure 'Add to PATH' is checked.
    echo.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js / npm was not found on your system PATH!
    echo Please install Node.js and ensure npm is added to your PATH.
    echo.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------------
:: 1. Check Ollama Local Model Server (Port 11434)
:: ----------------------------------------------------------------------
echo [1/4] Verifying Ollama Engine...
curl.exe -s http://127.0.0.1:11434/ >nul 2>&1
if not errorlevel 1 (
    echo       Ollama server is active on http://127.0.0.1:11434
) else (
    echo       Ollama not detected on port 11434. Attempting to start Ollama...
    where ollama >nul 2>&1
    if not errorlevel 1 (
        start "Ollama Engine" /min ollama serve
        ping 127.0.0.1 -n 4 >nul
    ) else (
        echo       [WARN] Ollama command not found on PATH. Ensure Ollama is running.
    )
)

:: ----------------------------------------------------------------------
:: 2. Check Database Service (PostgreSQL 18 / SQLite Fallback)
:: ----------------------------------------------------------------------
echo [2/4] Verifying Database Layer...
netstat -ano | findstr :5432 >nul 2>&1
if not errorlevel 1 (
    echo       PostgreSQL service is active on port 5432.
) else (
    echo       PostgreSQL service not active. Backend will use SQLite WAL fallback: ops2_research.sqlite3.
)

:: ----------------------------------------------------------------------
:: 3. Launch Django LangGraph Backend (Port 8000)
:: ----------------------------------------------------------------------
echo [3/4] Launching O.P.S. 2.0 Backend: Django + LangGraph Engine...
curl.exe -s http://127.0.0.1:8000/api/health/ >nul 2>&1
if not errorlevel 1 (
    echo       Django backend is already running on http://127.0.0.1:8000
) else (
    pushd "%ROOT_DIR%backend"
    if exist "venv\Scripts\activate.bat" (
        start "O.P.S 2.0 Backend - Django LangGraph" cmd /k "call venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"
    ) else (
        start "O.P.S 2.0 Backend - Django LangGraph" cmd /k "python manage.py runserver 0.0.0.0:8000"
    )
    popd
)

:: ----------------------------------------------------------------------
:: 4. Launch React Cockpit Frontend (Vite Port 3000)
:: ----------------------------------------------------------------------
echo [4/4] Launching O.P.S. 2.0 Cockpit Frontend: Vite...
curl.exe -s http://localhost:3000/ >nul 2>&1
if not errorlevel 1 (
    echo       Vite frontend is already running on http://localhost:3000
) else (
    pushd "%ROOT_DIR%frontend"
    start "O.P.S 2.0 Frontend - Vite Cockpit" cmd /k "npm run dev"
    popd
)

:: ----------------------------------------------------------------------
:: 5. Launch Main Browser Application & Native Desktop Cockpit Overlay
:: ----------------------------------------------------------------------
echo [5/5] Launching Browser Application ^& Native Cockpit Overlay...
echo Waiting for backend and frontend services to be ready...

set WAIT_COUNT=0
:WAIT_LOOP
set /a WAIT_COUNT+=1
if %WAIT_COUNT% gtr 30 goto TIMEOUT_CHECK

curl.exe -s http://127.0.0.1:8000/api/health/ >nul 2>&1
if errorlevel 1 (
    ping 127.0.0.1 -n 2 >nul
    goto WAIT_LOOP
)

curl.exe -s http://localhost:3000/ >nul 2>&1
if errorlevel 1 (
    ping 127.0.0.1 -n 2 >nul
    goto WAIT_LOOP
)

goto READY_NOW

:TIMEOUT_CHECK
echo.
echo [WARNING] One or more services took longer than 30 seconds to respond:
curl.exe -s http://127.0.0.1:8000/api/health/ >nul 2>&1
if errorlevel 1 (
    echo   - Backend (Port 8000): NOT RESPONDING yet. (Check backend console window)
) else (
    echo   - Backend (Port 8000): ONLINE
)
curl.exe -s http://localhost:3000/ >nul 2>&1
if errorlevel 1 (
    echo   - Frontend (Port 3000): NOT RESPONDING yet. (Check frontend console window)
) else (
    echo   - Frontend (Port 3000): ONLINE
)
echo Proceeding with launch...
goto LAUNCH_TARGETS

:READY_NOW
echo       Services initialized and responding!
ping 127.0.0.1 -n 2 >nul

:LAUNCH_TARGETS
:: Launch Main Application in Default Web Browser (Full Dashboard & Management)
start "" "http://localhost:3000"

:: Launch Separate Pop-up Cockpit as Native Desktop Overlay Window
start "O.P.S 2.0 Desktop Cockpit Overlay" cmd /k "python -m desktop_overlay.main --frontend-url http://localhost:3000/?mode=cockpit"

echo.
echo ======================================================================
echo  O.P.S. 2.0 SYSTEM CONNECTED AND ONLINE!                              
echo  ------------------------------------------------------------------   
echo  - Main Web Application : http://localhost:3000 (Full Dashboard)      
echo  - Desktop Cockpit HUD  : Floating Overlay (mode=cockpit)             
echo  - Open Cockpit Overlay  : [ Ctrl + Alt ]
echo  - Close Cockpit Overlay : [ Ctrl + Alt + Space ]
echo  - Backend LangGraph API: http://localhost:8000                       
echo  - Real-time Events     : Server-Sent Events (SSE)                    
echo ======================================================================
echo.
echo Leave the background terminal windows open while working.
echo.
pause
