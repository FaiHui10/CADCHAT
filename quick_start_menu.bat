@echo off
chcp 65001 > nul
title CADCHAT 快速启动菜单

:menu
cls
echo ========================================
echo        CADCHAT 快速启动菜单
echo ========================================
echo.
echo 请选择启动模式:
echo.
echo 1. 启动本地服务器
echo 2. 启动阿里云客户端
echo 3. 启动本地客户端
echo 4. 通用客户端启动器
echo.
echo 0. 退出
echo.
set /p choice="请输入选项 (0-4): "

if "%choice%"=="1" goto local_server
if "%choice%"=="2" goto alicloud_client
if "%choice%"=="3" goto local_client
if "%choice%"=="4" goto universal
if "%choice%"=="0" goto exit_menu

echo.
echo 无效选项，请重新选择。
timeout /t 2 > nul
goto menu

:local_server
echo.
echo [INFO] 启动本地服务器...
call start_local_server.bat
goto menu

:alicloud_client
echo.
echo [INFO] 启动阿里云客户端...
call start_client_alicloud.bat
goto menu

:local_client
echo.
echo [INFO] 启动本地客户端...
call start_client_local.bat
goto menu

:universal
echo.
echo [INFO] 启动通用客户端...
call start_client_universal.bat
goto menu

:exit_menu
echo.
echo [INFO] 退出启动菜单
exit /b 0