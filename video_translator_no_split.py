#!/usr/bin/env python3
"""
Video Translator using FFmpeg instead of MoviePy
Much more reliable and faster installation
"""

import os
import sys
import whisper
import torch
from transformers import pipeline
import pyttsx3
import tempfile
from pathlib import Path
import logging
import subprocess
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoTranslator:
    def __init__(self, use_edge_tts=False, edge_voice="en-US-AriaNeural"):
        """Initialize the video translator"""
        logger.info("Initializing Video Translator with FFmpeg backend...")
        
        # Check if FFmpeg is available
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
        
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
        self.use_edge_tts = use_edge_tts
        self.edge_voice = edge_voice
        logger.info(f"Initializing TTS engine (Edge TTS: {use_edge_tts}, Voice: {edge_voice})...")
        self.setup_tts()
        
        logger.info("Video Translator initialized successfully!")
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def setup_tts(self):
        """Setup TTS engine with better voice selection"""
        if self.use_edge_tts:
            # Edge TTS setup
            try:
                import edge_tts
                self.tts_engine = "edge_tts"
                logger.info("Edge TTS configured successfully")
                return
            except ImportError:
                logger.warning("Edge TTS not available, falling back to pyttsx3")
        
        # Standard pyttsx3 setup
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                logger.info(f"Found {len(voices)} voices:")
                
                # List all available voices
                english_voices = []
                for i, voice in enumerate(voices):
                    logger.info(f"  Voice {i}: {voice.name} (ID: {voice.id})")
                    if any(keyword in voice.name.lower() for keyword in ['english', 'en-', 'zira', 'david', 'hazel', 'aria']):
                        english_voices.append(voice)
                
                # Select the best English voice
                selected_voice = None
                if english_voices:
                    # Prefer high-quality voices (Zira, Aria, David on Windows)
                    for voice in english_voices:
                        if any(name in voice.name.lower() for name in ['zira', 'aria', 'hazel']):
                            selected_voice = voice
                            break
                    
                    # Fallback to any English voice
                    if not selected_voice:
                        selected_voice = english_voices[0]
                
                if selected_voice:
                    self.tts_engine.setProperty('voice', selected_voice.id)
                    logger.info(f"Selected voice: {selected_voice.name}")
                else:
                    logger.warning("No English voice found, using default")
                
                # Optimize settings for better quality
                self.tts_engine.setProperty('rate', 175)  # Slightly faster
                self.tts_engine.setProperty('volume', 1.0)  # Full volume
                logger.info("TTS engine configured successfully")
            else:
                logger.warning("No voices found for TTS")
                
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.tts_engine = None
    
    async def generate_audio_edge_tts(self, text, output_path, voice="en-US-AriaNeural"):
        """Generate audio using Edge TTS (high quality)"""
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Edge TTS generation failed: {e}")
            return None
    
    def get_video_info(self, video_path):
        """Get video information using FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return info
            else:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
    
    def extract_audio_ffmpeg(self, video_path, output_path=None):
        """Extract audio from video using FFmpeg"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")
        
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            cmd = [
                'ffmpeg', '-y', '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # 16kHz sample rate for Whisper
                '-ac', '1',  # Mono
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Audio extracted to {output_path}")
                return str(output_path)
            else:
                logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
                return None
                
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
    
    def generate_audio_tts(self, text, output_path=None):
        """Generate audio using TTS with better error handling"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")
        
        logger.info("Generating audio with TTS...")
        
        # Use Edge TTS if available
        if self.use_edge_tts and self.tts_engine == "edge_tts":
            try:
                import asyncio
                import edge_tts
                
                logger.info(f"Using Edge TTS with voice: {self.edge_voice}")
                
                async def generate_edge():
                    return await self.generate_audio_edge_tts(text, output_path, self.edge_voice)
                
                # Run async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(generate_edge())
                loop.close()
                
                if result and os.path.exists(result):
                    logger.info(f"Edge TTS audio generated: {result}")
                    return result
                else:
                    logger.warning("Edge TTS failed, falling back to pyttsx3")
                    
            except Exception as e:
                logger.warning(f"Edge TTS failed: {e}, falling back to pyttsx3")
        
        # Fallback to pyttsx3 or if Edge TTS is not enabled
        if not self.tts_engine or self.tts_engine == "edge_tts":
            logger.error("TTS engine not available")
            return None
        
        try:
            # Split very long text into smaller chunks to avoid TTS timeouts
            max_chunk_length = 500  # characters
            if len(text) > max_chunk_length:
                logger.info(f"Text is long ({len(text)} chars), splitting into chunks...")
                
                # Split by sentences first
                import re
                sentences = re.split(r'[.!?]+', text)
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_chunk_length:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Generate audio for each chunk and combine
                chunk_files = []
                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        chunk_file = tempfile.mktemp(suffix=f"_chunk_{i}.wav")
                        logger.info(f"Generating chunk {i+1}/{len(chunks)}")
                        
                        self.tts_engine.save_to_file(chunk, chunk_file)
                        self.tts_engine.runAndWait()
                        
                        if os.path.exists(chunk_file):
                            chunk_files.append(chunk_file)
                        else:
                            logger.warning(f"Chunk {i+1} was not generated")
                
                if chunk_files:
                    # Combine all chunks using FFmpeg
                    self.combine_audio_files(chunk_files, output_path)
                    
                    # Clean up chunk files
                    for chunk_file in chunk_files:
                        try:
                            os.remove(chunk_file)
                        except:
                            pass
                else:
                    logger.error("No audio chunks were generated")
                    return None
            else:
                # Generate single audio file for short text
                self.tts_engine.save_to_file(text, str(output_path))
                self.tts_engine.runAndWait()
            
            if os.path.exists(output_path):
                logger.info(f"Audio generated: {output_path}")
                return str(output_path)
            else:
                logger.error("Audio file was not created")
                return None
                
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None
    
    def combine_audio_files(self, audio_files, output_path):
        """Combine multiple audio files using FFmpeg"""
        try:
            # Create a temporary file list for FFmpeg
            list_file = tempfile.mktemp(suffix=".txt")
            
            with open(list_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
            
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy', str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Clean up list file
            try:
                os.remove(list_file)
            except:
                pass
            
            if result.returncode != 0:
                logger.error(f"Audio combination failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Audio combination failed: {e}")
            return False
    
    def combine_video_audio_ffmpeg(self, video_path, audio_path, output_path):
        """Combine video with new audio using FFmpeg"""
        logger.info("Combining video with new audio...")
        
        try:
            # Get video duration
            video_info = self.get_video_info(video_path)
            if not video_info:
                logger.error("Could not get video information")
                return None
            
            # Find video stream
            video_duration = None
            for stream in video_info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_duration = float(stream.get('duration', 0))
                    break
            
            if not video_duration:
                # Fallback to format duration
                video_duration = float(video_info.get('format', {}).get('duration', 0))
            
            if not video_duration:
                logger.error("Could not determine video duration")
                return None
            
            logger.info(f"Video duration: {video_duration} seconds")
            
            # Combine video and audio
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),  # Input video
                '-i', str(audio_path),  # Input audio
                '-c:v', 'copy',  # Copy video stream
                '-c:a', 'aac',  # Encode audio as AAC
                '-shortest',  # End when shortest input ends
                '-map', '0:v:0',  # Use video from first input
                '-map', '1:a:0',  # Use audio from second input
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"Final video created: {output_path}")
                return str(output_path)
            else:
                logger.error(f"FFmpeg video combination failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Video combination failed: {e}")
            return None
    
    def translate_video(self, input_video_path, output_video_path):
        """Complete video translation pipeline"""
        logger.info(f"Starting video translation: {input_video_path} -> {output_video_path}")
        
        temp_files = []
        
        try:
            # Step 1: Extract audio
            temp_audio = tempfile.mktemp(suffix=".wav")
            temp_files.append(temp_audio)
            
            extracted_audio = self.extract_audio_ffmpeg(input_video_path, temp_audio)
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
            
            new_audio_path = self.generate_audio_tts(translated_text, temp_new_audio)
            if not new_audio_path:
                return None
            
            # Step 5: Create final video
            result = self.combine_video_audio_ffmpeg(input_video_path, new_audio_path, output_video_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Video translation failed: {e}")
            return None
        
        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass

def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate video from Spanish to English using FFmpeg')
    parser.add_argument('input_video', help='Path to input Spanish video')
    parser.add_argument('output_video', help='Path to output English video')
    parser.add_argument('--edge-tts', action='store_true', help='Use Edge TTS for better voice quality')
    parser.add_argument('--voice', default='en-US-AriaNeural', help='Voice to use with Edge TTS')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_video):
        print(f"Error: Input video file not found: {args.input_video}")
        sys.exit(1)
    
    # Initialize translator
    try:
        translator = VideoTranslator(use_edge_tts=args.edge_tts, edge_voice=args.voice)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
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