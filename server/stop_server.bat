@echo off
setlocal enabledelayedexpansion
REM ========================================
REM Stop Server (Windows Version)
REM ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ========================================
REM Stop CADChat Server
REM ========================================
echo.

cd /d "%SCRIPT_DIR%"

REM Stop Flask service (CADChat Server)
echo [Step 1/2] Stopping Flask service...
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Checking for CADChat Server...
    for /f "tokens=2" %%p in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /I "cloud_server"') do (
        set "PID=%%p"
        set "PID=!PID:"=!"
        taskkill /F /PID !PID! >nul 2>&1
    )
    echo [INFO] CADChat Server stopped
) else (
    echo [INFO] CADChat Server is not running
)
echo.

REM Stop Ollama service
echo [Step 2/2] Stopping Ollama service...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Stopping Ollama service...
    taskkill /F /IM ollama.exe >nul 2>&1
    echo [INFO] Ollama service stopped
) else (
    echo [INFO] Ollama service is not running
)
echo.

echo ========================================
REM All services stopped
REM ========================================
echo.
