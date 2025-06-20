@echo off
REM Script to launch backend (FastAPI) and frontend (npm) in production mode on Windows

REM Start backend
call .venv\Scripts\activate
cd backend
start "Backend" cmd /c "fastapi run src/main.py"
cd ..

REM Start frontend
cd frontend
start "Frontend" cmd /c "npm run start"
cd ..

REM Wait for user to press any key to stop processes
echo.
echo Press any key to stop backend and frontend...
pause >nul

REM Kill the backend and frontend windows
taskkill /FI "WINDOWTITLE eq Backend" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend" /T /F >nul 2>&1