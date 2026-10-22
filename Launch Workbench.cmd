@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py --open-browser
) else (
  python run.py --open-browser
)
pause
