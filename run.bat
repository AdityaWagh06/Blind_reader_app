@echo off
echo.
echo ========================================
echo    Blind Reader Assistant Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements (fast no-op when already satisfied)
echo Checking requirements...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

REM Run the application
echo.
echo Starting Blind Reader Assistant...
echo Open the URL below in your web browser
echo URL: http://127.0.0.1:8000
echo Press Ctrl+C to stop the application
echo.
python app.py

pause 