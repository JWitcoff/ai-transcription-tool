import whisper
import torch
import os
from typing import Dict, Optional, List
import json
from pathlib import Path
from openai import OpenAI
import yt_dlp

# Import the proven audio transcriber
try:
    from audio_transcriber import AudioTranscriber
    ENHANCED_TRANSCRIBER_AVAILABLE = True
except ImportError:
    ENHANCED_TRANSCRIBER_AVAILABLE = False
    print("Warning: Enhanced AudioTranscriber not available. Using basic transcription.")

class Transcriber:
    """Handles audio transcription using OpenAI Whisper with enhanced features for uploaded files"""
    
    def __init__(self):
        self.model = None
        self.current_model_size = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.enhanced_transcriber = None
        
    def transcribe(self, audio_file: str, model_size: str = "base", 
                  language: Optional[str] = None, use_enhanced: bool = False, 
                  enable_diarization: bool = False, **kwargs) -> Dict:
        """
        Transcribe audio file using Whisper with optional enhanced features
        
        Args:
            audio_file: Path to audio file
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (e.g., 'en', 'es') or None for auto-detection
            use_enhanced: Use enhanced transcriber with speaker diarization support
            enable_diarization: Enable speaker diarization (requires use_enhanced=True)
            **kwargs: Additional whisper parameters
            
        Returns:
            Dictionary containing transcription results
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Use enhanced transcriber for uploaded files with advanced features
        if use_enhanced and ENHANCED_TRANSCRIBER_AVAILABLE:
            return self._transcribe_enhanced(audio_file, model_size, language, enable_diarization, **kwargs)
        
        # Fallback to basic transcription for streams
        return self._transcribe_basic(audio_file, model_size, language, **kwargs)
    
    def _transcribe_enhanced(self, audio_file: str, model_size: str, language: Optional[str], 
                           enable_diarization: bool, **kwargs) -> Dict:
        """Enhanced transcription with speaker diarization support"""
        try:
            # Initialize enhanced transcriber if needed
            if (self.enhanced_transcriber is None or 
                self.enhanced_transcriber.model_size != model_size):
                
                print(f"Loading enhanced transcriber with {model_size} model...")
                self.enhanced_transcriber = AudioTranscriber(
                    model_size=model_size,
                    device=self.device,
                    enable_diarization=enable_diarization
                )
            
            # Perform enhanced transcription
            result = self.enhanced_transcriber.transcribe_from_file(
                audio_file, 
                include_timestamps=True
            )
            
            # Add metadata for compatibility
            result['model_size'] = model_size
            result['audio_file'] = audio_file
            result['device'] = self.device
            result['enhanced'] = True
            
            return result
            
        except Exception as e:
            print(f"Enhanced transcription failed, falling back to basic: {e}")
            return self._transcribe_basic(audio_file, model_size, language, **kwargs)
    
    def _transcribe_basic(self, audio_file: str, model_size: str, language: Optional[str], **kwargs) -> Dict:
        """Basic transcription for streams and fallback"""
        # Load model if not loaded or different size requested
        if self.model is None or self.current_model_size != model_size:
            self._load_model(model_size)
        
        try:
            # Set transcription options
            options = {
                'language': language,
                'task': 'transcribe',
                'fp16': False,  # Use fp32 for better compatibility
                **kwargs
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            # Perform transcription
            result = self.model.transcribe(audio_file, **options)
            
            # Add metadata
            result['model_size'] = model_size
            result['audio_file'] = audio_file
            result['device'] = self.device
            result['enhanced'] = False
            
            return result
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_with_timestamps(self, audio_file: str, model_size: str = "base",
                                 language: Optional[str] = None) -> Dict:
        """
        Transcribe with detailed word-level timestamps
        
        Args:
            audio_file: Path to audio file
            model_size: Whisper model size
            language: Language code or None for auto-detection
            
        Returns:
            Dictionary with detailed timestamps
        """
        return self.transcribe(
            audio_file, 
            model_size=model_size,
            language=language,
            word_timestamps=True,
            verbose=True
        )
    
    def batch_transcribe(self, audio_files: List[str], model_size: str = "base",
                        language: Optional[str] = None) -> List[Dict]:
        """
        Transcribe multiple audio files
        
        Args:
            audio_files: List of audio file paths
            model_size: Whisper model size
            language: Language code or None for auto-detection
            
        Returns:
            List of transcription results
        """
        results = []
        
        # Load model once for all files
        if self.model is None or self.current_model_size != model_size:
            self._load_model(model_size)
        
        for audio_file in audio_files:
            try:
                result = self.transcribe(audio_file, model_size, language)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': str(e),
                    'audio_file': audio_file
                })
        
        return results
    
    def _load_model(self, model_size: str):
        """Load Whisper model"""
        try:
            print(f"Loading Whisper model: {model_size}")
            self.model = whisper.load_model(model_size, device=self.device)
            self.current_model_size = model_size
            print(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported languages"""
        return {
            'en': 'English',
            'zh': 'Chinese',
            'de': 'German',
            'es': 'Spanish',
            'ru': 'Russian',
            'ko': 'Korean',
            'fr': 'French',
            'ja': 'Japanese',
            'pt': 'Portuguese',
            'tr': 'Turkish',
            'pl': 'Polish',
            'ca': 'Catalan',
            'nl': 'Dutch',
            'ar': 'Arabic',
            'sv': 'Swedish',
            'it': 'Italian',
            'id': 'Indonesian',
            'hi': 'Hindi',
            'fi': 'Finnish',
            'vi': 'Vietnamese',
            'he': 'Hebrew',
            'uk': 'Ukrainian',
            'el': 'Greek',
            'ms': 'Malay',
            'cs': 'Czech',
            'ro': 'Romanian',
            'da': 'Danish',
            'hu': 'Hungarian',
            'ta': 'Tamil',
            'no': 'Norwegian',
            'th': 'Thai',
            'ur': 'Urdu',
            'hr': 'Croatian',
            'bg': 'Bulgarian',
            'lt': 'Lithuanian',
            'la': 'Latin',
            'mi': 'Maori',
            'ml': 'Malayalam',
            'cy': 'Welsh',
            'sk': 'Slovak',
            'te': 'Telugu',
            'fa': 'Persian',
            'lv': 'Latvian',
            'bn': 'Bengali',
            'sr': 'Serbian',
            'az': 'Azerbaijani',
            'sl': 'Slovenian',
            'kn': 'Kannada',
            'et': 'Estonian',
            'mk': 'Macedonian',
            'br': 'Breton',
            'eu': 'Basque',
            'is': 'Icelandic',
            'hy': 'Armenian',
            'ne': 'Nepali',
            'mn': 'Mongolian',
            'bs': 'Bosnian',
            'kk': 'Kazakh',
            'sq': 'Albanian',
            'sw': 'Swahili',
            'gl': 'Galician',
            'mr': 'Marathi',
            'pa': 'Punjabi',
            'si': 'Sinhala',
            'km': 'Khmer',
            'sn': 'Shona',
            'yo': 'Yoruba',
            'so': 'Somali',
            'af': 'Afrikaans',
            'oc': 'Occitan',
            'ka': 'Georgian',
            'be': 'Belarusian',
            'tg': 'Tajik',
            'sd': 'Sindhi',
            'gu': 'Gujarati',
            'am': 'Amharic',
            'yi': 'Yiddish',
            'lo': 'Lao',
            'uz': 'Uzbek',
            'fo': 'Faroese',
            'ht': 'Haitian creole',
            'ps': 'Pashto',
            'tk': 'Turkmen',
            'nn': 'Nynorsk',
            'mt': 'Maltese',
            'sa': 'Sanskrit',
            'lb': 'Luxembourgish',
            'my': 'Myanmar',
            'bo': 'Tibetan',
            'tl': 'Tagalog',
            'mg': 'Malagasy',
            'as': 'Assamese',
            'tt': 'Tatar',
            'haw': 'Hawaiian',
            'ln': 'Lingala',
            'ha': 'Hausa',
            'ba': 'Bashkir',
            'jw': 'Javanese',
            'su': 'Sundanese',
        }
    
    def export_transcript(self, transcript: Dict, format: str = "txt", 
                         output_file: Optional[str] = None) -> str:
        """
        Export transcript to different formats
        
        Args:
            transcript: Transcription result from whisper
            format: Export format ('txt', 'json', 'srt', 'vtt')
            output_file: Output file path (optional)
            
        Returns:
            Path to exported file or content string
        """
        if format == "txt":
            content = transcript.get("text", "")
            
        elif format == "json":
            content = json.dumps(transcript, indent=2, ensure_ascii=False)
            
        elif format == "srt":
            content = self._to_srt(transcript)
            
        elif format == "vtt":
            content = self._to_vtt(transcript)
            
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_file
        
        return content
    
    def _to_srt(self, transcript: Dict) -> str:
        """Convert transcript to SRT format"""
        srt_content = ""
        segments = transcript.get("segments", [])
        
        for i, segment in enumerate(segments, 1):
            start = self._seconds_to_srt_time(segment.get("start", 0))
            end = self._seconds_to_srt_time(segment.get("end", 0))
            text = segment.get("text", "").strip()
            
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
        
        return srt_content
    
    def _to_vtt(self, transcript: Dict) -> str:
        """Convert transcript to VTT format"""
        vtt_content = "WEBVTT\n\n"
        segments = transcript.get("segments", [])
        
        for segment in segments:
            start = self._seconds_to_vtt_time(segment.get("start", 0))
            end = self._seconds_to_vtt_time(segment.get("end", 0))
            text = segment.get("text", "").strip()
            
            vtt_content += f"{start} --> {end}\n{text}\n\n"
        
        return vtt_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def get_model_info(self) -> Dict:
        """Get information about current loaded model"""
        if self.model is None:
            return {"status": "No model loaded"}
        
        return {
            "model_size": self.current_model_size,
            "device": self.device,
            "status": "loaded"
        }
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            del self.model
            self.model = None
            self.current_model_size = None
            
            # Clear GPU cache if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()