@echo off
echo ================================================
echo   AURION Backend - Restart Script
echo ================================================
echo.
echo This will restart the backend server with admin dashboard support.
echo.
echo Make sure to:
echo   1. Stop any running backend server first (Ctrl+C)
echo   2. Then run this script
echo.
pause

echo.
echo Installing/checking dependencies...
pip install PyJWT psutil python-socketio

echo.
echo ================================================
echo   Starting Backend Server...
echo ================================================
echo.
echo Admin Dashboard will be available at:
echo   Login: http://localhost:5173/admin/login
echo   Email: rathodvamshi369@gmail.com
echo   Password: Rathod@369
echo.
echo Backend API: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ================================================
echo.

python start_server.py
