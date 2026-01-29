@echo off

:: Switch to the directory containing this batch file
cd /d "%~dp0"

:: Display startup information
echo AI Game Agent Launcher
echo --------------------

:: Activate Conda environment
echo Activating Conda environment (ai_agent_311)...
call conda activate ai_agent_311

if %errorlevel% neq 0 (
    echo [WARNING] Failed to activate Conda environment.
    echo Trying to use system Python...
    set PYTHON_EXECUTABLE=python
) else (
    echo Conda environment activated successfully.
    set PYTHON_EXECUTABLE=python
)

:: Check if Python is available
%PYTHON_EXECUTABLE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python command not found.
    echo Please ensure Python is installed and added to system PATH.
    pause
    exit /b
)

:: Check if PySide6 is installed
%PYTHON_EXECUTABLE% -c "import PySide6" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PySide6 not found, installing dependencies...
    %PYTHON_EXECUTABLE% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        echo Please run manually: pip install -r requirements.txt
        pause
        exit /b
    )
)

:: Run main program
echo Starting main program...
echo --------------------
%PYTHON_EXECUTABLE% main.py

:: Check run result
if %errorlevel% neq 0 (
    echo --------------------
    echo [ERROR] Program exited with error.
    echo This may be due to missing dependencies or environment issues.
    echo Please try running: pip install -r requirements.txt
    pause
) else (
    echo --------------------
    echo Program exited normally.
    pause
)
