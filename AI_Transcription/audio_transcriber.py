import whisper
import os
import tempfile
import pyaudio
import wave
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import timedelta
try:
    from pyannote.audio import Pipeline
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False
    print("Warning: pyannote.audio not available. Diarization features disabled.")

try:
    from elevenlabs_scribe import ScribeClient, parse_words_from_response, group_words_into_segments
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs_scribe not available. Scribe features disabled.")

class AudioTranscriber:
    def __init__(self, model_size: str = "base", device: Optional[str] = None, enable_diarization: bool = True, diarization_provider: str = "auto"):
        """
        Initialize AudioTranscriber with offline Whisper model and optional diarization.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run model on (cpu, cuda, etc.)
            enable_diarization: Whether to enable speaker diarization
            diarization_provider: Diarization provider ('auto', 'pyannote', 'elevenlabs')
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self.diarization_pipeline = None
        self.elevenlabs_scribe = None
        self.diarization_provider = self._select_diarization_provider(diarization_provider, enable_diarization)
        self.enable_diarization = enable_diarization and (self.diarization_provider is not None)
        
        self._load_model()
        
        # Show diarization status
        if enable_diarization and not self.enable_diarization:
            print("⚠️  Speaker diarization: DISABLED (no providers available)")
            if not DIARIZATION_AVAILABLE and not ELEVENLABS_AVAILABLE:
                print("   Install pyannote: pip install pyannote.audio>=3.1.0")
                print("   OR configure ElevenLabs API key in .env file")
        elif not enable_diarization:
            print("ℹ️  Speaker diarization: DISABLED (not requested)")
        
        if self.enable_diarization:
            self._load_diarization_provider()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            print(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            print("Whisper model loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    def _select_diarization_provider(self, provider: str, enable_diarization: bool) -> Optional[str]:
        """Select the best available diarization provider."""
        if not enable_diarization:
            return None
            
        if provider == "elevenlabs":
            return "elevenlabs" if ELEVENLABS_AVAILABLE else None
        elif provider == "pyannote":
            return "pyannote" if DIARIZATION_AVAILABLE else None
        elif provider == "auto":
            # Prefer ElevenLabs for better accuracy
            if ELEVENLABS_AVAILABLE:
                return "elevenlabs"
            elif DIARIZATION_AVAILABLE:
                return "pyannote"
        
        return None
    
    def _load_diarization_provider(self):
        """Load the selected diarization provider."""
        if self.diarization_provider == "elevenlabs":
            self._load_elevenlabs_scribe()
        elif self.diarization_provider == "pyannote":
            self._load_pyannote_pipeline()
    
    def _load_elevenlabs_scribe(self):
        """Load ElevenLabs Scribe for diarization."""
        try:
            print("🎯 Loading ElevenLabs Scribe...")
            self.elevenlabs_scribe = ScribeClient()
            print("✅ Speaker diarization: ENABLED (ElevenLabs Scribe)")
            print("   • Up to 32 speakers supported")
            print("   • 96.7% accuracy + audio event detection")
        except Exception as e:
            print(f"Warning: Failed to load ElevenLabs Scribe: {e}")
            self.enable_diarization = False
            self.diarization_provider = None
    
    def _load_pyannote_pipeline(self):
        """Load pyannote.audio pipeline for diarization."""
        try:
            print("🎯 Loading pyannote speaker diarization...")
            self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            print("✅ Speaker diarization: ENABLED (pyannote.audio)")
            print("   Model: pyannote/speaker-diarization-3.1")
        except Exception as e:
            print(f"Warning: Failed to load diarization model: {e}")
            self.enable_diarization = False
        
    def transcribe_from_file(self, audio_file_path: str, include_timestamps: bool = False) -> Dict:
        """
        Transcribe audio from a file using offline Whisper with optional diarization.
        
        Args:
            audio_file_path: Path to audio file
            include_timestamps: Whether to include word-level timestamps
            
        Returns:
            Dictionary containing transcription results with speaker labels
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            print(f"Transcribing: {audio_file_path}")
            
            # Use ElevenLabs Scribe if available (handles both transcription and diarization)
            if self.enable_diarization and self.diarization_provider == "elevenlabs":
                return self._transcribe_with_elevenlabs(audio_file_path)
            
            # Otherwise use Whisper + optional pyannote diarization
            return self._transcribe_with_whisper(audio_file_path, include_timestamps)
            
        except Exception as e:
            raise RuntimeError(f"Transcription error: {e}")
    
    def _transcribe_with_elevenlabs(self, audio_file_path: str) -> Dict:
        """Transcribe using ElevenLabs Scribe (includes diarization)."""
        print("🚀 Using ElevenLabs Scribe for transcription + diarization")
        
        try:
            # Use file upload for local files
            raw_result = self.elevenlabs_scribe.transcribe_file(
                audio_file_path,
                diarize=True,
                num_speakers=None,  # Auto-detect
                use_multi_channel=False  # Single channel for now
            )
            
            # Parse words and group into segments
            words = parse_words_from_response(raw_result)
            segments = group_words_into_segments(words)
            
            # Extract unique speakers
            speakers = list(set(seg.speaker_id for seg in segments))
            
            # Format segments for compatibility
            formatted_segments = []
            for seg in segments:
                formatted_segments.append({
                    'speaker': seg.speaker_id,
                    'text': seg.text,
                    'start': seg.start,
                    'end': seg.end
                })
            
            # Convert to standard format
            return {
                "text": raw_result.get("text", ""),
                "language": raw_result.get("language_code", "auto-detected"),
                "segments": formatted_segments,
                "words": [{"text": w.text, "start": w.start, "end": w.end} for w in words],
                "has_diarization": True,
                "speakers": speakers,
                "provider": "elevenlabs_scribe",
                "raw_response": raw_result
            }
            
        except Exception as e:
            print(f"❌ ElevenLabs Scribe failed: {e}")
            print("   Falling back to Whisper...")
            # Fall back to Whisper
            return self._transcribe_with_whisper(audio_file_path, include_timestamps=True)
    
    def _transcribe_with_whisper(self, audio_file_path: str, include_timestamps: bool) -> Dict:
        """Transcribe using Whisper + optional pyannote diarization."""
        # Get transcription from Whisper
        result = self.model.transcribe(
            audio_file_path,
            word_timestamps=include_timestamps,
            verbose=True
        )
        
        # Add speaker diarization if enabled
        diarization_result = None
        if self.enable_diarization and self.diarization_provider == "pyannote":
            print("\n🎯 Performing speaker diarization...")
            print("   This may take a moment...")
            try:
                diarization_result = self.diarization_pipeline(audio_file_path)
                
                # Count speakers
                speakers = set()
                for _, _, speaker in diarization_result.itertracks(yield_label=True):
                    speakers.add(speaker)
                
                print(f"✅ Diarization completed! Found {len(speakers)} speaker(s)")
            except Exception as e:
                print(f"Diarization failed: {e}")
        
        # Combine transcription with speaker labels
        enhanced_segments = self._combine_transcription_and_diarization(
            result.get("segments", []), 
            diarization_result
        )
        
        return {
            "text": result["text"],
            "language": result["language"],
            "segments": enhanced_segments,
            "words": result.get("words", []) if include_timestamps else [],
            "has_diarization": diarization_result is not None,
            "provider": "whisper+pyannote" if diarization_result else "whisper"
        }
    
    def _combine_transcription_and_diarization(self, segments: List[Dict], diarization) -> List[Dict]:
        """
        Combine Whisper transcription segments with speaker diarization results.
        
        Args:
            segments: Whisper transcription segments
            diarization: Pyannote diarization result
            
        Returns:
            Enhanced segments with speaker labels
        """
        if not diarization:
            return segments
        
        enhanced_segments = []
        
        for segment in segments:
            segment_start = segment["start"]
            segment_end = segment["end"]
            segment_mid = (segment_start + segment_end) / 2
            
            # Find the speaker at the midpoint of this segment
            speaker = "Unknown"
            for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                if turn.start <= segment_mid <= turn.end:
                    speaker = f"Speaker {speaker_label}"
                    break
            
            enhanced_segment = segment.copy()
            enhanced_segment["speaker"] = speaker
            enhanced_segments.append(enhanced_segment)
        
        return enhanced_segments
    
    def transcribe_from_microphone(self, duration: int = 5) -> Dict:
        """
        Record and transcribe audio from microphone.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Dictionary containing transcription results
        """
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1
        rate = 44100
        
        p = pyaudio.PyAudio()
        
        stream = p.open(format=format,
                       channels=channels,
                       rate=rate,
                       input=True,
                       frames_per_buffer=chunk)
        
        print(f"Recording for {duration} seconds...")
        frames = []
        
        for _ in range(0, int(rate / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)
        
        print("Recording finished.")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            wf = wave.open(temp_audio.name, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            try:
                result = self.transcribe_from_file(temp_audio.name)
                os.unlink(temp_audio.name)
                return result
            except Exception as e:
                os.unlink(temp_audio.name)
                raise RuntimeError(f"Microphone transcription error: {e}")
    
    def export_transcription(self, result: Dict, output_file: str, format: str = "txt"):
        """
        Export transcription in various formats.
        
        Args:
            result: Transcription result dictionary
            output_file: Output file path
            format: Export format (txt, srt, vtt, json)
        """
        format = format.lower()
        
        if format == "txt":
            self._export_txt(result, output_file)
        elif format == "srt":
            self._export_srt(result, output_file)
        elif format == "vtt":
            self._export_vtt(result, output_file)
        elif format == "json":
            self._export_json(result, output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_txt(self, result: Dict, output_file: str):
        """Export as plain text with speaker labels if available."""
        with open(output_file, 'w', encoding='utf-8') as f:
            if result.get("has_diarization") and result.get("segments"):
                # Format with speaker labels
                current_speaker = None
                for segment in result["segments"]:
                    speaker = segment.get("speaker", "Unknown")
                    if speaker != current_speaker:
                        f.write(f"\n{speaker}:\n")
                        current_speaker = speaker
                    f.write(f"{segment['text'].strip()}\n")
            else:
                # Standard text output
                f.write(result["text"])
    
    def _export_srt(self, result: Dict, output_file: str):
        """Export as SRT subtitle format with speaker labels."""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result.get("segments", []), 1):
                start_time = self._seconds_to_srt_time(segment["start"])
                end_time = self._seconds_to_srt_time(segment["end"])
                
                # Include speaker label if available
                text = segment['text'].strip()
                if segment.get("speaker"):
                    text = f"[{segment['speaker']}] {text}"
                
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
    
    def _export_vtt(self, result: Dict, output_file: str):
        """Export as WebVTT format with speaker labels."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for segment in result.get("segments", []):
                start_time = self._seconds_to_vtt_time(segment["start"])
                end_time = self._seconds_to_vtt_time(segment["end"])
                
                # Include speaker label if available
                text = segment['text'].strip()
                if segment.get("speaker"):
                    text = f"[{segment['speaker']}] {text}"
                
                f.write(f"{start_time} --> {end_time}\n{text}\n\n")
    
    def _export_json(self, result: Dict, output_file: str):
        """Export as JSON format."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format."""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format."""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{milliseconds:03d}"
    
    def transcribe_batch(self, file_paths: List[str], output_dir: str = ".", format: str = "txt") -> List[Dict]:
        """
        Transcribe multiple files in batch.
        
        Args:
            file_paths: List of audio file paths
            output_dir: Output directory for transcriptions
            format: Export format
            
        Returns:
            List of transcription results
        """
        results = []
        os.makedirs(output_dir, exist_ok=True)
        
        for i, file_path in enumerate(file_paths, 1):
            print(f"\nProcessing file {i}/{len(file_paths)}: {file_path}")
            try:
                result = self.transcribe_from_file(file_path, include_timestamps=True)
                
                # Generate output filename
                base_name = Path(file_path).stem
                output_file = os.path.join(output_dir, f"{base_name}.{format}")
                
                # Export transcription
                self.export_transcription(result, output_file, format)
                result["output_file"] = output_file
                results.append(result)
                
                print(f"✓ Completed: {output_file}")
                
            except Exception as e:
                print(f"✗ Failed to process {file_path}: {e}")
                results.append({"file": file_path, "error": str(e)})
        
        return results

def main():
    print("=== Vibe Audio Transcriber ===")
    print("Loading AI model...")
    
    try:
        model_size = input("Choose model size (tiny/base/small/medium/large) [base]: ").strip() or "base"
        transcriber = AudioTranscriber(model_size=model_size)
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    while True:
        print("\n=== Main Menu ===")
        print("1. Transcribe single audio file")
        print("2. Batch transcribe multiple files")
        print("3. Record and transcribe from microphone")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == '1':
            file_path = input("Enter audio file path: ").strip()
            try:
                result = transcriber.transcribe_from_file(file_path, include_timestamps=True)
                print(f"\nDetected language: {result['language']}")
                print(f"Transcription: {result['text']}")
                
                save = input("\nExport transcription? (y/n): ").strip().lower()
                if save == 'y':
                    output_file = input("Enter output filename (without extension): ").strip()
                    format_choice = input("Choose format (txt/srt/vtt/json) [txt]: ").strip() or "txt"
                    
                    full_output = f"{output_file}.{format_choice}"
                    transcriber.export_transcription(result, full_output, format_choice)
                    print(f"✓ Transcription exported to {full_output}")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '2':
            file_paths = []
            print("Enter audio file paths (one per line, empty line to finish):")
            while True:
                path = input().strip()
                if not path:
                    break
                file_paths.append(path)
            
            if file_paths:
                output_dir = input("Output directory [./transcriptions]: ").strip() or "./transcriptions"
                format_choice = input("Choose format (txt/srt/vtt/json) [srt]: ").strip() or "srt"
                
                print(f"\nStarting batch transcription of {len(file_paths)} files...")
                results = transcriber.transcribe_batch(file_paths, output_dir, format_choice)
                
                successful = sum(1 for r in results if "error" not in r)
                print(f"\n✓ Batch completed: {successful}/{len(file_paths)} files processed successfully")
            else:
                print("No files provided.")
        
        elif choice == '3':
            duration = input("Recording duration in seconds (default 5): ").strip()
            duration = int(duration) if duration else 5
            
            try:
                result = transcriber.transcribe_from_microphone(duration)
                print(f"\nDetected language: {result['language']}")
                print(f"Transcription: {result['text']}")
                
                save = input("\nExport transcription? (y/n): ").strip().lower()
                if save == 'y':
                    output_file = input("Enter output filename (without extension): ").strip()
                    format_choice = input("Choose format (txt/srt/vtt/json) [txt]: ").strip() or "txt"
                    
                    full_output = f"{output_file}.{format_choice}"
                    transcriber.export_transcription(result, full_output, format_choice)
                    print(f"✓ Transcription exported to {full_output}")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()