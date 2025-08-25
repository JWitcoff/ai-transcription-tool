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

class AudioTranscriber:
    def __init__(self, model_size: str = "base", device: Optional[str] = None, enable_diarization: bool = True):
        """
        Initialize AudioTranscriber with offline Whisper model and optional diarization.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run model on (cpu, cuda, etc.)
            enable_diarization: Whether to enable speaker diarization
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self.diarization_pipeline = None
        self.enable_diarization = enable_diarization and DIARIZATION_AVAILABLE
        self._load_model()
        if self.enable_diarization:
            self._load_diarization_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            print(f"Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            print("Whisper model loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    def _load_diarization_model(self):
        """Load the speaker diarization model."""
        try:
            print("Loading speaker diarization model...")
            # Use the default pretrained model for speaker diarization
            self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            print("Diarization model loaded successfully!")
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
            
            # Get transcription from Whisper
            result = self.model.transcribe(
                audio_file_path,
                word_timestamps=include_timestamps,
                verbose=True
            )
            
            # Add speaker diarization if enabled
            diarization_result = None
            if self.enable_diarization and self.diarization_pipeline:
                print("Performing speaker diarization...")
                try:
                    diarization_result = self.diarization_pipeline(audio_file_path)
                    print("Diarization completed!")
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
                "has_diarization": diarization_result is not None
            }
        except Exception as e:
            raise RuntimeError(f"Transcription error: {e}")
    
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