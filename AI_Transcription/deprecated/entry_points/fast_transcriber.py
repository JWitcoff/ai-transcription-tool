import torch
import whisper
import numpy as np
import asyncio
import threading
import queue
import time
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass
from collections import deque
import tempfile
import os

@dataclass
class TranscriptionSegment:
    """Represents a transcribed segment with timing and confidence"""
    text: str
    start_time: float
    end_time: float
    confidence: float = 0.0
    is_partial: bool = False

class FastTranscriber:
    """Optimized transcriber for real-time streaming with chunked processing"""
    
    def __init__(self, model_size: str = "base", device: str = None, use_faster_whisper: bool = True):
        """
        Initialize fast transcriber
        
        Args:
            model_size: Whisper model size (tiny, base, small for real-time)
            device: Device to use (auto-detected if None)
            use_faster_whisper: Use faster-whisper for better performance
        """
        self.model_size = model_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_faster_whisper = use_faster_whisper
        
        # Performance optimizations
        self.sample_rate = 16000
        self.chunk_duration = 5.0  # Process 5-second chunks (better for accuracy)
        self.overlap_duration = 1.0  # 1-second overlap
        
        # Threading - Larger queue to prevent overflow
        self.transcription_queue = queue.Queue(maxsize=20)
        self.result_queue = queue.Queue()
        self.worker_thread = None
        self.is_processing = False
        
        # Transcript continuity
        self.recent_segments = deque(maxlen=10)
        self.last_transcript = ""
        
        # Load model
        self.model = None
        self.is_faster_whisper = False
        self._load_model()
        
    def _load_model(self):
        """Load the transcription model with optimizations"""
        print(f"Loading {self.model_size} model for real-time transcription...")
        
        try:
            if self.use_faster_whisper:
                try:
                    from faster_whisper import WhisperModel
                    
                    # Use compute type optimization
                    compute_type = "float16" if self.device == "cuda" else "int8"
                    
                    self.model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=compute_type,
                        cpu_threads=4 if self.device == "cpu" else None
                    )
                    self.is_faster_whisper = True
                    print(f"✅ Loaded faster-whisper model ({compute_type})")
                    return
                    
                except ImportError:
                    print("⚠️  faster-whisper not available, using standard whisper")
                    self.use_faster_whisper = False
            
            # Fallback to standard whisper
            self.model = whisper.load_model(self.model_size, device=self.device)
            self.is_faster_whisper = False
            
            # Optimize for inference
            if hasattr(self.model, 'eval'):
                self.model.eval()
            
            print(f"✅ Loaded whisper model on {self.device}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def start_processing(self, callback: Optional[Callable[[TranscriptionSegment], None]] = None):
        """Start background transcription processing"""
        if self.is_processing:
            return
            
        self.is_processing = True
        self.worker_thread = threading.Thread(
            target=self._transcription_worker,
            args=(callback,),
            daemon=True
        )
        self.worker_thread.start()
        print("🚀 Started real-time transcription processing")
    
    def stop_processing(self):
        """Stop background processing"""
        self.is_processing = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("🛑 Stopped transcription processing")
    
    def transcribe_chunk(self, audio_data: np.ndarray, timestamp: float) -> Optional[TranscriptionSegment]:
        """
        Transcribe an audio chunk
        
        Args:
            audio_data: Audio data as numpy array
            timestamp: Timestamp of the chunk
            
        Returns:
            TranscriptionSegment or None
        """
        if not self.is_processing:
            self.start_processing()
        
        try:
            # Add to processing queue
            self.transcription_queue.put((audio_data, timestamp), timeout=0.1)
            
            # Try to get result (non-blocking)
            try:
                return self.result_queue.get_nowait()
            except queue.Empty:
                return None
                
        except queue.Full:
            # Skip if queue is full (prevents backlog)
            print("⚠️  Transcription queue full, skipping chunk")
            return None
    
    def _transcription_worker(self, callback: Optional[Callable[[TranscriptionSegment], None]]):
        """Background worker for transcription processing"""
        
        while self.is_processing:
            try:
                # Get audio chunk with timeout
                audio_data, timestamp = self.transcription_queue.get(timeout=0.5)
                
                # Transcribe the chunk
                start_time = time.time()
                segment = self._process_audio_chunk(audio_data, timestamp)
                process_time = time.time() - start_time
                
                if segment:
                    # Add to recent segments for context
                    self.recent_segments.append(segment)
                    
                    # Put result in queue
                    try:
                        self.result_queue.put_nowait(segment)
                    except queue.Full:
                        # Remove oldest result if queue is full
                        try:
                            self.result_queue.get_nowait()
                            self.result_queue.put_nowait(segment)
                        except queue.Empty:
                            pass
                    
                    # Call callback if provided
                    if callback:
                        try:
                            callback(segment)
                        except Exception as e:
                            print(f"Callback error: {e}")
                    
                    # Performance monitoring
                    real_time_factor = len(audio_data) / self.sample_rate / process_time
                    if real_time_factor < 1.0:
                        print(f"⚠️  Transcription slower than real-time: {real_time_factor:.2f}x")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Transcription worker error: {e}")
                continue
    
    def _process_audio_chunk(self, audio_data: np.ndarray, timestamp: float) -> Optional[TranscriptionSegment]:
        """Process individual audio chunk"""
        try:
            # Skip very short or silent audio
            if len(audio_data) < self.sample_rate * 0.5:  # Less than 0.5 seconds
                return None
            
            # Check for silence (simple energy-based detection)
            energy = np.mean(audio_data ** 2)
            if energy < 1e-6:  # Very quiet
                return None
            
            # Prepare audio for model
            if self.is_faster_whisper and hasattr(self.model, 'transcribe'):
                # faster-whisper expects float32 audio
                result = self._transcribe_with_faster_whisper(audio_data)
            else:
                # Standard whisper
                result = self._transcribe_with_whisper(audio_data)
            
            if result and result.get('text', '').strip():
                text = result['text'].strip()
                
                # Filter out repetitions and very short transcriptions
                if len(text) < 3 or text.lower() in ['um', 'uh', 'ah', 'hmm']:
                    return None
                
                # Check for repetition with recent segments
                if self._is_repetitive_text(text):
                    return None
                
                return TranscriptionSegment(
                    text=text,
                    start_time=timestamp,
                    end_time=timestamp + len(audio_data) / self.sample_rate,
                    confidence=result.get('confidence', 0.8),
                    is_partial=False
                )
            
            return None
            
        except Exception as e:
            print(f"Chunk processing error: {e}")
            return None
    
    def _transcribe_with_faster_whisper(self, audio_data: np.ndarray) -> Dict:
        """Transcribe using faster-whisper"""
        try:
            # faster-whisper transcription with compatible parameters
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=1,  # Faster beam search
                temperature=0.0,  # Deterministic
                no_speech_threshold=0.6,
                condition_on_previous_text=False,  # Faster for live streams
                word_timestamps=False,  # Skip word timing for speed
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine all segments
            text_parts = []
            avg_confidence = 0
            segment_count = 0
            
            for segment in segments:
                text_parts.append(segment.text)
                avg_confidence += getattr(segment, 'avg_logprob', -0.5)
                segment_count += 1
            
            if segment_count == 0:
                return {'text': '', 'confidence': 0.0}
            
            # Convert log probability to confidence score
            confidence = min(1.0, max(0.0, (avg_confidence / segment_count + 1.0)))
            
            return {
                'text': ''.join(text_parts),
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"faster-whisper error: {e}")
            return {'text': '', 'confidence': 0.0}
    
    def _transcribe_with_whisper(self, audio_data: np.ndarray) -> Dict:
        """Transcribe using standard whisper"""
        try:
            # Create temporary file for whisper
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                # Save audio as WAV
                import soundfile as sf
                sf.write(tmp_file.name, audio_data, self.sample_rate)
                
                # Transcribe
                result = self.model.transcribe(
                    tmp_file.name,
                    fp16=torch.cuda.is_available(),
                    condition_on_previous_text=False,
                    temperature=0.0,
                    beam_size=1,
                    best_of=1,
                    word_timestamps=False
                )
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                
                return {
                    'text': result.get('text', ''),
                    'confidence': 0.8  # Standard whisper doesn't provide confidence
                }
                
        except Exception as e:
            print(f"Standard whisper error: {e}")
            return {'text': '', 'confidence': 0.0}
    
    def _is_repetitive_text(self, text: str) -> bool:
        """Check if text is repetitive with recent segments"""
        text_lower = text.lower().strip()
        
        for segment in list(self.recent_segments)[-3:]:  # Check last 3 segments
            if segment.text.lower().strip() == text_lower:
                return True
        
        return False
    
    def get_recent_transcript(self, duration: float = 30.0) -> str:
        """Get transcript from recent segments"""
        current_time = time.time()
        recent_text = []
        
        for segment in self.recent_segments:
            if current_time - segment.end_time <= duration:
                recent_text.append(segment.text)
        
        return ' '.join(recent_text)
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        return {
            'queue_size': self.transcription_queue.qsize(),
            'result_queue_size': self.result_queue.qsize(),
            'recent_segments': len(self.recent_segments),
            'is_processing': self.is_processing,
            'model_size': self.model_size,
            'device': self.device,
            'uses_faster_whisper': self.use_faster_whisper
        }


class TranscriptBuffer:
    """Manages continuous transcript with intelligent text joining"""
    
    def __init__(self, max_duration: float = 300.0):  # 5 minutes
        self.max_duration = max_duration
        self.segments = deque()
        self.full_transcript = ""
        
    def add_segment(self, segment: TranscriptionSegment):
        """Add new transcription segment"""
        # Remove old segments
        current_time = segment.end_time
        while self.segments and current_time - self.segments[0].end_time > self.max_duration:
            self.segments.popleft()
        
        # Add new segment
        self.segments.append(segment)
        
        # Rebuild transcript
        self._rebuild_transcript()
    
    def _rebuild_transcript(self):
        """Rebuild full transcript from segments"""
        if not self.segments:
            self.full_transcript = ""
            return
        
        # Join segments with intelligent spacing
        text_parts = []
        last_end_time = 0
        
        for segment in self.segments:
            text = segment.text.strip()
            
            # Add spacing based on timing gaps
            if text_parts and segment.start_time - last_end_time > 2.0:  # 2+ second gap
                text_parts.append('\n\n')  # Paragraph break
            elif text_parts and not text_parts[-1].endswith(('.', '!', '?', '\n')):
                text_parts.append(' ')  # Regular space
            
            text_parts.append(text)
            last_end_time = segment.end_time
        
        self.full_transcript = ''.join(text_parts)
    
    def get_transcript(self) -> str:
        """Get current full transcript"""
        return self.full_transcript
    
    def get_recent_transcript(self, duration: float = 60.0) -> str:
        """Get transcript from last N seconds"""
        if not self.segments:
            return ""
        
        current_time = self.segments[-1].end_time
        recent_segments = []
        
        for segment in reversed(self.segments):
            if current_time - segment.end_time <= duration:
                recent_segments.append(segment)
            else:
                break
        
        # Rebuild recent transcript
        recent_segments.reverse()
        text_parts = []
        
        for segment in recent_segments:
            if text_parts:
                text_parts.append(' ')
            text_parts.append(segment.text.strip())
        
        return ''.join(text_parts)
    
    def clear(self):
        """Clear all segments"""
        self.segments.clear()
        self.full_transcript = ""