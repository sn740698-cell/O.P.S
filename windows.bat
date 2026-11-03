@echo off
TITLE O.P.S. 2.0 - System Launcher
COLOR 0A
CLS

SET "ROOT_DIR=%~dp0"
CD /D "%ROOT_DIR%"

echo ======================================================================
echo           O.P.S. 2.0 [Over-Engineered Programmed System]              
echo      Unified Launcher: LangGraph Web Research & Cockpit UI            
echo ======================================================================
echo.

:: ----------------------------------------------------------------------
:: 1. Check Ollama Local Model Server (Port 11434)
:: ----------------------------------------------------------------------
echo [1/4] Verifying Ollama Engine...
netstat -ano | findstr :11434 >nul
if not errorlevel 1 (
    echo       Ollama server is active on http://127.0.0.1:11434
) else (
    echo       Ollama not detected on port 11434. Attempting to start Ollama...
    where ollama >nul 2>&1
    if not errorlevel 1 (
        start "Ollama Engine" /min ollama serve
        timeout /t 3 /nobreak >nul
    ) else (
        echo       [WARN] Ollama command not found on PATH. Ensure Ollama is running.
    )
)

:: ----------------------------------------------------------------------
:: 2. Check Database Service (PostgreSQL 18 / SQLite Fallback)
:: ----------------------------------------------------------------------
echo [2/4] Verifying Database Layer...
netstat -ano | findstr :5432 >nul
if not errorlevel 1 (
    echo       PostgreSQL service is active on port 5432.
) else (
    if exist "D:\Program Files\program Files (postgreSQL)\18\bin\postgres.exe" (
        echo       Launching PostgreSQL 18 background engine...
        start "O.P.S PostgreSQL" /min "D:\Program Files\program Files (postgreSQL)\18\bin\postgres.exe" -D "D:\Program Files\program Files (postgreSQL)\18\data"
        timeout /t 2 /nobreak >nul
    ) else (
        echo       PostgreSQL not detected. Backend will use SQLite WAL fallback.
    )
)

:: ----------------------------------------------------------------------
:: 3. Launch Django LangGraph Backend (Port 8000)
:: ----------------------------------------------------------------------
echo [3/4] Launching O.P.S. 2.0 Backend (Django + LangGraph Engine)...
netstat -ano | findstr :8000 >nul
if not errorlevel 1 (
    echo       Django backend is already running on http://127.0.0.1:8000
) else (
    if exist "%ROOT_DIR%backend\venv\Scripts\activate.bat" (
        start "O.P.S 2.0 Backend (Django + LangGraph)" cmd /k "cd /d "%ROOT_DIR%backend" && call "%ROOT_DIR%backend\venv\Scripts\activate.bat" && python manage.py runserver 0.0.0.0:8000"
    ) else (
        start "O.P.S 2.0 Backend (Django + LangGraph)" cmd /k "cd /d "%ROOT_DIR%backend" && python manage.py runserver 0.0.0.0:8000"
    )
)

:: ----------------------------------------------------------------------
:: 4. Launch React Cockpit Frontend (Vite Port 3000)
:: ----------------------------------------------------------------------
echo [4/4] Launching O.P.S. 2.0 Cockpit Frontend (Vite)...
netstat -ano | findstr :3000 >nul
if not errorlevel 1 (
    echo       Vite frontend is already running on http://localhost:3000
) else (
    start "O.P.S 2.0 Frontend (Vite Cockpit)" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"
)

:: ----------------------------------------------------------------------
:: 5. Launch Main Browser Application & Native Desktop Cockpit Overlay
:: ----------------------------------------------------------------------
echo [5/5] Launching Browser Application & Native Cockpit Overlay...
echo Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

:: Launch Main Application in Default Web Browser (Full Dashboard & Management)
start http://localhost:3000

:: Launch Separate Pop-up Cockpit as Native Desktop Overlay Window
start "O.P.S 2.0 Desktop Cockpit Overlay" python -m desktop_overlay.main --frontend-url "http://localhost:3000/?mode=cockpit"

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
