#!/usr/bin/env python3
"""
Test script to verify all dependencies are working (No MoviePy version)
"""

import sys
import platform
import subprocess

def test_imports():
    """Test all required imports"""
    tests = [
        ("whisper", "OpenAI Whisper"),
        ("torch", "PyTorch"),
        ("transformers", "Hugging Face Transformers"),
        ("pyttsx3", "pyttsx3 TTS"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("librosa", "Librosa"),
        ("soundfile", "SoundFile"),
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

def test_ffmpeg():
    """Test FFmpeg availability"""
    print("\n🎬 Testing FFmpeg...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            
            # Test FFprobe too
            result2 = subprocess.run(['ffprobe', '-version'], 
                                   capture_output=True, text=True, timeout=10)
            if result2.returncode == 0:
                print("✅ FFprobe also available")
            else:
                print("⚠️  FFprobe not found (may affect some features)")
            
            return True
        else:
            print("❌ FFmpeg not found or not working")
            return False
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        print("   Make sure FFmpeg is installed and in your PATH")
        print("   Ubuntu: sudo apt install ffmpeg")
        print("   Windows: Download from https://ffmpeg.org or use chocolatey")
        return False

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

def test_video_processing():
    """Test basic video processing capabilities"""
    print("\n📹 Testing video processing capabilities...")
    
    try:
        # Test if we can get video info
        import tempfile
        import json
        
        # Create a tiny test video command
        test_cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-y', tempfile.mktemp(suffix='.mp4')
        ]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Video generation test passed")
            # Clean up the test file
            import os
            try:
                os.remove(test_cmd[-1])
            except:
                pass
            return True
        else:
            print("⚠️  Video generation test failed (may still work with real videos)")
            return True  # Don't fail the whole test for this
            
    except Exception as e:
        print(f"⚠️  Video processing test failed: {e}")
        return True  # Don't fail the whole test for this

def test_whisper_model():
    """Test if Whisper model can be loaded"""
    print("\n🎤 Testing Whisper model loading...")
    
    try:
        import whisper
        model = whisper.load_model("tiny")  # Load smallest model for testing
        print("✅ Whisper model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Whisper model loading failed: {e}")
        return False

def main():
    print("🚀 Video Translator Installation Test (FFmpeg version)\n")
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version}\n")
    
    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_ffmpeg()
    all_passed &= test_audio_system()
    all_passed &= test_gpu()
    all_passed &= test_video_processing()
    all_passed &= test_whisper_model()
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All tests passed! Installation is ready.")
        print("\n📝 Next steps:")
        print("   1. Put a Spanish video file in this folder")
        print("   2. Run: python video_translator_ffmpeg.py input.mp4 output.mp4")
        print("\n💡 This version uses FFmpeg instead of MoviePy")
        print("   - Much more reliable installation")
        print("   - Better performance")
        print("   - Wider format support")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    if platform.system() == "Windows":
        input("Press Enter to continue...")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())