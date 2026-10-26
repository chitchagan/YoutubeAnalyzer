@echo off
setlocal
cd /d "%~dp0"
title YouTube Subscriber Analyzer

if exist ".venv\Scripts\python.exe" goto dependencies
echo Creating the local Python environment...
py -3 -m venv .venv
if not errorlevel 1 goto dependencies
python -m venv .venv
if errorlevel 1 goto python_error

:dependencies
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, requests" >nul 2>&1
if not errorlevel 1 goto launch
echo Installing required packages. Internet access is needed for this first setup.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error

:launch
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop Local Server.ps1"
if errorlevel 1 (
    pause
    exit /b 1
)
echo.
echo Open: http://127.0.0.1:8000
echo.
echo Enter your YouTube API key in the app.
echo Keep this window open. Press Ctrl+C to stop the app.
echo.
start "" "http://127.0.0.1:8000"
".venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000
if errorlevel 1 pause
exit /b

:python_error
echo.
echo Python could not create the environment. Install Python 3.10 or newer
echo from https://www.python.org/downloads/ and enable the Python launcher.
pause
exit /b 1

:install_error
echo.
echo Package installation failed. Check your internet connection and try again.
pause
exit /b 1
