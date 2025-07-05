#!/usr/bin/env python3
"""
Audio Debug Script - Test and fix audio issues before transcription
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
import subprocess
import tempfile
import matplotlib.pyplot as plt

def analyze_audio(audio_path):
    """Analyze audio file for potential issues"""
    print(f"\n🔍 Analyzing audio: {audio_path}")
    
    try:
        # Load audio
        audio_data, sr = librosa.load(audio_path, sr=16000)
        
        print(f"📊 Audio Statistics:")
        print(f"   Duration: {len(audio_data) / sr:.2f} seconds")
        print(f"   Sample rate: {sr} Hz")
        print(f"   Samples: {len(audio_data)}")
        print(f"   Min value: {np.min(audio_data):.6f}")
        print(f"   Max value: {np.max(audio_data):.6f}")
        print(f"   Mean: {np.mean(audio_data):.6f}")
        print(f"   RMS: {np.sqrt(np.mean(audio_data**2)):.6f}")
        
        # Check for issues
        issues = []
        
        if len(audio_data) == 0:
            issues.append("❌ Empty audio file")
        
        if np.all(audio_data == 0):
            issues.append("❌ All silence (zeros)")
        
        if np.any(np.isnan(audio_data)):
            issues.append(f"❌ Contains {np.sum(np.isnan(audio_data))} NaN values")
        
        if np.any(np.isinf(audio_data)):
            issues.append(f"❌ Contains {np.sum(np.isinf(audio_data))} Inf values")
        
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 1e-5:
            issues.append(f"⚠️  Very quiet audio (RMS: {rms:.2e})")
        
        if np.max(np.abs(audio_data)) > 0.99:
            issues.append("⚠️  Audio may be clipping")
        
        # Check for DC offset
        dc_offset = np.mean(audio_data)
        if abs(dc_offset) > 0.01:
            issues.append(f"⚠️  DC offset detected: {dc_offset:.4f}")
        
        if len(issues) == 0:
            print("✅ No major issues detected")
        else:
            print("🚨 Issues found:")
            for issue in issues:
                print(f"   {issue}")
        
        return audio_data, sr, issues
        
    except Exception as e:
        print(f"❌ Failed to analyze audio: {e}")
        return None, None, [f"❌ Analysis failed: {e}"]

def clean_audio(audio_data, sr):
    """Clean audio data to prevent Whisper issues"""
    print("\n🧹 Cleaning audio...")
    
    original_data = audio_data.copy()
    
    # Remove NaN and Inf values
    if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
        print("   Removing NaN/Inf values...")
        audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Remove DC offset
    dc_offset = np.mean(audio_data)
    if abs(dc_offset) > 0.001:
        print(f"   Removing DC offset: {dc_offset:.4f}")
        audio_data = audio_data - dc_offset
    
    # Normalize if too loud
    max_amp = np.max(np.abs(audio_data))
    if max_amp > 0.9:
        print(f"   Normalizing amplitude (was {max_amp:.3f})")
        audio_data = audio_data / max_amp * 0.9
    elif max_amp > 0 and max_amp < 0.1:
        print(f"   Boosting quiet audio (was {max_amp:.3f})")
        audio_data = audio_data / max_amp * 0.5
    
    # Check if changes were made
    if not np.array_equal(original_data, audio_data):
        print("✅ Audio cleaned")
    else:
        print("ℹ️  No cleaning needed")
    
    return audio_data

def test_whisper_transcription(audio_path):
    """Test Whisper transcription with different settings"""
    print(f"\n🎤 Testing Whisper transcription...")
    
    try:
        import whisper
        
        # Load small model for testing
        print("   Loading Whisper model...")
        model = whisper.load_model("tiny", device="cpu")
        
        # Test different configurations
        configs = [
            {
                "name": "Standard",
                "params": {"language": "es", "fp16": False}
            },
            {
                "name": "Conservative", 
                "params": {
                    "language": "es", 
                    "fp16": False, 
                    "temperature": 0.0,
                    "no_speech_threshold": 0.8,
                    "beam_size": 1
                }
            },
            {
                "name": "No Language Hint",
                "params": {"fp16": False, "temperature": 0.0}
            }
        ]
        
        for config in configs:
            print(f"\n   Testing {config['name']} config...")
            try:
                result = model.transcribe(audio_path, **config["params"])
                text = result["text"].strip()
                print(f"   ✅ {config['name']}: '{text[:100]}{'...' if len(text) > 100 else ''}'")
                print(f"      Length: {len(text)} characters")
            except Exception as e:
                print(f"   ❌ {config['name']}: {e}")
        
    except ImportError:
        print("   ❌ Whisper not available for testing")
    except Exception as e:
        print(f"   ❌ Whisper test failed: {e}")

def extract_and_test_audio(video_path):
    """Extract audio from video and test it"""
    print(f"\n📹 Extracting audio from video: {video_path}")
    
    # Extract with different methods
    methods = [
        {
            "name": "Standard",
            "cmd": [
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1'
            ]
        },
        {
            "name": "Filtered",
            "cmd": [
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-af', 'volume=0.5,highpass=f=80,lowpass=f=8000,dynaudnorm'
            ]
        }
    ]
    
    for method in methods:
        print(f"\n   Testing {method['name']} extraction...")
        
        output_path = tempfile.mktemp(suffix=f"_{method['name'].lower()}.wav")
        cmd = method["cmd"] + [output_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"   ✅ Extraction successful")
                
                # Analyze the extracted audio
                audio_data, sr, issues = analyze_audio(output_path)
                
                if audio_data is not None and len(issues) == 0:
                    print(f"   ✅ {method['name']} method looks good!")
                    
                    # Test transcription if no major issues
                    test_whisper_transcription(output_path)
                
                # Clean up
                try:
                    os.remove(output_path)
                except:
                    pass
            else:
                print(f"   ❌ Extraction failed: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Extraction error: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug audio issues for video translation')
    parser.add_argument('input', help='Video or audio file to test')
    parser.add_argument('--extract-only', action='store_true', help='Only extract audio, don\'t test transcription')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)
    
    print("🔧 Audio Debug Tool")
    print("=" * 40)
    
    # Determine if input is video or audio
    ext = os.path.splitext(args.input)[1].lower()
    
    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        # Video file - extract audio first
        extract_and_test_audio(args.input)
    elif ext in ['.wav', '.mp3', '.m4a', '.flac']:
        # Audio file - analyze directly
        audio_data, sr, issues = analyze_audio(args.input)
        
        if audio_data is not None:
            # Clean audio and save
            cleaned_audio = clean_audio(audio_data, sr)
            
            if not args.extract_only:
                # Test transcription
                test_whisper_transcription(args.input)
    else:
        print(f"❌ Unsupported file type: {ext}")
        sys.exit(1)

if __name__ == "__main__":
    main()