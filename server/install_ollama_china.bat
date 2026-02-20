a@echo off
REM Install Ollama from local file

echo ========================================
echo Install Ollama from Local File
echo ========================================
echo.

REM Ask user for file path
echo Please enter path to ollama-windows-amd64.zip
echo Example: C:\Downloads\ollama-windows-amd64.zip
echo.
set /p OLLAMA_ZIP="Enter path: "

if not exist "%OLLAMA_ZIP%" (
    echo [ERROR] Ollama file not found: %OLLAMA_ZIP%
    echo.
    echo Please check the path and try again
    echo Download from: https://github.com/ollama/ollama/releases
    pause
    exit /b 1
)

echo [INFO] Found Ollama file: %OLLAMA_ZIP%
echo.

REM Check if Ollama is already installed
echo [Step 1/5] Checking existing installation...
set OLLAMA_DIR=%USERPROFILE%\ollama
if exist "%OLLAMA_DIR%\ollama.exe" (
    echo [INFO] Ollama is already installed
    "%OLLAMA_DIR%\ollama.exe" --version
    echo.
    set /p REINSTALL="Reinstall? (Y/N): "
    if /i not "%REINSTALL%"=="Y" (
        echo [SKIP] Keeping existing installation
        goto :download_model
    )
    echo [UNINSTALL] Uninstalling existing version...
    if exist "%OLLAMA_DIR%" rmdir /s /q "%OLLAMA_DIR%"
    echo.
)
echo.

REM Extract installation package
echo [Step 2/5] Extracting installation package...

if exist "%OLLAMA_DIR%" (
    echo [INFO] Removing existing directory...
    rmdir /s /q "%OLLAMA_DIR%"
)

mkdir "%OLLAMA_DIR%"

powershell -Command "Expand-Archive -Path '%OLLAMA_ZIP%' -DestinationPath '%OLLAMA_DIR%' -Force"

if %errorlevel% neq 0 (
    echo [ERROR] Extraction failed
    pause
    exit /b 1
)

echo [DONE] Extraction successful
echo.

REM Add to PATH
echo [Step 3/5] Adding to PATH...
setx PATH "%PATH%;%OLLAMA_DIR%" /M

echo [DONE] Added to PATH
echo.

REM Verify installation
echo [Step 4/5] Verifying installation...
"%OLLAMA_DIR%\ollama.exe" --version

if %errorlevel% neq 0 (
    echo [ERROR] Verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation Complete
echo ========================================
echo.
echo Ollama installed to: %OLLAMA_DIR%
echo.

:download_model
echo ========================================
echo Download Model
echo ========================================
echo.

REM Download embedding model
echo [Step 1/2] Downloading bge-m3 embedding model...
"%OLLAMA_DIR%\ollama.exe" pull bge-m3

if %errorlevel% neq 0 (
    echo [ERROR] Model download failed
    echo.
    echo Try using proxy or download manually
    pause
    exit /b 1
)

echo [DONE] Model download successful
echo.

REM Verify model
echo [Step 2/2] Verifying model...
"%OLLAMA_DIR%\ollama.exe" list

echo.
echo ========================================
echo All Complete
echo ========================================
echo.
echo Installed:
echo   - Ollama: %OLLAMA_DIR%
echo   - Embedding Model: bge-m3
echo.
echo Next steps:
echo   1. Reopen command prompt to make PATH effective
echo   2. Start Ollama: ollama serve
echo   3. Or run in background: Start-Process ollama -ArgumentList "serve"
echo.

pause
