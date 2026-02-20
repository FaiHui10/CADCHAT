@echo off
REM ========================================
REM Start RAG Server (Windows Version)
REM ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ========================================
REM Start CADChat RAG Server
REM ========================================
echo.

cd /d "%SCRIPT_DIR%"

REM Set Ollama path (可以从环境变量读取，默认尝试常见位置)
if defined OLLAMA_PATH (
    set "OLLAMA_PATH=%OLLAMA_PATH%"
) else (
    set "OLLAMA_PATH=C:\Users\%USERNAME%\ollama"
    if not exist "%OLLAMA_PATH%\ollama.exe" (
        set "OLLAMA_PATH=C:\Ollama"
    )
    if not exist "%OLLAMA_PATH%\ollama.exe" (
        set "OLLAMA_PATH=C:\Program Files\Ollama"
    )
)

REM Check if Ollama is running
echo [Step 1/4] Checking Ollama service...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Ollama service is running
) else (
    echo [INFO] Ollama service is not running
    if exist "%OLLAMA_PATH%\ollama.exe" (
        echo [INFO] Starting Ollama service...
        start "" "%OLLAMA_PATH%\ollama.exe" serve
        timeout /t 5 /nobreak >nul
        echo [INFO] Ollama service started
    ) else (
        echo [WARNING] Ollama not found at: %OLLAMA_PATH%
        echo [INFO] Please set OLLAMA_PATH environment variable
    )
)
echo.

REM Check Ollama connection
echo [Step 2/4] Checking Ollama connection...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Ollama service is responding
) else (
    echo [ERROR] Ollama service is not responding
    echo.
    echo Please check if Ollama is installed and running
    echo Ollama path: %OLLAMA_PATH%
    echo You can set OLLAMA_PATH environment variable
    pause
    exit /b 1
)
echo.

REM Check embedding model
echo [Step 3/4] Checking embedding model...
"%OLLAMA_PATH%\ollama.exe" list | findstr bge-m3 >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Embedding model is available
) else (
    echo [WARNING] Embedding model not found
    echo [INFO] Downloading bge-m3 embedding model...
    echo [INFO] This may take a few minutes...
    "%OLLAMA_PATH%\ollama.exe" pull bge-m3:latest
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to download embedding model
        pause
        exit /b 1
    )
    echo [INFO] Embedding model downloaded
)
echo.

REM Start Flask RAG service
echo [Step 4/4] Starting Flask RAG service...
echo Port: 5000
echo Model: qwen3:1.7b
echo Embedding Model: bge-m3
echo Command Files: autocad_basic_commands.txt, lisp_commands.txt
echo.
python cloud_server_rag.py

pause
