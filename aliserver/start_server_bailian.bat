@echo off
REM ========================================
REM Start Bailian RAG Server (Windows Version)
REM ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ========================================
echo Start CADChat Bailian RAG Server
echo ========================================
echo.

cd /d "%SCRIPT_DIR%"

REM Check if required environment variables are set
if not defined BAILIAN_APP_ID (
    echo [ERROR] BAILIAN_APP_ID environment variable is not set
    echo [INFO] Please set BAILIAN_APP_ID to your Aliyun Bailian App ID
    echo [INFO] Example: set BAILIAN_APP_ID=your_app_id_here
    pause
    exit /b 1
)

if not defined DASHSCOPE_API_KEY (
    echo [ERROR] DASHSCOPE_API_KEY environment variable is not set
    echo [INFO] Please set DASHSCOPE_API_KEY to your Aliyun DashScope API Key
    echo [INFO] Example: set DASHSCOPE_API_KEY=sk-your_api_key_here
    pause
    exit /b 1
)

echo [Step 1/3] Checking Python environment...
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
echo [Step 2/3] Installing/updating required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install required packages
    pause
    exit /b 1
)
echo.

REM Start Flask Bailian RAG service
echo [Step 3/3] Starting Flask Bailian RAG service...
echo Port: 5000
echo Bailian App ID: %BAILIAN_APP_ID%
echo RAG Provider: Aliyun Bailian Platform
echo.
python cloud_server_bailian.py

pause