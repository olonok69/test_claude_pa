# Complete Installation Guide: Video Translator with UV on Ubuntu

This guide will walk you through setting up the complete video translation system using UV (the ultra-fast Python package manager) on Ubuntu.

## Prerequisites

### 1. Update Ubuntu System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies
```bash
# Essential development tools
sudo apt install -y build-essential curl git

# Python development dependencies
sudo apt install -y python3-dev python3-pip python3-venv

# Audio/Video processing dependencies
sudo apt install -y ffmpeg libavcodec-extra

# Audio system dependencies for TTS
sudo apt install -y espeak espeak-data libespeak1 libespeak-dev

# PortAudio dependencies (REQUIRED for PyAudio)
sudo apt install -y portaudio19-dev python3-pyaudio libasound2-dev

# Additional audio libraries
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils

# Optional: GUI dependencies if you want to test audio
sudo apt install -y pavucontrol
```

## Step 1: Install UV Package Manager

### Option A: Install UV using the official installer (Recommended)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Option B: Install UV using pip
```bash
pip install uv
```

### Verify UV installation
```bash
# Restart your terminal or source the shell config
source ~/.bashrc
# or
source ~/.zshrc

# Verify installation
uv --version
```

## Step 2: Create Project Directory and Virtual Environment

```bash
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
```bash
cat > requirements.txt << 'EOF'
# Core ML and AI packages
openai-whisper>=20231117
torch>=2.0.0
transformers>=4.35.0
tokenizers>=0.15.0

# Video/Audio processing
moviepy>=1.0.3
pydub>=0.25.1

# TTS engines
pyttsx3>=2.90
edge-tts>=6.1.0

# Additional dependencies
numpy>=1.24.0
scipy>=1.10.0
librosa>=0.10.0
soundfile>=0.12.0
EOF
```

### Create optional requirements file (if you want PyAudio)
```bash
cat > requirements-audio.txt << 'EOF'
# After installing system dependencies, you can optionally install:
pyaudio>=0.2.11
EOF
```

### Install packages using UV
```bash
# Activate virtual environment
source .venv/bin/activate

# Install main packages first (without PyAudio)
uv pip install -r requirements.txt

# Install PyTorch with CPU support
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Optional: Install PyAudio if you installed the system dependencies
# (Only needed for advanced audio processing - pyttsx3 works without it)
uv pip install pyaudio

# If PyAudio still fails, you can skip it - the translator works without it
```

## Step 4: Handle Audio System Setup

### Configure audio for TTS
```bash
# Test if audio system is working
speaker-test -t sine -f 1000 -l 1

# If you're using WSL or headless system, install pulse audio
sudo apt install -y pulseaudio-utils

# Start pulseaudio if not running
pulseaudio --start
```

### Fix potential pyttsx3 issues on Ubuntu
```bash
# Install additional espeak voices
sudo apt install -y espeak-data

# Test espeak
espeak "Hello, this is a test"

# If espeak doesn't work, try installing additional packages
sudo apt install -y festival festvox-kallpc16k
```

## Step 5: Create the Video Translator Application

### Create the main application file
```bash
cat > video_translator.py << 'EOF'
#!/usr/bin/env python3
"""
Complete Video Translator Application
Optimized for Ubuntu with UV package manager
"""

import os
import sys
import whisper
import torch
from transformers import pipeline
import pyttsx3
from moviepy.editor import VideoFileClip, AudioFileClip
import tempfile
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoTranslator:
    def __init__(self):
        """Initialize the video translator"""
        logger.info("Initializing Video Translator...")
        
        # Check if CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load Whisper model
        logger.info("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base", device=self.device)
        
        # Load translation model
        logger.info("Loading translation model...")
        self.translator = pipeline(
            "translation",
            model="Helsinki-NLP/opus-mt-es-en",
            device=0 if self.device == "cuda" else -1
        )
        
        # Initialize TTS
        logger.info("Initializing TTS engine...")
        self.setup_tts()
        
        logger.info("Video Translator initialized successfully!")
    
    def setup_tts(self):
        """Setup TTS engine with error handling"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find English voice
                for voice in voices:
                    if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                
                # Set properties
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.9)
                logger.info("TTS engine configured successfully")
            else:
                logger.warning("No voices found for TTS")
                
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.tts_engine = None
    
    def extract_audio(self, video_path, output_path=None):
        """Extract audio from video"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")
        
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(output_path, verbose=False, logger=None)
            video.close()
            logger.info(f"Audio extracted to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio using Whisper"""
        logger.info("Transcribing audio...")
        
        try:
            result = self.whisper_model.transcribe(audio_path)
            text = result["text"].strip()
            logger.info(f"Transcription completed: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def translate_text(self, text, max_chunk_size=400):
        """Translate text using transformers"""
        logger.info("Translating text...")
        
        try:
            # Split text into chunks for better translation
            words = text.split()
            chunks = []
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) > max_chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word) + 1
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Translate each chunk
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Translating chunk {i+1}/{len(chunks)}")
                result = self.translator(chunk)
                translated_chunks.append(result[0]['translation_text'])
            
            translated_text = ' '.join(translated_chunks)
            logger.info(f"Translation completed: {len(translated_text)} characters")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    def generate_audio(self, text, output_path=None):
        """Generate audio using TTS"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")
        
        logger.info("Generating audio...")
        
        if self.tts_engine is None:
            logger.error("TTS engine not available")
            return None
        
        try:
            self.tts_engine.save_to_file(text, output_path)
            self.tts_engine.runAndWait()
            
            if os.path.exists(output_path):
                logger.info(f"Audio generated: {output_path}")
                return output_path
            else:
                logger.error("Audio file was not created")
                return None
                
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None
    
    def create_final_video(self, original_video_path, new_audio_path, output_path):
        """Combine original video with new audio"""
        logger.info("Creating final video...")
        
        try:
            # Load original video and new audio
            video = VideoFileClip(original_video_path)
            new_audio = AudioFileClip(new_audio_path)
            
            # Adjust audio duration to match video
            video_duration = video.duration
            audio_duration = new_audio.duration
            
            if audio_duration > video_duration:
                new_audio = new_audio.subclip(0, video_duration)
            elif audio_duration < video_duration:
                # Speed up audio to fit video duration
                speed_factor = audio_duration / video_duration
                new_audio = new_audio.fx(lambda clip: clip.speedx(1/speed_factor))
            
            # Combine video and audio
            final_video = video.set_audio(new_audio)
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Cleanup
            video.close()
            new_audio.close()
            final_video.close()
            
            logger.info(f"Final video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            return None
    
    def translate_video(self, input_video_path, output_video_path):
        """Complete video translation pipeline"""
        logger.info(f"Starting video translation: {input_video_path} -> {output_video_path}")
        
        temp_files = []
        
        try:
            # Step 1: Extract audio
            temp_audio = tempfile.mktemp(suffix=".wav")
            temp_files.append(temp_audio)
            
            extracted_audio = self.extract_audio(input_video_path, temp_audio)
            if not extracted_audio:
                return None
            
            # Step 2: Transcribe
            original_text = self.transcribe_audio(extracted_audio)
            if not original_text:
                return None
            
            logger.info(f"Original text: {original_text[:100]}...")
            
            # Step 3: Translate
            translated_text = self.translate_text(original_text)
            if not translated_text:
                return None
            
            logger.info(f"Translated text: {translated_text[:100]}...")
            
            # Step 4: Generate new audio
            temp_new_audio = tempfile.mktemp(suffix=".wav")
            temp_files.append(temp_new_audio)
            
            new_audio_path = self.generate_audio(translated_text, temp_new_audio)
            if not new_audio_path:
                return None
            
            # Step 5: Create final video
            result = self.create_final_video(input_video_path, new_audio_path, output_video_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Video translation failed: {e}")
            return None
        
        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate video from Spanish to English')
    parser.add_argument('input_video', help='Path to input Spanish video')
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
EOF
```

### Make the script executable
```bash
chmod +x video_translator.py
```

## Step 6: Create Helper Scripts

### Create a simple test script
```bash
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify all dependencies are working
"""

import sys

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
        else:
            print("ℹ️  CPU only (no CUDA)")
        return True
    except Exception as e:
        print(f"❌ GPU test failed: {e}")
        return False

def main():
    print("🚀 Video Translator Installation Test\n")
    
    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_audio_system()
    all_passed &= test_gpu()
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! Installation is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x test_installation.py
```

### Create a simple usage script
```bash
cat > translate_video.sh << 'EOF'
#!/bin/bash

# Simple wrapper script for video translation

set -e

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_video> <output_video>"
    echo "Example: $0 spanish_video.mp4 english_video.mp4"
    exit 1
fi

INPUT_VIDEO="$1"
OUTPUT_VIDEO="$2"

# Check if input file exists
if [ ! -f "$INPUT_VIDEO" ]; then
    echo "Error: Input video file not found: $INPUT_VIDEO"
    exit 1
fi

echo "🚀 Starting video translation..."
echo "📹 Input: $INPUT_VIDEO"
echo "📹 Output: $OUTPUT_VIDEO"
echo ""

# Run the translator
python video_translator.py "$INPUT_VIDEO" "$OUTPUT_VIDEO"

echo ""
echo "✅ Done!"
EOF

chmod +x translate_video.sh
```

## Step 7: Test the Installation

### Run the test script
```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
python test_installation.py
```

### Test with a sample video (if you have one)
```bash
# Example usage
./translate_video.sh my_spanish_video.mp4 my_english_video.mp4

# Or directly with Python
python video_translator.py input_video.mp4 output_video.mp4
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Audio/TTS Issues
```bash
# If pyttsx3 doesn't work
sudo apt install -y espeak-ng espeak-ng-data

# Test espeak directly
espeak "test audio"

# If still no audio in headless environment
export PULSE_RUNTIME_PATH=/tmp/pulse-runtime
```

#### 2. GPU/CUDA Issues
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If you have NVIDIA GPU but CUDA not detected
sudo apt install -y nvidia-cuda-toolkit
```

#### 3. MoviePy/FFmpeg Issues
```bash
# Reinstall ffmpeg with additional codecs
sudo apt install -y ffmpeg libavcodec-extra gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
```

#### 4. Permission Issues
```bash
# Fix permissions for audio devices
sudo usermod -a -G audio $USER
# Log out and log back in
```

### Performance Tips

1. **Use larger Whisper models for better accuracy:**
   ```python
   # In video_translator.py, change:
   self.whisper_model = whisper.load_model("medium")  # or "large"
   ```

2. **Enable GPU acceleration if available:**
   ```bash
   # Install CUDA version of PyTorch
   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Use faster translation models:**
   ```python
   # Try different translation models:
   # "Helsinki-NLP/opus-mt-es-en"  # Spanish to English
   # "Helsinki-NLP/opus-mt-fr-en"  # French to English
   ```

## Project Structure

After following this guide, your project structure should look like:

```
video-translator/
├── .venv/                 # Virtual environment (created by UV)
├── video_translator.py    # Main application
├── test_installation.py  # Installation test script
├── translate_video.sh    # Convenient wrapper script
├── requirements.txt      # Package dependencies
└── pyproject.toml        # UV project configuration
```

## Usage Examples

```bash
# Activate environment
source .venv/bin/activate

# Translate a video
python video_translator.py spanish_lecture.mp4 english_lecture.mp4

# Or use the wrapper script
./translate_video.sh "Mi Video en Español.mp4" "My Video in English.mp4"
```

This complete setup gives you a professional-grade video translation system that's completely free and runs locally on your Ubuntu machine! 🎉