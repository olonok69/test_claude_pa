@echo off
:: Batch installation script for PDF Document Processor MCP Server on Windows using uv

setlocal enabledelayedexpansion

echo.
echo ========================================
echo PDF Document Processor MCP Server
echo Windows Installation with UV
echo ========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Warning: Not running as administrator. Some installations may fail.
    echo Consider running as administrator for best results.
    echo.
    timeout /t 3 >nul
)

:: Step 1: Install uv if not present
echo [1/5] Checking uv installation...
uv --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing uv...
    powershell -Command "& {Invoke-RestMethod -Uri 'https://astral.sh/uv/install.ps1' | Invoke-Expression}"
    if %errorLevel% neq 0 (
        echo Error: Failed to install uv
        echo Please install uv manually from: https://github.com/astral-sh/uv
        pause
        exit /b 1
    )
    :: Refresh PATH
    call refreshenv.cmd >nul 2>&1
    :: Add uv to PATH for current session
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo uv is already installed
)

:: Verify uv installation
uv --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: uv is not accessible. Please restart the command prompt and try again.
    pause
    exit /b 1
)

echo uv installation verified
echo.

:: Step 2: Check for Tesseract OCR
echo [2/5] Checking Tesseract OCR...
tesseract --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Tesseract OCR not found.
    echo.
    echo Please install Tesseract OCR:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Install with Spanish and English language packs
    echo 3. Add to PATH during installation
    echo.
    set /p continue="Continue without Tesseract? (OCR will not work) [y/N]: "
    if /i not "!continue!"=="y" (
        echo Installation cancelled. Please install Tesseract and try again.
        pause
        exit /b 1
    )
    echo Continuing without Tesseract...
) else (
    echo Tesseract OCR found
)
echo.

:: Step 3: Create project directory
echo [3/5] Creating project directory...
set "PROJECT_DIR=pdf-processor-mcp"

if exist "%PROJECT_DIR%" (
    echo Directory already exists. 
    set /p overwrite="Overwrite existing directory? [y/N]: "
    if /i not "!overwrite!"=="y" (
        echo Installation cancelled.
        pause
        exit /b 1
    )
    rmdir /s /q "%PROJECT_DIR%"
)

::Initialize uv project with --no-workspace to avoid conflicts
uv init %PROJECT_DIR% --no-readme --no-workspace
if %errorLevel% neq 0 (
    echo Error: Failed to create project directory
    pause
    exit /b 1
)

cd %PROJECT_DIR%
echo Project created: %CD%
echo.

:: Step 4: Install dependencies
echo [4/5] Installing Python dependencies...
echo This may take a few minutes...

uv add "mcp[cli]>=1.2.0"
if %errorLevel% neq 0 (
    echo Error: Failed to install mcp
    pause
    exit /b 1
)

uv add "PyMuPDF>=1.23.0"
if %errorLevel% neq 0 (
    echo Error: Failed to install PyMuPDF
    pause
    exit /b 1
)

uv add "pytesseract>=0.3.10"
if %errorLevel% neq 0 (
    echo Error: Failed to install pytesseract
    pause
    exit /b 1
)

uv add "Pillow>=10.0.0"
if %errorLevel% neq 0 (
    echo Error: Failed to install Pillow
    pause
    exit /b 1
)

uv add "opencv-python>=4.8.0"
if %errorLevel% neq 0 (
    echo Error: Failed to install opencv-python
    pause
    exit /b 1
)

echo Dependencies installed successfully
echo.

:: Step 5: Setup instructions
echo [5/5] Setup complete!
echo.
echo ========================================
echo Installation Summary
echo ========================================
echo Project Location: %CD%
echo.
echo Next Steps:
echo 1. Copy these files to the project directory:
echo    - pdf_processor_server.py
echo    - prompts.json
echo.
echo 2. Test the server:
echo    uv run python pdf_processor_server.py
echo.
echo 3. For Claude Desktop, add this configuration:
echo    {
echo      "mcpServers": {
echo        "pdf-processor": {
echo          "command": "uv",
echo          "args": ["run", "python", "%CD%\pdf_processor_server.py"]
echo        }
echo      }
echo    }
echo.
echo 4. Configuration file location:
echo    Windows: %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo ========================================

pause