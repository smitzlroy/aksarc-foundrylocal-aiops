@echo off
REM AKS Arc AI Ops - Start Server
echo.
echo ========================================
echo   AKS Arc AI Operations Assistant
echo ========================================
echo.

REM Get to the right directory
cd /d "%~dp0backend"

REM Check if we're in the right place
if not exist "run.py" (
    echo ERROR: Cannot find run.py
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Refresh PATH to find Python
for /f "usebackq tokens=*" %%i in (`powershell -Command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%i"

REM Verify Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.11 or later
    pause
    exit /b 1
)

REM Start the server
echo Starting server on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
python run.py

pause
