@echo off
chcp 65001 > nul
echo ========================================
echo CADCHAT 本地服务器启动脚本 (RAG版本)
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] 检查 Python 环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

echo [INFO] Python 可用

echo.
echo [INFO] 检查依赖包...
pip show flask > nul 2>&1
if errorlevel 1 (
    echo [WARNING] flask 未安装，正在安装...
    pip install flask flask-cors requests numpy scipy scikit-learn watchdog
)

echo.
echo [INFO] 启动服务器...
echo [INFO] 服务地址: http://localhost:5000
echo [INFO] 按 Ctrl+C 停止服务
echo.

python cloud_server_rag.py

if errorlevel 1 (
    echo [ERROR] 服务启动失败
    pause
)
