@echo off
title Daily Expense Tracker
echo Starting Daily Expense Tracker...
cd /d "%~dp0"
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
echo.
echo Launching Application at http://localhost:5000
start http://localhost:5000
python app.py
pause
