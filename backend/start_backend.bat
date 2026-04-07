@echo off
echo =================================================================
echo  TruthTrace Backend Startup
echo =================================================================
cd /d "%~dp0"

:: Start PostgreSQL via Docker Compose if docker is available
where docker >nul 2>&1
if %errorlevel% == 0 (
  echo [INFO] Starting PostgreSQL via Docker Compose...
  docker-compose up -d postgres
) else (
  echo [WARN] Docker not found. Make sure PostgreSQL is running manually on port 5432.
)

:: Non-blocking DB check so API starts immediately
python -c "import os; from dotenv import load_dotenv; from sqlalchemy import create_engine, text; load_dotenv(); url=os.getenv('DATABASE_URL','postgresql+psycopg://truthtrace:password@127.0.0.1:5432/truthtracedb'); e=create_engine(url); c=e.connect(); c.execute(text('SELECT 1')); c.close(); print('[INFO] PostgreSQL connection OK')" 2>nul
if not %errorlevel% == 0 (
  echo [WARN] PostgreSQL is not ready yet. Starting API anyway...
  echo [WARN] DB-dependent endpoints may temporarily return 503 until DB is up.
)

echo.
echo [INFO] Starting TruthTrace backend on http://0.0.0.0:8001
echo [INFO] Accessible on your local network at your machine's IP:8001
echo [INFO] Press Ctrl+C to stop.
echo =================================================================
python -m uvicorn main:app --host 0.0.0.0 --port 8001
if not %errorlevel% == 0 (
  echo.
  echo [ERROR] Failed to start Uvicorn.
  echo [HINT] Install dependencies: pip install -r requirements.txt
)
pause
