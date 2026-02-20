@echo off
REM ========================================
REM Start CADChat Client (Windows Version)
REM ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ========================================
REM Start CADChat Client
REM ========================================
echo.

cd /d "%SCRIPT_DIR%"

REM Check if Python is available
echo [Step 1/2] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)
echo [INFO] Python is available
echo.

REM Check if server is running
echo [Step 2/2] Checking server connection...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:5000/api/stats' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% equ 0 (
    echo [INFO] Server is running and responding
) else (
    echo [WARNING] Server is not responding
    echo [INFO] Please make sure the server is running first
    echo [INFO] Run: cd "%SCRIPT_DIR%\server" ^&^& start_server_rag.bat
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        exit /b 1
    )
)
echo.

REM Start client
echo [INFO] Starting CADChat Client...
echo.
python main_gui_cloud.py
