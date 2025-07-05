@echo off
setlocal

REM Simple wrapper batch file for video translation

REM Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
)

REM Check arguments
if "%~2"=="" (
    echo Usage: %~n0 ^<input_video^> ^<output_video^>
    echo Example: %~n0 spanish_video.mp4 english_video.mp4
    pause
    exit /b 1
)

set INPUT_VIDEO=%~1
set OUTPUT_VIDEO=%~2

REM Check if input file exists
if not exist "%INPUT_VIDEO%" (
    echo Error: Input video file not found: %INPUT_VIDEO%
    pause
    exit /b 1
)

echo 🚀 Starting video translation...
echo 📹 Input: %INPUT_VIDEO%
echo 📹 Output: %OUTPUT_VIDEO%
echo.

REM Run the translator
python video_translator.py "%INPUT_VIDEO%" "%OUTPUT_VIDEO%"

echo.
if %ERRORLEVEL% EQU 0 (
    echo ✅ Done!
) else (
    echo ❌ Translation failed!
)

pause