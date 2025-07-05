@echo off
echo ============================================
echo Fort Knox Gemini Agent Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)
echo [OK] Python is installed

REM Create virtual environment
echo.
echo Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables
echo.
echo Setting up environment...
set GEMINI_API_KEY=AIzaSyCULQJzJVi9VuMQM6-YaqKAzbooLyG8WD4
set PYTHONPATH=%CD%

REM Run test
echo.
echo ============================================
echo Running Gemini Agent Test
echo ============================================
echo.
python test_gemini_agents.py

echo.
echo ============================================
echo Setup complete!
echo ============================================
echo.
echo To use the agents:
echo 1. Activate the virtual environment: venv\Scripts\activate
echo 2. Set GEMINI_API_KEY environment variable
echo 3. Run your agent scripts
echo.
pause
