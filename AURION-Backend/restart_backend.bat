@echo off
echo ========================================
echo   AURION Backend - Quick Restart
echo ========================================
echo.
echo Stopping any existing backend processes...
taskkill /F /IM uvicorn.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting AURION backend with enhanced logging...
echo.
echo Backend will be available at: http://127.0.0.1:8000
echo Frontend should be at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the backend
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
