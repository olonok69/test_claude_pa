# 🎬 AI Video Translator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-required-red.svg)](https://ffmpeg.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cross Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)]()

A powerful, **completely free** and **local** AI-powered video translation system that translates Spanish videos to English using state-of-the-art machine learning models. No cloud services, no subscriptions, no data privacy concerns - everything runs on your machine!

## ✨ Key Features

- 🎯 **High Accuracy** transcription and translation using cutting-edge AI models
- ⚡ **Fast Processing** with GPU/CUDA support for hardware acceleration
- 🔧 **Robust Error Handling** for reliable processing of various video formats
- 📱 **Cross-Platform** support (Windows 10/11 and Ubuntu Linux)
- 🎨 **Multiple Voice Options** including high-quality Edge TTS and system voices
- 📹 **Wide Format Support** (.mp4, .avi, .mov, .mkv, .webm)
- ⏱️ **Long Video Support** up to 2+ hours with intelligent segment processing
- 🔄 **Memory Efficient** segment-based processing for large files
- 🎤 **Advanced Audio Processing** with noise reduction and normalization
- 🔒 **100% Local Processing** - your videos never leave your computer

## 🎥 How It Works

![Video Translation Process](https://raw.githubusercontent.com/user/repo/main/docs/pipeline.png)

The translation process follows these steps:

### 1. 🎵 Audio Extraction
- Extracts audio track from video using FFmpeg
- Optimizes audio for speech recognition (16kHz PCM, mono channel)
- Applies noise reduction and normalization filters

### 2. 🎤 Speech Recognition  
- Transcribes Spanish audio to text using **OpenAI Whisper**
- Supports multiple model sizes (base, medium, large)
- Robust error handling for various audio qualities

### 3. 🌐 Text Translation
- Translates Spanish text to English using **Helsinki-NLP transformer**
- Intelligent text chunking for optimal translation quality
- Maintains context across long texts

### 4. 🗣️ Text-to-Speech
- Generates English audio using **Edge TTS** or system TTS
- Multiple voice options with natural-sounding speech
- Optimized audio quality and timing

### 5. 🎬 Video Processing
- Replaces original audio with translated audio
- Preserves video quality and synchronization
- Maintains original video format and metadata

### 6. 💾 Output Generation
- Creates final video with English audio track
- No quality loss in video processing
- Compatible with all major video players

## 🤖 AI Models Used

| Model | Purpose | Description |
|-------|---------|-------------|
| **OpenAI Whisper** | Speech Recognition | State-of-the-art model trained on 680,000 hours of multilingual audio data |
| **Helsinki-NLP opus-mt** | Translation | High-quality neural machine translation specifically for Spanish→English |
| **Edge TTS / pyttsx3** | Text-to-Speech | Advanced TTS engines providing natural-sounding English voices |

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or 3.12
- FFmpeg (for video/audio processing)
- At least 4GB RAM (8GB+ recommended for long videos)

### Installation

**Option 1: Windows**
```bash
# Install Python, FFmpeg, and Visual C++ Redistributable
# See detailed Windows installation guide below

# Install UV package manager
irm https://astral.sh/uv/install.ps1 | iex

# Create project
mkdir video-translator && cd video-translator
uv init && uv venv
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

**Option 2: Ubuntu Linux**
```bash
# Install system dependencies
sudo apt update && sudo apt install -y python3-dev ffmpeg build-essential

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
mkdir video-translator && cd video-translator
uv init && uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Basic Usage

```bash
# Simple translation
python video_translator.py spanish_video.mp4 english_video.mp4

# High-quality translation with Edge TTS
python video_translator.py input.mp4 output.mp4 --edge-tts

# For long videos (2+ hours)
python video_translator.py long_movie.mp4 long_movie_en.mp4 --edge-tts --segment-length 600

# Windows batch file (drag and drop)
translate_video.bat "Mi Video.mp4" "My Video.mp4"
```

## 📋 Available Scripts

| Script | Purpose | Best For |
|--------|---------|----------|
| `video_translator.py` | Standard video translation | Videos under 1 hour |
| `test_installation.py` | Verify installation | Testing setup |
| `audio_debug_script.py` | Debug audio issues | Troubleshooting |
| `translate_video.bat` | Windows wrapper | Easy Windows usage |

## 🎤 Voice Options

### Edge TTS Voices (Recommended)
| Voice | Gender | Accent | Style |
|-------|--------|---------|-------|
| `en-US-AriaNeural` | Female | American | Natural (default) |
| `en-US-JennyNeural` | Female | American | Friendly |
| `en-US-GuyNeural` | Male | American | Natural |
| `en-US-DavisNeural` | Male | American | Expressive |
| `en-GB-SoniaNeural` | Female | British | Natural |
| `en-GB-RyanNeural` | Male | British | Natural |

### Usage Examples
```bash
# Use specific voice
python video_translator.py input.mp4 output.mp4 --edge-tts --voice en-US-GuyNeural

# British accent
python video_translator.py input.mp4 output.mp4 --edge-tts --voice en-GB-SoniaNeural
```

## ⚙️ Advanced Configuration

### Long Video Processing
For videos longer than 1 hour, use segment-based processing:

```bash
# Process 2-hour movie with 10-minute segments
python video_translator.py movie.mp4 movie_en.mp4 --segment-length 600

# Smaller segments for better memory usage
python video_translator.py movie.mp4 movie_en.mp4 --segment-length 300
```

### GPU Acceleration
For faster processing with NVIDIA GPUs:

```bash
# Install CUDA-enabled PyTorch
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# The system automatically detects and uses GPU
```

### Debug Audio Issues
```bash
# Analyze and fix audio problems
python audio_debug_script.py problematic_video.mp4

# Test different extraction methods
python audio_debug_script.py video.mp4 --extract-only
```

## 📊 Performance Estimates

| Video Length | Processing Time | RAM Usage | Storage Needed |
|--------------|----------------|-----------|----------------|
| 30 minutes | 15-60 minutes | 2-4 GB | 5 GB temp |
| 1 hour | 30-120 minutes | 4-6 GB | 10 GB temp |
| 2 hours | 1-2 hours | 6-8 GB | 20 GB temp |

*Times vary based on hardware, video quality, and chosen models*

## 🛠️ Detailed Installation Guides

<details>
<summary><strong>🪟 Windows Installation (Click to expand)</strong></summary>

### Prerequisites
1. **Install Python 3.11 or 3.12**
   - Download from [python.org](https://www.python.org/downloads/windows/)
   - ✅ **IMPORTANT**: Check "Add Python to PATH"

2. **Install FFmpeg**
   ```powershell
   # Option 1: Chocolatey (recommended)
   choco install ffmpeg
   
   # Option 2: Manual download from ffmpeg.org
   # Extract to C:\ffmpeg and add C:\ffmpeg\bin to PATH
   ```

3. **Install Visual C++ Redistributable**
   - Download from [Microsoft's website](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Setup Steps
```cmd
# Install UV package manager
irm https://astral.sh/uv/install.ps1 | iex

# Create project
mkdir video-translator
cd video-translator
uv init
uv venv

# Activate environment
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Test installation
python test_installation.py
```

### Usage
```cmd
# Basic usage
python video_translator.py "spanish_video.mp4" "english_video.mp4"

# Or use the batch file
translate_video.bat "Mi Video.mp4" "My Video.mp4" --edge-tts
```

</details>

<details>
<summary><strong>🐧 Ubuntu Linux Installation (Click to expand)</strong></summary>

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y build-essential curl git python3-dev python3-pip

# Install FFmpeg and audio libraries
sudo apt install -y ffmpeg libavcodec-extra espeak espeak-data

# Install PortAudio for audio processing
sudo apt install -y portaudio19-dev python3-pyaudio libasound2-dev

# Audio system dependencies
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils
```

### Setup Steps
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Create project
mkdir video-translator && cd video-translator
uv init && uv venv

# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Test installation
python test_installation.py
```

### Usage
```bash
# Basic usage
python video_translator.py spanish_video.mp4 english_video.mp4

# Or use the shell script
./translate_video.sh spanish_video.mp4 english_video.mp4
```

</details>

## 🔧 Troubleshooting

### Common Issues

**🎵 Audio/TTS Problems**
```bash
# Test system audio
speaker-test -t sine -f 1000 -l 1

# Install additional voices (Ubuntu)
sudo apt install -y espeak-ng espeak-ng-data

# Windows: Check Windows TTS voices in Settings
```

**🎬 FFmpeg Not Found**
```bash
# Verify FFmpeg installation
ffmpeg -version
ffprobe -version

# Ubuntu: Install FFmpeg
sudo apt install -y ffmpeg

# Windows: Add to PATH or reinstall
```

**🧠 Memory Issues (Long Videos)**
```bash
# Use smaller segments
python video_translator.py movie.mp4 movie_en.mp4 --segment-length 300

# Force CPU processing (more stable)
CUDA_VISIBLE_DEVICES= python video_translator.py input.mp4 output.mp4
```

**🤖 Whisper NaN/Logits Errors**
```bash
# Debug the audio first
python audio_debug_script.py problematic_video.mp4

# Use more conservative settings
python video_translator.py input.mp4 output.mp4 --conservative
```

### Getting Help

1. **Run the test script**: `python test_installation.py`
2. **Check the debug tool**: `python audio_debug_script.py your_video.mp4`
3. **Review logs**: All operations are logged with detailed error messages
4. **Try smaller segments**: For long videos, reduce `--segment-length`

## 📁 Project Structure

```
video-translator/
├── .venv/                      # Virtual environment
├── video_translator.py         # Main application (standard videos)
├── audio_debug_script.py       # Audio debugging tool
├── test_installation.py        # Installation verification
├── translate_video.bat         # Windows batch wrapper
├── translate_video.sh          # Linux shell wrapper
├── requirements.txt            # Python dependencies
├── pyproject.toml             # UV project configuration
├── pipeline.html              # Process visualization
└── README.md                  # This file
```

## 🔄 Example Workflows

### Basic Translation
```bash
# 1. Put your Spanish video in the project folder
# 2. Run translation
python video_translator.py "conferencia_español.mp4" "conference_english.mp4"

# 3. The translated video will be created with English audio
```

### High-Quality Translation
```bash
# Use Edge TTS for better voice quality
python video_translator.py input.mp4 output.mp4 \
  --edge-tts \
  --voice en-US-AriaNeural
```

### Long Video Processing
```bash
# For 2+ hour videos, use segment processing
python video_translator.py "pelicula_larga.mp4" "long_movie_en.mp4" \
  --edge-tts \
  --segment-length 600  # 10-minute segments
```

## 📈 Supported Formats

### Input Formats
- **Video**: .mp4, .avi, .mov, .mkv, .webm, .flv
- **Audio**: .wav, .mp3, .m4a, .flac (for audio-only processing)

### Output Formats
- **Video**: Same as input format
- **Audio**: AAC encoding for broad compatibility

## 🎯 Use Cases

- **📚 Educational Content**: Translate Spanish lectures, tutorials, courses
- **🎬 Entertainment**: Translate movies, documentaries, shows
- **💼 Business**: Translate presentations, meetings, training videos
- **📺 Content Creation**: Translate YouTube videos, vlogs, interviews
- **🏛️ Accessibility**: Make Spanish content accessible to English speakers

## ⚡ Performance Tips

1. **Use SSD storage** for faster file I/O operations
2. **Close unnecessary programs** during processing
3. **Enable GPU acceleration** for 2-3x speed improvement
4. **Use larger Whisper models** (medium/large) for better accuracy
5. **Optimize segment length** based on available RAM
6. **Use Edge TTS** for higher quality voice output

## 🆚 Comparison with Other Solutions

| Feature | This Tool | Cloud Services | Other Local Tools |
|---------|-----------|----------------|-------------------|
| **Cost** | Free | $10-50/hour | $50-500 one-time |
| **Privacy** | 100% Local | Cloud-based | Varies |
| **Quality** | High | Very High | Medium |
| **Speed** | Fast | Very Fast | Slow |
| **Offline** | ✅ Yes | ❌ No | ✅ Yes |
| **Unlimited Use** | ✅ Yes | ❌ No | ✅ Yes |

## 🛡️ Privacy & Security

- **🔒 Complete Privacy**: All processing happens locally on your machine
- **🚫 No Data Collection**: No telemetry, analytics, or data uploading
- **📁 Local Storage**: Videos and models stored only on your computer
- **🔓 Open Source**: All code is transparent and auditable
- **⚡ Offline Operation**: Works without internet connection (after initial setup)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 💡 Future Enhancements

- 🌍 Additional language pairs (French↔English, German↔English)
- 🎥 Real-time translation for live streams
- 🎛️ GUI interface for non-technical users
- 🔧 More TTS voice options and customization
- 📱 Mobile app version
- 🎨 Subtitle generation and embedding
- 🤖 Integration with other AI models

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Run `python test_installation.py` to verify your setup
3. Use `python audio_debug_script.py` for audio-related issues
4. Review the detailed error logs for specific problems

---
