@echo off
REM ========================================
REM Install BGE-M3 Embedding Model
REM ========================================

REM 获取脚本所在目录的绝对路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo ========================================
REM Install BGE-M3 Embedding Model
REM ========================================
echo.

REM 设置 Ollama 路径
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

echo [Step 1/1] Downloading BGE-M3 embedding model...
echo This may take a few minutes...
echo.

"%OLLAMA_PATH%\ollama.exe" pull bge-m3:latest

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo BGE-M3 model installed successfully!
    echo ========================================
    echo.
    echo To use BGE-M3, update cloud_server_rag.py:
    echo   EMBEDDING_MODEL = "bge-m3"
    echo.
) else (
    echo.
    echo ========================================
    echo Failed to install BGE-M3 model
    echo ========================================
    echo.
)

pause
