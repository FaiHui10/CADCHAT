@echo off
REM ========================================
REM Start CADChat Client (Windows Version)
REM ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ========================================
echo Start CADChat Client
echo ========================================
echo.

cd /d "%SCRIPT_DIR%"

REM Check if required environment variables are set
if not exist ".env" (
    echo [WARN] .env file not found, using defaults
    echo [INFO] Copy .env.example to .env and configure your settings
)

REM Check if required packages are installed
echo [Step 1/2] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Python is available
) else (
    echo [ERROR] Python is not available
    pause
    exit /b 1
)
echo.

REM Install/update required packages
echo [Step 2/2] Installing/updating required packages...
pip install -r client_requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install required packages
    pause
    exit /b 1
)
echo.

REM Start CADChat Client
echo Starting CADChat Client...
echo.
python main_gui_cloud.py

pause