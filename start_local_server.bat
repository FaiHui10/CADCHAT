@echo off
chcp 65001 > nul
echo ========================================
echo CADCHAT 本地服务器启动脚本
echo ========================================
echo.

REM 检查Python是否可用
echo [Step 1/3] Checking Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
) else (
    echo [INFO] Python is available
)

REM 检查虚拟环境
echo.
echo [Step 2/3] Activating virtual environment...
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
    echo [INFO] Virtual environment activated
) else (
    echo [WARNING] Virtual environment not found, using system Python
)

REM 启动本地服务器
echo.
echo [Step 3/3] Starting local server...
echo [INFO] Server will run on http://localhost:5000
echo [INFO] Press Ctrl+C to stop the server
echo.

python cloud_server_bailian.py

if errorlevel 1 (
    echo [ERROR] Failed to start the local server
    pause
)

pause