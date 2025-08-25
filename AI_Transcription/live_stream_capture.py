import asyncio
import subprocess
import threading
import queue
import time
import numpy as np
import io
from typing import Optional, Callable, Dict, Any
from collections import deque

class LiveStreamCapture:
    """Real-time audio capture from live video streams using chunked processing"""
    
    def __init__(self, chunk_duration: float = 3.0):
        """
        Initialize live stream capture
        
        Args:
            chunk_duration: Duration of each audio chunk in seconds
        """
        self.chunk_duration = chunk_duration
        self.sample_rate = 16000
        self.chunk_size = int(self.sample_rate * chunk_duration)
        
        self.audio_queue = queue.Queue(maxsize=10)
        self.is_capturing = False
        self.process = None
        self.capture_thread = None
        
        # Audio buffer for overlapping chunks
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 10))  # 10 second buffer
        
    async def start_live_capture(self, stream_url: str, callback: Callable[[np.ndarray, float], None]):
        """
        Start capturing live audio stream in chunks
        
        Args:
            stream_url: Live stream URL
            callback: Function to call with each audio chunk (audio_data, timestamp)
        """
        if self.is_capturing:
            raise RuntimeError("Already capturing")
            
        self.is_capturing = True
        
        # Get stream info and audio URL
        audio_url = await self._get_live_audio_url(stream_url)
        
        # Start ffmpeg process for continuous streaming
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', audio_url,
            '-f', 's16le',  # Raw 16-bit PCM
            '-acodec', 'pcm_s16le',
            '-ar', str(self.sample_rate),
            '-ac', '1',  # Mono
            '-buffer_size', '32768',
            '-fflags', 'nobuffer',
            '-flags', 'low_delay',
            '-fflags', '+discardcorrupt',
            'pipe:1'
        ]
        
        try:
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Start audio processing thread
            self.capture_thread = threading.Thread(
                target=self._process_audio_stream,
                args=(callback,),
                daemon=True
            )
            self.capture_thread.start()
            
            print(f"✅ Started live capture from: {stream_url}")
            
        except Exception as e:
            self.is_capturing = False
            raise Exception(f"Failed to start live capture: {e}")
    
    def _process_audio_stream(self, callback: Callable[[np.ndarray, float], None]):
        """Process continuous audio stream in separate thread"""
        bytes_per_sample = 2  # 16-bit = 2 bytes
        chunk_bytes = self.chunk_size * bytes_per_sample
        
        buffer = b''
        chunk_count = 0
        start_time = time.time()
        
        try:
            while self.is_capturing and self.process:
                # Read raw audio data
                data = self.process.stdout.read(4096)
                
                if not data:
                    break
                    
                buffer += data
                
                # Process complete chunks
                while len(buffer) >= chunk_bytes:
                    chunk_data = buffer[:chunk_bytes]
                    buffer = buffer[chunk_bytes:]
                    
                    # Convert to numpy array
                    audio_chunk = np.frombuffer(chunk_data, dtype=np.int16)
                    audio_chunk = audio_chunk.astype(np.float32) / 32768.0  # Normalize
                    
                    # Add to buffer for overlapping processing
                    self.audio_buffer.extend(audio_chunk)
                    
                    # Calculate timestamp
                    timestamp = start_time + (chunk_count * self.chunk_duration)
                    
                    # Call callback with audio chunk
                    try:
                        callback(audio_chunk, timestamp)
                    except Exception as e:
                        print(f"Callback error: {e}")
                    
                    chunk_count += 1
                    
        except Exception as e:
            print(f"Audio stream processing error: {e}")
        finally:
            self._cleanup()
    
    async def _get_live_audio_url(self, stream_url: str) -> str:
        """Extract live audio stream URL using yt-dlp"""
        import yt_dlp
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(stream_url, download=False)
                
                if 'entries' in info:
                    video_info = info['entries'][0]
                else:
                    video_info = info
                
                # Check if it's a live stream
                if not video_info.get('is_live', False):
                    print("⚠️  Warning: This doesn't appear to be a live stream")
                
                # Get audio URL
                formats = video_info.get('formats', [])
                
                # Prefer audio-only streams for live content
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                if audio_formats:
                    # Sort by quality but prefer lower latency
                    audio_formats.sort(key=lambda x: (x.get('abr', 0) or 0, -x.get('filesize', 0) or 0))
                    return audio_formats[0]['url']
                
                # Fallback to best available
                best_format = None
                for fmt in formats:
                    if fmt.get('acodec') != 'none':
                        best_format = fmt
                        break
                
                if not best_format:
                    raise ValueError("No audio stream found")
                
                return best_format['url']
                
        except Exception as e:
            raise Exception(f"Failed to extract audio URL: {e}")
    
    def get_overlapping_chunk(self, overlap_duration: float = 1.0) -> Optional[np.ndarray]:
        """
        Get overlapping audio chunk for better transcription continuity
        
        Args:
            overlap_duration: Duration of overlap in seconds
            
        Returns:
            Overlapping audio chunk or None
        """
        overlap_samples = int(self.sample_rate * overlap_duration)
        
        if len(self.audio_buffer) >= overlap_samples:
            # Get last N samples from buffer
            overlap_data = list(self.audio_buffer)[-overlap_samples:]
            return np.array(overlap_data, dtype=np.float32)
        
        return None
    
    def stop_capture(self):
        """Stop live audio capture"""
        self.is_capturing = False
        self._cleanup()
        print("🛑 Live capture stopped")
    
    def _cleanup(self):
        """Clean up resources"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1)
    
    def is_live_stream(self, url: str) -> bool:
        """Check if URL is a live stream"""
        import yt_dlp
        
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    video_info = info['entries'][0]
                else:
                    video_info = info
                
                return video_info.get('is_live', False)
        except:
            return False
    
    def get_stream_info(self, url: str) -> Dict[str, Any]:
        """Get stream information"""
        import yt_dlp
        
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    video_info = info['entries'][0]
                else:
                    video_info = info
                
                return {
                    'title': video_info.get('title', 'Unknown'),
                    'uploader': video_info.get('uploader', 'Unknown'),
                    'is_live': video_info.get('is_live', False),
                    'duration': video_info.get('duration'),
                    'view_count': video_info.get('view_count'),
                    'description': video_info.get('description', '')[:200] + '...' if video_info.get('description', '') else '',
                }
        except Exception as e:
            return {'error': str(e)}


class BufferedAudioProcessor:
    """Handles buffered audio processing for overlapping transcription"""
    
    def __init__(self, buffer_duration: float = 6.0, overlap_duration: float = 2.0):
        """
        Initialize buffered processor
        
        Args:
            buffer_duration: Total buffer duration in seconds
            overlap_duration: Overlap between chunks in seconds
        """
        self.buffer_duration = buffer_duration
        self.overlap_duration = overlap_duration
        self.sample_rate = 16000
        
        self.buffer_size = int(self.sample_rate * buffer_duration)
        self.overlap_size = int(self.sample_rate * overlap_duration)
        
        self.audio_buffer = deque(maxlen=self.buffer_size)
        self.last_transcript = ""
        
    def add_audio(self, audio_chunk: np.ndarray):
        """Add new audio chunk to buffer"""
        self.audio_buffer.extend(audio_chunk)
    
    def get_processing_chunk(self) -> Optional[np.ndarray]:
        """Get audio chunk ready for transcription processing"""
        if len(self.audio_buffer) >= self.buffer_size:
            return np.array(list(self.audio_buffer), dtype=np.float32)
        return None
    
    def should_process(self) -> bool:
        """Check if buffer has enough audio for processing"""
        return len(self.audio_buffer) >= self.buffer_size
    
    def clear_processed_audio(self):
        """Remove processed audio, keeping overlap"""
        if len(self.audio_buffer) >= self.overlap_size:
            # Keep only the overlap portion
            overlap_data = list(self.audio_buffer)[-self.overlap_size:]
            self.audio_buffer.clear()
            self.audio_buffer.extend(overlap_data)