@echo off
chcp 65001 >nul
echo Starting Script Manager...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe .\script_manager.py

if errorlevel 1 (
    echo.
    echo Program exited with error. Press any key to close...
    pause >nul
)
