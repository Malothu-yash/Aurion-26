@echo off
echo ============================================================
echo RESTARTING AURION BACKEND WITH ADMIN SUPPORT
echo ============================================================
echo.

echo Step 1: Killing existing Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo Step 2: Checking dependencies...
python -c "import jwt; print('✓ PyJWT installed')" 2>nul || (
    echo Installing PyJWT...
    pip install PyJWT
)

python -c "import psutil; print('✓ psutil installed')" 2>nul || (
    echo Installing psutil...
    pip install psutil
)

python -c "import socketio; print('✓ python-socketio installed')" 2>nul || (
    echo Installing python-socketio...
    pip install python-socketio
)

python -c "import bcrypt; print('✓ bcrypt installed')" 2>nul || (
    echo Installing bcrypt...
    pip install bcrypt
)

echo.
echo Step 3: Starting backend server...
echo Backend will start on http://127.0.0.1:8000
echo Admin endpoints at http://127.0.0.1:8000/api/v1/admin/*
echo.

start "AURION Backend" cmd /k "python start_server.py"

timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo ✅ Backend restarted!
echo ============================================================
echo.
echo Admin Login Credentials:
echo   Email: rathodvamshi369@gmail.com
echo   Password: Rathod@369
echo.
echo Admin Endpoints:
echo   POST /api/v1/admin/login
echo   GET  /api/v1/admin/dashboard/stats
echo   GET  /api/v1/admin/users
echo.
echo Testing admin endpoint...
echo.

timeout /t 3 /nobreak >nul

python -c "import requests; r = requests.post('http://127.0.0.1:8000/api/v1/admin/login', json={'email': 'rathodvamshi369@gmail.com', 'password': 'Rathod@369'}); print('Status:', r.status_code); print('Response:', r.json() if r.status_code == 200 else r.text)"

echo.
pause
