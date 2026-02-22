@echo off
chcp 65001 > nul
echo ========================================
echo CADCHAT 客户端 - 连接到本地服务器
echo ========================================
echo.

REM 检查Python是否可用
echo [Step 1/2] Checking Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
) else (
    echo [INFO] Python is available
)

echo.
echo [Step 2/2] Connecting to local server...
echo [INFO] Server URL: http://localhost:5000
echo [INFO] Make sure the local server is running first
echo [INFO] To start local server: run "start_local_server.bat"
echo.

REM 启动GUI客户端
echo [INFO] Starting CADCHAT GUI client (Local Version)...
python main_gui_cloud.py

if errorlevel 1 (
    echo [ERROR] Failed to start the application
    pause
)

pause