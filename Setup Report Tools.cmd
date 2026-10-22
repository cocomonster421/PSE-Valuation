@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 (
  echo Setup failed. Install Python 3.11 or newer with pip and add it to PATH.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your connection and run this setup again.
  pause
  exit /b 1
)
echo Setup complete. Open Launch Workbench.cmd. Ordinary analysis and report parsing work offline.
pause
