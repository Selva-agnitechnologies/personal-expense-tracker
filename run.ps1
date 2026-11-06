# PowerShell startup script for Daily Expense Tracker
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    & .\.venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host "Starting Daily Expense Tracker on http://localhost:5000 ..." -ForegroundColor Green
Start-Process "http://localhost:5000"
& .\.venv\Scripts\python.exe app.py

