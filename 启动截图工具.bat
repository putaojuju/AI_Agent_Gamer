@echo off
chcp 65001 >nul
echo Starting Screenshot Tool...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe .\screenshot_tool.py

if errorlevel 1 (
    echo.
    echo Program exited with error. Press any key to close...
    pause >nul
)
