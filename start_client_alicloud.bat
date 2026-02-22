@echo off
chcp 65001 > nul
echo ========================================
echo CADCHAT 客户端 - 连接到阿里云服务
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
echo [Step 2/2] Connecting to阿里云server...
echo [INFO] Server URL: http://47.99.51.155:5000
echo [INFO] This client connects to the cloud server running on阿里云ECS
echo.

REM 启动GUI客户端
echo [INFO] Starting CADCHAT GUI client (Cloud Version)...
python main_gui_cloud.py

if errorlevel 1 (
    echo [ERROR] Failed to start the application
    pause
)

pause