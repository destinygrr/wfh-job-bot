@echo off
REM ============================================================
REM  WFH JOB BOT - Windows one-click runner
REM  First time  : installs what it needs (1 minute)
REM  Every time  : checks jobs + sends your WhatsApp / Telegram alert
REM ============================================================
title WFH Job Bot
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo  Python is not installed. Get it free from https://www.python.org/downloads/
  echo  IMPORTANT: during install, tick the box "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

python -c "import requests, yaml" 2>nul
if errorlevel 1 (
  echo Installing required pieces ^(one time only^)...
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r requirements.txt
)

echo.
echo  Checking LinkedIn, Apna, Naukri for work-from-home jobs...
echo.
python -m jobbot.main
echo.
echo  Done. Digest saved at: data\latest_digest.html
echo  To prove alerts work, run:  python -m jobbot.main --test
echo.
pause
