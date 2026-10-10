@echo off
setlocal
cd /d "%~dp0"
if not exist .env (
  echo .env not found. Create it from .env.example and add your LLM_API_KEY.
  exit /b 1
)
docker compose up -d --build
if errorlevel 1 exit /b 1
docker compose ps
start http://localhost:5173
endlocal
