@echo off
setlocal
cd /d "%~dp0"
echo [1/4] Checking containers...
docker compose ps
if errorlevel 1 exit /b 1

echo [2/4] Checking API health...
curl -fsS http://localhost:8000/api/health
if errorlevel 1 exit /b 1

echo.
echo [3/4] Running backend tests...
docker compose exec backend pytest tests -q
if errorlevel 1 exit /b 1

echo [4/4] Running evaluation harness...
python evals\evaluator.py
if errorlevel 1 exit /b 1

echo.
echo FowForge verification completed.
endlocal
