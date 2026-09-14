@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0launch.py" %*
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
)
if errorlevel 1 pause
