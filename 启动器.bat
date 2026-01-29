@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: AI Game Agent Launcher
:: ============================================================

title AI Game Agent Launcher
color 0B

cls
echo.
echo  ============================================================
echo.
echo    AI GAME AGENT - HOLOGRAPHIC CONSOLE
echo.
echo  ============================================================
echo.

:: Switch to the directory containing this batch file
cd /d "%~dp0"

:: 1. Environment Check
echo  [*] Checking Environment...
set CONDA_ENV=ai_agent_311

conda run -n %CONDA_ENV% python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo  [ERROR] Python environment '%CONDA_ENV%' not found!
    echo.
    echo  Please run the following command to create the environment:
    echo    conda create -n ai_agent_311 python=3.11
    echo.
    pause
    exit /b
)
echo  [OK] Environment '%CONDA_ENV%' detected.

:: 2. Dependency Check
echo  [*] Checking Dependencies...
conda run -n %CONDA_ENV% python -c "import PySide6" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [INFO] Installing missing dependencies...
    conda run -n %CONDA_ENV% pip install -r requirements.txt
    if !errorlevel! neq 0 (
        color 0C
        echo.
        echo  [ERROR] Failed to install dependencies.
        echo  Please run manually: conda run -n ai_agent_311 pip install -r requirements.txt
        echo.
        pause
        exit /b
    )
    echo  [OK] Dependencies installed.
) else (
    echo  [OK] Dependencies ready.
)

:: 3. Launch Core
echo.
echo  ============================================================
echo  [*] Launching Holographic Console...
echo  ============================================================
echo.

conda run -n %CONDA_ENV% python main.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo  [ERROR] Program exited with error code: %errorlevel%
    echo.
    pause
) else (
    echo.
    echo  [INFO] Program exited normally.
    timeout /t 3 >nul
)
