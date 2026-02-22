@echo off
chcp 65001 > nul
echo ========================================
echo CADCHAT 通用客户端启动器
echo ========================================
echo.

REM 检查参数
if "%1"=="--local" goto start_local
if "%1"=="--alicloud" goto start_alicloud

REM 显示帮助信息
echo 使用方法:
echo   %0 --local     ^| 启动连接到本地服务器的客户端
echo   %0 --alicloud  ^| 启动连接到阿里云服务器的客户端
echo.
echo 默认使用阿里云配置
echo.

:start_alicloud
echo [INFO] 启动连接到阿里云服务器的客户端...
echo [INFO] 服务器地址: http://47.99.51.155:5000
python main_gui_cloud.py --alicloud
goto end

:start_local
echo [INFO] 启动连接到本地服务器的客户端...
echo [INFO] 服务器地址: http://localhost:5000
python main_gui_cloud.py --local
goto end

:end
if errorlevel 1 (
    echo [ERROR] 启动失败
    pause
)