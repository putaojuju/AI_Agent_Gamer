@echo off

:: Switch to the directory containing this batch file
cd /d "%~dp0"

:: Display startup information
echo AI Game Agent Launcher
echo --------------------

:: Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo Virtual environment detected, using Python from venv...
    set PYTHON_EXECUTABLE=venv\Scripts\python.exe
) else (
    echo No virtual environment detected, using system Python...
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

:: Check if customtkinter is installed
%PYTHON_EXECUTABLE% -c "import customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] customtkinter not found, installing...
    %PYTHON_EXECUTABLE% -m pip install customtkinter
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install customtkinter.
        echo Please run manually: pip install customtkinter
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