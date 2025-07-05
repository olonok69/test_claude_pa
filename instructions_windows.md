# Complete Installation Guide: Video Translator with UV on Windows

This guide will walk you through setting up the complete video translation system using UV (the ultra-fast Python package manager) on Windows 10/11. The system uses FFmpeg directly for reliable video processing and supports videos up to 2+ hours.

## Prerequisites

### 1. Install Required Software

#### A. Install Python 3.11 or 3.12
1. Download Python from [python.org](https://www.python.org/downloads/windows/)
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Choose "Customize installation" and ensure these are checked:
   - ✅ pip
   - ✅ py launcher
   - ✅ Add Python to environment variables

#### B. Install Git (Optional but recommended)
1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Use default installation options

#### C. Install FFmpeg
**Option 1: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey first (run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install FFmpeg
choco install ffmpeg
```

**Option 2: Manual Installation**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html#build-windows)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your PATH environment variable:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click "Environment Variables"
   - Under "System Variables", find "Path" and click "Edit"
   - Click "New" and add `C:\ffmpeg\bin`
   - Click "OK" on all dialogs

#### D. Install Microsoft Visual C++ Redistributable
Download and install from [Microsoft's website](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### 2. Verify Installation
Open **Command Prompt** or **PowerShell** and test:
```cmd
python --version
pip --version
ffmpeg -version
```

## Step 1: Install UV Package Manager

### Option A: Using PowerShell (Recommended)
```powershell
# Run in PowerShell
irm https://astral.sh/uv/install.ps1 | iex
```

### Option B: Using pip
```cmd
pip install uv
```

### Option C: Using Chocolatey
```powershell
choco install uv
```

### Verify UV Installation
```cmd
# Restart your command prompt
uv --version
```

## Step 2: Create Project Directory and Virtual Environment

```cmd
# Create project directory
mkdir video-translator
cd video-translator

# Initialize a new Python project with UV
uv init

# Create virtual environment with UV
uv venv
```

## Step 3: Install Required Packages with UV

### Create requirements file
```cmd
echo # Core ML and AI packages > requirements.txt
echo openai-whisper>=20231117 >> requirements.txt
echo torch>=2.0.0 >> requirements.txt
echo transformers>=4.35.0 >> requirements.txt
echo tokenizers>=0.15.0 >> requirements.txt
echo. >> requirements.txt
echo # Required for Helsinki translation models >> requirements.txt
echo sentencepiece>=0.1.95 >> requirements.txt
echo. >> requirements.txt
echo # TTS engines >> requirements.txt
echo pyttsx3>=2.90 >> requirements.txt
echo edge-tts>=6.1.0 >> requirements.txt
echo. >> requirements.txt
echo # Essential dependencies >> requirements.txt
echo numpy>=1.24.0,^<2.3.0 >> requirements.txt
echo scipy>=1.10.0 >> requirements.txt
echo librosa>=0.10.0 >> requirements.txt
echo soundfile>=0.12.0 >> requirements.txt
echo. >> requirements.txt
echo # Audio processing >> requirements.txt
echo pydub>=0.25.1 >> requirements.txt
echo. >> requirements.txt
echo # Optional: for better HuggingFace performance >> requirements.txt
echo huggingface_hub[hf_xet]>=0.16.0 >> requirements.txt
echo. >> requirements.txt
echo # Audio analysis and plotting >> requirements.txt
echo matplotlib>=3.5.0 >> requirements.txt
```

### Install packages using UV
```cmd
# Activate virtual environment
.venv\Scripts\activate

# Install all packages with UV (ultra-fast!)
uv pip install -r requirements.txt

# Install PyTorch with CPU support (or GPU if you have CUDA)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# For NVIDIA GPU users (optional - better performance)
# uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Step 4: Create the Video Translator Applications

The system includes multiple scripts for different use cases:

1. **`video_translator.py`** - Basic video translator (short videos)
2. **`long_video_translator.py`** - Optimized for 2+ hour videos with segment processing
3. **`audio_debug_script.py`** - Debug audio issues and test different extraction methods
4. **`test_installation.py`** - Verify all dependencies are working
5. **`voice_tester.py`** - Test different TTS voices

*Copy the Python scripts from the artifacts provided in the conversation.*

## Step 5: Create Helper Scripts

### Create a Windows test script
Create `test_installation.py` (from artifacts)

### Create a Windows batch file for easy usage
Create `translate_video.bat`:

```batch
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
    echo.
    echo Advanced usage:
    echo %~n0 input.mp4 output.mp4 --edge-tts
    echo %~n0 input.mp4 output.mp4 --edge-tts --voice en-US-GuyNeural
    pause
    exit /b 1
)

set INPUT_VIDEO=%~1
set OUTPUT_VIDEO=%~2
set EXTRA_ARGS=%~3 %~4 %~5 %~6

REM Check if input file exists
if not exist "%INPUT_VIDEO%" (
    echo Error: Input video file not found: %INPUT_VIDEO%
    pause
    exit /b 1
)

echo 🚀 Starting video translation...
echo 📹 Input: %INPUT_VIDEO%
echo 📹 Output: %OUTPUT_VIDEO%
echo ⚙️ Extra options: %EXTRA_ARGS%
echo.

REM Run the translator (use long_video_translator for better handling)
python long_video_translator.py "%INPUT_VIDEO%" "%OUTPUT_VIDEO%" %EXTRA_ARGS%

echo.
if %ERRORLEVEL% EQU 0 (
    echo ✅ Done!
) else (
    echo ❌ Translation failed!
)

pause
```

## Step 6: Test the Installation

### Run the test script
```cmd
# Make sure you're in the virtual environment
.venv\Scripts\activate

# Run tests
python test_installation.py
```

### Test with a sample video
```cmd
# Example usage with batch file (basic translation)
translate_video.bat "my spanish video.mp4" "my english video.mp4"

# High-quality translation with Edge TTS
translate_video.bat "input.mp4" "output.mp4" --edge-tts

# Custom voice
translate_video.bat "input.mp4" "output.mp4" --edge-tts --voice en-US-GuyNeural

# For long videos (2+ hours)
python long_video_translator.py "long_movie.mp4" "long_movie_en.mp4" --edge-tts
```

## Available TTS Voices

### Edge TTS (High Quality)
| Voice | Gender | Accent | Style |
|-------|--------|---------|-------|
| `en-US-AriaNeural` | Female | American | Natural (default) |
| `en-US-JennyNeural` | Female | American | Friendly |
| `en-US-GuyNeural` | Male | American | Natural |
| `en-US-DavisNeural` | Male | American | Expressive |
| `en-GB-SoniaNeural` | Female | British | Natural |
| `en-GB-RyanNeural` | Male | British | Natural |
| `en-AU-NatashaNeural` | Female | Australian | Natural |

### Test voices
```cmd
python voice_tester.py
```

## Windows-Specific Troubleshooting

### Common Issues and Solutions

#### 1. "Python is not recognized" Error
```cmd
# Add Python to PATH manually
# 1. Find Python installation (usually C:\Users\[username]\AppData\Local\Programs\Python\Python311)
# 2. Add to PATH environment variable
# 3. Restart Command Prompt

# Or reinstall Python with "Add to PATH" checked
```

#### 2. FFmpeg Not Found
```cmd
# Test if FFmpeg is in PATH
ffmpeg -version

# If not found, download and extract to C:\ffmpeg
# Add C:\ffmpeg\bin to PATH environment variable
# Restart Command Prompt
```

#### 3. TTS Not Working
```powershell
# Test Windows TTS
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Speak("Hello, this is a test")
```

#### 4. NaN/Logits Errors with Whisper
```cmd
# Debug the audio first
python audio_debug_script.py your_video.mp4

# Force CPU processing (more stable)
set CUDA_VISIBLE_DEVICES=
python video_translator.py input.mp4 output.mp4

# Use smaller segments for problematic videos
python long_video_translator.py input.mp4 output.mp4 --segment-length 120
```

#### 5. CUDA Issues (for NVIDIA GPU users)
```cmd
# Check NVIDIA drivers
nvidia-smi

# Install CUDA Toolkit if needed
# Download from: https://developer.nvidia.com/cuda-downloads

# Install CUDA-enabled PyTorch
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 6. Permission Issues
```cmd
# Run Command Prompt as Administrator if needed
# Or move project to a folder without special permissions (like Documents)
```

#### 7. Long Path Issues
```cmd
# Enable long paths in Windows (run as Administrator)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1
```

#### 8. Windows Defender Issues
- Add the video-translator folder to Windows Defender exclusions
- This prevents antivirus from interfering with Python processes

### Performance Tips for Windows

1. **Use SSD storage** for faster file processing
2. **Close unnecessary programs** during translation
3. **Use larger Whisper models** for better accuracy (if you have enough RAM):
   ```python
   # The system automatically uses medium model for better quality
   ```

4. **Enable GPU acceleration** if you have NVIDIA GPU:
   ```cmd
   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

5. **Optimize Windows for performance:**
   - Set power plan to "High Performance"
   - Close background apps
   - Ensure at least 8GB RAM available

## System Requirements

### Minimum Requirements
- **RAM**: 4GB available
- **Storage**: 5GB free space
- **CPU**: Multi-core recommended
- **Internet**: For downloading models (first run only)

### Recommended for Long Videos (2+ hours)
- **RAM**: 8GB+ available
- **Storage**: 20GB+ free space
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional but faster)
- **CPU**: 8+ cores for faster processing

## Performance Estimates

### Short Videos (under 1 hour)
- **Processing time**: 0.5-2x video length
- **Example**: 30-minute video = 15-60 minutes processing

### Long Videos (2+ hours)
- **Processing time**: 0.5-1x video length  
- **Example**: 2-hour movie = 1-2 hours processing

## Project Structure

After following this guide, your project structure should look like:

```
video-translator\
├── .venv\                    # Virtual environment (created by UV)
├── video_translator.py       # Basic translator for short videos
├── long_video_translator.py  # Optimized for long videos (2+ hours)
├── audio_debug_script.py     # Debug audio issues
├── test_installation.py      # Installation test script
├── voice_tester.py          # Test different TTS voices
├── translate_video.bat      # Windows batch wrapper script
├── requirements.txt         # Package dependencies
└── pyproject.toml           # UV project configuration
```

## Usage Examples

```cmd
REM Activate environment
.venv\Scripts\activate

REM Basic translation
python video_translator.py "spanish_lecture.mp4" "english_lecture.mp4"

REM High-quality with Edge TTS
python video_translator.py "input.mp4" "output.mp4" --edge-tts

REM Long video processing
python long_video_translator.py "movie.mp4" "movie_en.mp4" --edge-tts --voice en-US-GuyNeural

REM Batch file (easiest)
translate_video.bat "Mi Video.mp4" "My Video.mp4" --edge-tts
```

## Windows-Specific Features

- **Native Windows SAPI TTS** - Uses built-in Windows voices
- **Path handling** - Properly handles Windows file paths and spaces
- **Batch file wrapper** - Easy drag-and-drop usage
- **Windows-optimized settings** - Better speech rate and voice selection
- **Long video support** - Segment processing for 2+ hour videos
- **GPU acceleration** - CUDA support for faster processing

## Advanced Features

### Enable Windows Developer Mode (Optional)
For better HuggingFace model caching performance:

1. **Press `Win + I`** to open Settings
2. Go to **Update & Security** > **For developers**
3. Turn on **Developer Mode**
4. Restart your command prompt

This enables symlinks and improves model loading speed.

### Batch Processing
```cmd
REM Process multiple videos
for %%f in (*.mp4) do (
    python long_video_translator.py "%%f" "translated_%%f" --edge-tts
)
```

This complete Windows setup gives you a professional-grade video translation system that works natively on Windows and takes advantage of Windows-specific features! 🎉

### Quick Start Summary

1. Install Python, FFmpeg, and Visual C++ Redistributable
2. Install UV package manager
3. Create project and virtual environment
4. Install packages with UV
5. Create the Python scripts
6. Test everything
7. Start translating videos!

The entire setup takes about 15-20 minutes, and then you have a powerful, free video translation system running locally on Windows.add_argument('input_video', help='Path to input Spanish video')
    parser.add_argument('output_video', help='Path to output English video')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_video):
        print(f"Error: Input video file not found: {args.input_video}")
        sys.exit(1)
    
    # Initialize translator
    translator = VideoTranslator()
    
    # Translate video
    result = translator.translate_video(args.input_video, args.output_video)
    
    if result:
        print(f"✅ Translation completed successfully!")
        print(f"📹 Output video: {args.output_video}")
    else:
        print("❌ Translation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Step 5: Create Helper Scripts

### Create a Windows test script
Create `test_installation.py`:

```python
#!/usr/bin/env python3
"""
Test script to verify all dependencies are working on Windows
"""

import sys
import platform

def test_imports():
    """Test all required imports"""
    tests = [
        ("whisper", "OpenAI Whisper"),
        ("torch", "PyTorch"),
        ("transformers", "Hugging Face Transformers"),
        ("moviepy.editor", "MoviePy"),
        ("pyttsx3", "pyttsx3 TTS"),
        ("numpy", "NumPy"),
    ]
    
    print("🧪 Testing imports...")
    failed = []
    
    for module, name in tests:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {e}")
            failed.append(name)
    
    return len(failed) == 0

def test_audio_system():
    """Test audio system"""
    print("\n🔊 Testing audio system...")
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        if voices:
            print(f"✅ Found {len(voices)} TTS voices")
            for i, voice in enumerate(voices[:3]):  # Show first 3
                print(f"   Voice {i+1}: {voice.name}")
        else:
            print("⚠️  No TTS voices found")
        
        return True
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False

def test_gpu():
    """Test GPU availability"""
    print("\n🖥️  Testing GPU...")
    
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name()}")
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU count: {torch.cuda.device_count()}")
        else:
            print("ℹ️  CPU only (no CUDA)")
        return True
    except Exception as e:
        print(f"❌ GPU test failed: {e}")
        return False

def test_ffmpeg():
    """Test FFmpeg availability"""
    print("\n🎬 Testing FFmpeg...")
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            return True
        else:
            print("❌ FFmpeg not found or not working")
            return False
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        print("   Make sure FFmpeg is installed and in your PATH")
        return False

def main():
    print("🚀 Video Translator Installation Test - Windows\n")
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version}\n")
    
    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_audio_system()
    all_passed &= test_gpu()
    all_passed &= test_ffmpeg()
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! Installation is ready.")
        print("\n📝 Next steps:")
        print("   1. Put a Spanish video file in this folder")
        print("   2. Run: python video_translator.py input.mp4 output.mp4")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    input("Press Enter to run tests...")
    sys.exit(main())
```

### Create a Windows batch file for easy usage
Create `translate_video.bat`:

```batch
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
```

## Step 6: Test the Installation

### Run the test script
```cmd
# Make sure you're in the virtual environment
.venv\Scripts\activate

# Run tests
python test_installation.py
```

### Test with a sample video
```cmd
# Example usage with batch file
translate_video.bat "my spanish video.mp4" "my english video.mp4"

# Or directly with Python
python video_translator.py "input_video.mp4" "output_video.mp4"
```

## Windows-Specific Troubleshooting

### Common Issues and Solutions

#### 1. "Python is not recognized" Error
```cmd
# Add Python to PATH manually
# 1. Find Python installation (usually C:\Users\[username]\AppData\Local\Programs\Python\Python311)
# 2. Add to PATH environment variable
# 3. Restart Command Prompt

# Or reinstall Python with "Add to PATH" checked
```

#### 2. FFmpeg Not Found
```cmd
# Test if FFmpeg is in PATH
ffmpeg -version

# If not found, download and extract to C:\ffmpeg
# Add C:\ffmpeg\bin to PATH environment variable
# Restart Command Prompt
```

#### 3. TTS Not Working
```powershell
# Test Windows TTS
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Speak("Hello, this is a test")
```

#### 4. CUDA Issues (for NVIDIA GPU users)
```cmd
# Check NVIDIA drivers
nvidia-smi

# Install CUDA Toolkit if needed
# Download from: https://developer.nvidia.com/cuda-downloads

# Install CUDA-enabled PyTorch
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 5. Permission Issues
```cmd
# Run Command Prompt as Administrator if needed
# Or move project to a folder without special permissions (like Documents)
```

#### 6. MoviePy Issues
```cmd
# If you get imageio-ffmpeg errors
uv pip install imageio-ffmpeg --upgrade

# Test MoviePy
python -c "from moviepy.editor import VideoFileClip; print('MoviePy working!')"
```

### Performance Tips for Windows

1. **Use SSD storage** for faster file processing
2. **Close unnecessary programs** during translation
3. **Use larger Whisper models** for better accuracy (if you have enough RAM):
   ```python
   # In video_translator.py, change:
   self.whisper_model = whisper.load_model("medium")  # or "large"
   ```

4. **Enable GPU acceleration** if you have NVIDIA GPU:
   ```cmd
   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

## Project Structure

After following this guide, your project structure should look like:

```
video-translator\
├── .venv\                 # Virtual environment (created by UV)
├── video_translator.py    # Main application
├── test_installation.py  # Installation test script
├── translate_video.bat   # Windows batch wrapper script
├── requirements.txt      # Package dependencies
└── pyproject.toml        # UV project configuration
```

## Usage Examples

```cmd
REM Activate environment
.venv\Scripts\activate

REM Translate a video
python video_translator.py "spanish_lecture.mp4" "english_lecture.mp4"

REM Or use the batch file (easier)
translate_video.bat "Mi Video en Español.mp4" "My Video in English.mp4"

REM The batch file handles spaces in filenames automatically
```

## Windows-Specific Features

- **Native Windows SAPI TTS** - Uses built-in Windows voices
- **Path handling** - Properly handles Windows file paths and spaces
- **Batch file wrapper** - Easy drag-and-drop usage
- **Windows-optimized settings** - Better speech rate and voice selection

This complete Windows setup gives you a professional-grade video translation system that works natively on Windows and takes advantage of Windows-specific features! 🎉

### Quick Start Summary

1. Install Python, FFmpeg, and Visual C++ Redistributable
2. Install UV package manager
3. Create project and virtual environment
4. Install packages with UV
5. Create the Python scripts
6. Test everything
7. Start translating videos!

The entire setup takes about 15-20 minutes, and then you have a powerful, free video translation system running locally on Windows.