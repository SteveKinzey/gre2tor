@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  set PYTHON=py -3
) else (
  where python >nul 2>nul
  if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
  ) else (
    echo Python 3 is required. Install it from https://www.python.org/downloads/
    pause
    exit /b 1
  )
)

if not exist venv (
  echo Creating local Python environment...
  %PYTHON% -m venv venv
)

echo Installing/updating requirements...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

echo Starting GRE2Tor...
venv\Scripts\python.exe scripts\run_local.py
pause
