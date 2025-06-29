#!/usr/bin/env python3
"""
Long Video Translator - Optimized for videos up to 2+ hours
Includes segment-based processing and memory management
"""

import os
import sys
import whisper
import torch
from transformers import pipeline
import tempfile
from pathlib import Path
import logging
import subprocess
import json
import time
import gc
from datetime import timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LongVideoTranslator:
    def __init__(self, use_edge_tts=False, edge_voice="en-US-AriaNeural", segment_length=600):
        """
        Initialize the long video translator
        
        Args:
            use_edge_tts: Use Edge TTS for better quality
            edge_voice: Voice to use with Edge TTS
            segment_length: Length of each segment in seconds (default: 10 minutes)
        """
        logger.info("Initializing Long Video Translator with FFmpeg backend...")
        
        # Check if FFmpeg is available
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
        
        # Check if CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Configuration for long videos
        self.segment_length = segment_length
        self.use_edge_tts = use_edge_tts
        self.edge_voice = edge_voice
        
        logger.info(f"Segment length: {segment_length} seconds ({segment_length/60:.1f} minutes)")
        logger.info(f"TTS: {'Edge TTS' if use_edge_tts else 'System TTS'} (Voice: {edge_voice})")
        
        # Load models
        self.load_models()
        
        logger.info("Long Video Translator initialized successfully!")
    
    def load_models(self):
        """Load AI models with memory optimization"""
        # Load Whisper model with error handling
        logger.info("Loading Whisper model...")
        try:
            # Use medium model as requested, with CPU fallback for stability
            model_name = "medium"
            
            # Try CUDA first, but fallback to CPU if there are issues
            if self.device == "cuda":
                try:
                    self.whisper_model = whisper.load_model(model_name, device="cuda")
                    logger.info(f"Loaded Whisper {model_name} model on CUDA")
                except Exception as e:
                    logger.warning(f"Failed to load Whisper on CUDA: {e}")
                    logger.info("Falling back to CPU for Whisper...")
                    self.whisper_model = whisper.load_model(model_name, device="cpu")
                    self.device = "cpu"  # Update device for consistency
            else:
                self.whisper_model = whisper.load_model(model_name, device="cpu")
                logger.info(f"Loaded Whisper {model_name} model on CPU")
        
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            logger.info("Trying smaller base model...")
            try:
                self.whisper_model = whisper.load_model("base", device="cpu")
                logger.info("Loaded Whisper base model on CPU as fallback")
            except Exception as e2:
                logger.error(f"Failed to load any Whisper model: {e2}")
                raise RuntimeError("Could not load Whisper model")
        
        # Load translation model
        logger.info("Loading translation model...")
        try:
            # Use CPU for translation to avoid memory conflicts
            self.translator = pipeline(
                "translation",
                model="Helsinki-NLP/opus-mt-es-en",
                device=-1  # Force CPU
            )
            logger.info("Translation model loaded on CPU")
        except Exception as e:
            logger.error(f"Failed to load translation model: {e}")
            raise RuntimeError("Could not load translation model")
        
        # Initialize TTS
        logger.info("Initializing TTS engine...")
        self.setup_tts()
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def setup_tts(self):
        """Setup TTS engine"""
        if self.use_edge_tts:
            try:
                import edge_tts
                self.tts_engine = "edge_tts"
                logger.info("Edge TTS configured successfully")
                return
            except ImportError:
                logger.warning("Edge TTS not available, falling back to pyttsx3")
        
        # Standard pyttsx3 setup
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Select best English voice
                english_voices = [v for v in voices if 'english' in v.name.lower() or 'en' in v.id.lower()]
                if english_voices:
                    selected = english_voices[0]
                    for voice in english_voices:
                        if any(name in voice.name.lower() for name in ['zira', 'aria', 'hazel']):
                            selected = voice
                            break
                    
                    self.tts_engine.setProperty('voice', selected.id)
                    logger.info(f"Selected voice: {selected.name}")
                
                self.tts_engine.setProperty('rate', 175)
                self.tts_engine.setProperty('volume', 1.0)
            
            logger.info("System TTS configured successfully")
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.tts_engine = None
    
    def get_video_info(self, video_path):
        """Get video information"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
    
    def split_video_into_segments(self, video_path, output_dir, segment_length):
        """Split video into smaller segments for processing"""
        logger.info(f"Splitting video into {segment_length}-second segments...")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-c', 'copy',  # Copy streams without re-encoding
                '-f', 'segment',
                '-segment_time', str(segment_length),
                '-segment_format', 'mp4',
                '-reset_timestamps', '1',
                os.path.join(output_dir, 'segment_%03d.mp4')
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                # Get list of created segments
                segments = sorted([f for f in os.listdir(output_dir) if f.startswith('segment_') and f.endswith('.mp4')])
                logger.info(f"Created {len(segments)} segments")
                return [os.path.join(output_dir, seg) for seg in segments]
            else:
                logger.error(f"Video splitting failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Video splitting failed: {e}")
            return None
    
    def extract_audio_segment(self, video_path, output_path):
        """Extract audio from video segment with noise reduction and normalization"""
        try:
            cmd = [
                'ffmpeg', '-y', '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # 16kHz sample rate for Whisper
                '-ac', '1',  # Mono
                '-af', 'volume=0.5,highpass=f=80,lowpass=f=8000,dynaudnorm',  # Audio filters
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Verify audio file has content
                if self.check_audio_content(output_path):
                    return str(output_path)
                else:
                    logger.warning(f"Audio file appears to be silent or corrupted")
                    return None
            else:
                logger.error(f"Audio extraction failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return None
    
    def check_audio_content(self, audio_path):
        """Check if audio file has actual content (not just silence)"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-select_streams', 'a:0', '-of', 'csv=p=0', str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                if duration > 0.1:  # At least 0.1 seconds
                    return True
            
            return False
            
        except Exception:
            return True  # Assume it's OK if we can't check
    
    def transcribe_audio_segment(self, audio_path, max_retries=3):
        """Transcribe audio segment with robust error handling"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Transcription attempt {attempt + 1}/{max_retries}")
                
                # Load audio with error checking
                import librosa
                import numpy as np
                
                # Load audio and check for issues
                audio_data, sr = librosa.load(audio_path, sr=16000)
                
                # Check for problematic audio
                if len(audio_data) == 0:
                    logger.warning("Audio file is empty")
                    return ""
                
                # Check for all zeros or NaN
                if np.all(audio_data == 0):
                    logger.warning("Audio contains only silence")
                    return ""
                
                if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                    logger.warning("Audio contains NaN or Inf values, cleaning...")
                    audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=0.0, neginf=0.0)
                
                # Normalize audio to prevent overflow
                if np.max(np.abs(audio_data)) > 0:
                    audio_data = audio_data / np.max(np.abs(audio_data)) * 0.9
                
                # Check RMS energy to detect very quiet audio
                rms = np.sqrt(np.mean(audio_data**2))
                if rms < 1e-5:  # Very quiet audio
                    logger.warning("Audio is very quiet, may contain little speech")
                    if rms < 1e-7:  # Extremely quiet
                        return ""
                
                # Save cleaned audio temporarily
                cleaned_audio_path = audio_path.replace('.wav', '_cleaned.wav')
                import soundfile as sf
                sf.write(cleaned_audio_path, audio_data, 16000)
                
                # Transcribe with Whisper
                result = self.whisper_model.transcribe(
                    cleaned_audio_path,
                    language="es",  # Specify source language
                    fp16=False,     # Disable FP16 to avoid numerical issues
                    temperature=0.0, # Deterministic output
                    no_speech_threshold=0.6,  # Higher threshold for speech detection
                    logprob_threshold=-1.0,   # Conservative logprob threshold
                    compression_ratio_threshold=2.4  # Conservative compression threshold
                )
                
                # Clean up temporary file
                try:
                    os.remove(cleaned_audio_path)
                except:
                    pass
                
                text = result["text"].strip()
                
                # Validate transcription
                if len(text) == 0:
                    logger.warning("No text transcribed")
                    return ""
                
                # Check for repetitive output (common Whisper issue)
                words = text.split()
                if len(words) > 10:
                    unique_words = len(set(words))
                    if unique_words / len(words) < 0.3:  # Less than 30% unique words
                        logger.warning("Transcription appears repetitive, may be hallucination")
                        if attempt < max_retries - 1:
                            continue
                
                logger.info(f"Transcription successful: {len(text)} characters")
                return text
                
            except Exception as e:
                logger.error(f"Transcription attempt {attempt + 1} failed: {e}")
                
                if "Expected parameter logits" in str(e) or "nan" in str(e).lower():
                    logger.warning("Detected NaN/logits error, trying with different parameters...")
                    
                    # Try with more conservative settings
                    try:
                        result = self.whisper_model.transcribe(
                            audio_path,
                            language="es",
                            fp16=False,
                            temperature=0.0,
                            beam_size=1,  # Use greedy decoding
                            best_of=1,    # Single attempt
                            no_speech_threshold=0.8,  # Very high threshold
                        )
                        
                        text = result["text"].strip()
                        if text:
                            logger.info(f"Conservative transcription successful: {len(text)} characters")
                            return text
                    except Exception as e2:
                        logger.error(f"Conservative transcription also failed: {e2}")
                
                if attempt == max_retries - 1:
                    logger.error(f"All transcription attempts failed")
                    return ""
                
                # Wait before retry
                time.sleep(2)
        
        return ""
    
    def translate_text(self, text):
        """Translate text with chunking for long content"""
        if not text.strip():
            return ""
        
        try:
            # Split into smaller chunks
            max_chunk = 400
            words = text.split()
            chunks = []
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) > max_chunk and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word) + 1
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Translate chunks
            translated_chunks = []
            for chunk in chunks:
                result = self.translator(chunk)
                translated_chunks.append(result[0]['translation_text'])
            
            return ' '.join(translated_chunks)
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    async def generate_audio_edge_tts(self, text, output_path):
        """Generate audio using Edge TTS"""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, self.edge_voice)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Edge TTS failed: {e}")
            return None
    
    def generate_audio_segment(self, text, output_path):
        """Generate audio for text segment"""
        if not text.strip():
            return None
        
        try:
            if self.use_edge_tts and self.tts_engine == "edge_tts":
                # Use Edge TTS
                import asyncio
                
                async def generate():
                    return await self.generate_audio_edge_tts(text, output_path)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(generate())
                loop.close()
                
                if result and os.path.exists(result):
                    return result
            
            # Fallback to system TTS
            if self.tts_engine and self.tts_engine != "edge_tts":
                self.tts_engine.save_to_file(text, str(output_path))
                self.tts_engine.runAndWait()
                
                if os.path.exists(output_path):
                    return str(output_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None
    
    def replace_segment_audio(self, video_path, audio_path, output_path):
        """Replace audio in video segment"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                '-map', '0:v:0',
                '-map', '1:a:0',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return str(output_path)
            else:
                logger.error(f"Audio replacement failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Audio replacement failed: {e}")
            return None
    
    def combine_video_segments(self, segment_paths, output_path):
        """Combine processed video segments"""
        try:
            # Create file list for FFmpeg
            list_file = tempfile.mktemp(suffix=".txt")
            
            with open(list_file, 'w') as f:
                for segment_path in segment_paths:
                    f.write(f"file '{os.path.abspath(segment_path)}'\n")
            
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy', str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            # Clean up
            try:
                os.remove(list_file)
            except:
                pass
            
            if result.returncode == 0:
                return str(output_path)
            else:
                logger.error(f"Video combination failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Video combination failed: {e}")
            return None
    
    def translate_long_video(self, input_video_path, output_video_path, progress_callback=None):
        """Translate a long video using segment-based processing"""
        start_time = time.time()
        
        # Get video info
        video_info = self.get_video_info(input_video_path)
        if not video_info:
            logger.error("Could not get video information")
            return None
        
        # Calculate video duration
        duration = float(video_info.get('format', {}).get('duration', 0))
        logger.info(f"Video duration: {timedelta(seconds=int(duration))} ({duration:.1f} seconds)")
        
        if duration > 7200:  # 2 hours
            logger.warning(f"Very long video detected ({duration/3600:.1f} hours). This may take a while...")
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix="long_video_")
        logger.info(f"Working directory: {temp_dir}")
        
        try:
            # Step 1: Split video into segments
            segments_dir = os.path.join(temp_dir, "segments")
            video_segments = self.split_video_into_segments(input_video_path, segments_dir, self.segment_length)
            
            if not video_segments:
                logger.error("Failed to split video")
                return None
            
            # Step 2: Process each segment
            processed_segments = []
            total_segments = len(video_segments)
            
            for i, segment_path in enumerate(video_segments):
                segment_num = i + 1
                logger.info(f"\n--- Processing segment {segment_num}/{total_segments} ---")
                
                if progress_callback:
                    progress_callback(segment_num, total_segments, "processing")
                
                # Extract audio from segment
                audio_path = os.path.join(temp_dir, f"audio_{i:03d}.wav")
                if not self.extract_audio_segment(segment_path, audio_path):
                    logger.error(f"Failed to extract audio from segment {segment_num}")
                    continue
                
                # Transcribe segment
                logger.info(f"Transcribing segment {segment_num}...")
                original_text = self.transcribe_audio_segment(audio_path)
                if not original_text:
                    logger.warning(f"No text transcribed from segment {segment_num}")
                    # Copy original segment if no transcription
                    processed_segments.append(segment_path)
                    continue
                
                logger.info(f"Segment {segment_num} text: {original_text[:100]}...")
                
                # Translate segment
                logger.info(f"Translating segment {segment_num}...")
                translated_text = self.translate_text(original_text)
                logger.info(f"Segment {segment_num} translation: {translated_text[:100]}...")
                
                # Generate new audio
                logger.info(f"Generating audio for segment {segment_num}...")
                new_audio_path = os.path.join(temp_dir, f"new_audio_{i:03d}.wav")
                if not self.generate_audio_segment(translated_text, new_audio_path):
                    logger.warning(f"Failed to generate audio for segment {segment_num}")
                    # Use original segment if audio generation fails
                    processed_segments.append(segment_path)
                    continue
                
                # Replace audio in segment
                logger.info(f"Replacing audio in segment {segment_num}...")
                processed_segment_path = os.path.join(temp_dir, f"processed_{i:03d}.mp4")
                if self.replace_segment_audio(segment_path, new_audio_path, processed_segment_path):
                    processed_segments.append(processed_segment_path)
                else:
                    logger.warning(f"Failed to replace audio in segment {segment_num}")
                    processed_segments.append(segment_path)
                
                # Clean up segment temp files to save space
                for temp_file in [audio_path, new_audio_path]:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
                
                # Force garbage collection
                gc.collect()
                
                elapsed = time.time() - start_time
                avg_time_per_segment = elapsed / segment_num
                estimated_total = avg_time_per_segment * total_segments
                remaining = estimated_total - elapsed
                
                logger.info(f"Segment {segment_num} completed. "
                          f"Elapsed: {timedelta(seconds=int(elapsed))}, "
                          f"ETA: {timedelta(seconds=int(remaining))}")
            
            # Step 3: Combine all processed segments
            logger.info(f"\nCombining {len(processed_segments)} segments...")
            if progress_callback:
                progress_callback(total_segments, total_segments, "combining")
            
            final_result = self.combine_video_segments(processed_segments, output_video_path)
            
            if final_result:
                total_time = time.time() - start_time
                logger.info(f"✅ Translation completed in {timedelta(seconds=int(total_time))}")
                return final_result
            else:
                logger.error("Failed to combine segments")
                return None
            
        except Exception as e:
            logger.error(f"Long video translation failed: {e}")
            return None
        
        finally:
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info("Temporary files cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

def progress_callback(current, total, stage):
    """Simple progress callback"""
    percentage = (current / total) * 100
    print(f"Progress: {current}/{total} ({percentage:.1f}%) - {stage}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate long videos (up to 2+ hours)')
    parser.add_argument('input_video', help='Path to input Spanish video')
    parser.add_argument('output_video', help='Path to output English video')
    parser.add_argument('--edge-tts', action='store_true', help='Use Edge TTS for better quality')
    parser.add_argument('--voice', default='en-US-AriaNeural', help='Voice for Edge TTS')
    parser.add_argument('--segment-length', type=int, default=600, help='Segment length in seconds (default: 600 = 10 minutes)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_video):
        print(f"Error: Input video not found: {args.input_video}")
        sys.exit(1)
    
    # Initialize translator
    try:
        translator = LongVideoTranslator(
            use_edge_tts=args.edge_tts,
            edge_voice=args.voice,
            segment_length=args.segment_length
        )
    except Exception as e:
        print(f"Error initializing translator: {e}")
        sys.exit(1)
    
    # Translate video
    print(f"🚀 Starting translation of long video...")
    print(f"📹 Input: {args.input_video}")
    print(f"📹 Output: {args.output_video}")
    print(f"⚙️  Segment length: {args.segment_length} seconds")
    print(f"🎤 TTS: {'Edge TTS' if args.edge_tts else 'System TTS'}")
    if args.edge_tts:
        print(f"🗣️  Voice: {args.voice}")
    
    result = translator.translate_long_video(args.input_video, args.output_video, progress_callback)
    
    if result:
        print(f"\n✅ Translation completed successfully!")
        print(f"📹 Output: {args.output_video}")
    else:
        print(f"\n❌ Translation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()