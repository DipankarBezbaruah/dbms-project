@echo off
title HostelOut Demo Launcher
echo ========================================================
echo   Starting HostelOut Prototype (Backend + Frontend)
echo ========================================================

echo.
echo [1/2] Starting Flask Backend on http://localhost:5000...
start "HostelOut Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python app.py"

echo [2/2] Starting Vite Frontend on http://localhost:5173...
start "HostelOut Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are starting up in separate windows!
echo Once Vite is ready, open your browser at: http://localhost:5173
echo.
pause
