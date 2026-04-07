@echo off
setlocal
echo =================================================================
echo  TruthTrace AI - Full Stack Launcher
echo =================================================================

:: 1. Start Backend
echo [1/2] Starting Backend (http://127.0.0.1:8001)...
start "TruthTrace Backend" cmd /k "cd /d ""%~dp0backend"" && python -m uvicorn main:app --host 0.0.0.0 --port 8001"

:: 2. Start Frontend
timeout /t 1 /nobreak >nul
echo [2/2] Starting Frontend (http://127.0.0.1:5500)...
start "TruthTrace Frontend" cmd /k "cd /d ""%~dp0frontend"" && python -m http.server 5500"

:: 3. Fetch Network IP
timeout /t 1 /nobreak >nul
echo.
echo  Local Dashboard  : http://127.0.0.1:5500
echo  API Docs         : http://127.0.0.1:8001/docs
echo =================================================================
echo  Fetching network IP for mobile access...
for /f "delims=" %%I in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like '*Wi-Fi*' -or $_.InterfaceAlias -like '*Wireless*' -or $_.InterfaceAlias -like '*Ethernet*' } | Select-Object -First 1).IPAddress"') do set "NETWORK_IP=%%I"
if defined NETWORK_IP (
    echo  Mobile Access : http://%NETWORK_IP%:5500
) 
echo =================================================================
echo  Press any key to close this launcher (servers will keep running in windows).
pause >nul
