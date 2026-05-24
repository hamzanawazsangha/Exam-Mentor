@echo off
REM CSS/PMS Exam Preparation Portal - Run Script (Windows CMD)

echo.
echo ==================================
echo CSS/PMS Exam Preparation Portal
echo ==================================
echo.

REM Get the script directory
set "scriptDir=%~dp0"

REM Check if venv exists
if not exist "%scriptDir%venv" (
    echo Creating virtual environment...
    python -m venv "%scriptDir%venv"
)

REM Activate venv
echo Activating virtual environment...
call "%scriptDir%venv\Scripts\activate.bat"

REM Navigate to backend
cd /d "%scriptDir%backend"

REM Display startup information
echo.
echo ==================================
echo Starting Flask Server...
echo ==================================
echo.
echo Server running at:
echo   http://127.0.0.1:5000 (Home)
echo   http://127.0.0.1:5000/dashboard (Dashboard)
echo.
echo API Endpoints:
echo   POST   /api/auth/register
echo   POST   /api/auth/login
echo   GET    /api/dashboard/metrics/^<user_id^>
echo   POST   /api/preparation/select-exam
echo   POST   /api/preparation/generate-paper/^<user_id^>/^<subject_id^>
echo.
echo Press Ctrl+C to stop the server
echo ==================================
echo.

REM Start Flask server
python main.py

pause
