"""
OpenAI Whisper provider implementation.
"""

import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Any

# Suppress torchaudio deprecation warnings that clutter clean UI
warnings.filterwarnings("ignore", message=".*torchaudio._extension.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torch.load.*", category=UserWarning)

from .base import TranscriptionProvider, TranscriptionResult, TranscriptionSegment
from ..errors import APIError, ConfigurationError, ValidationError


class WhisperProvider(TranscriptionProvider):
    """OpenAI Whisper transcription provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_size = self.config.get('model_size', 'base')
        self.device = self.config.get('device')
        self.enable_diarization = self.config.get('enable_diarization', False)
        self._whisper_model = None
        self._diarization_pipeline = None

    @property
    def whisper_model(self):
        """Lazy-load the Whisper model."""
        if self._whisper_model is None:
            try:
                import whisper
                self._whisper_model = whisper.load_model(self.model_size, device=self.device)
            except ImportError:
                raise ConfigurationError(
                    "Whisper not available. Install with: pip install openai-whisper",
                    provider="Whisper"
                )
        return self._whisper_model

    @property
    def diarization_pipeline(self):
        """Lazy-load the pyannote diarization pipeline."""
        if self._diarization_pipeline is None and self.enable_diarization:
            try:
                from pyannote.audio import Pipeline
                self._diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            except ImportError:
                raise ConfigurationError(
                    "pyannote.audio not available. Install with: pip install pyannote.audio>=3.1.0",
                    provider="Whisper"
                )
        return self._diarization_pipeline

    def is_available(self) -> bool:
        """Check if Whisper is available."""
        try:
            import whisper
            return True
        except ImportError:
            return False

    def transcribe(
        self,
        audio_file: Path,
        enable_diarization: bool = False,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio using Whisper.

        Args:
            audio_file: Path to audio file
            enable_diarization: Enable speaker diarization (requires pyannote.audio)
            language: Language code
            **kwargs: Additional Whisper options

        Returns:
            TranscriptionResult with segments
        """
        if not self.validate_audio_file(audio_file):
            raise ValidationError(f"Invalid audio file: {audio_file}", provider="Whisper")

        try:
            # Transcribe with Whisper
            whisper_options = {
                'language': language,
                'task': 'transcribe',
                **kwargs
            }

            result = self.whisper_model.transcribe(str(audio_file), **whisper_options)

            if not result or not result.get('text'):
                raise APIError("Empty transcription result", provider="Whisper")

            # Convert segments
            segments = []
            for segment_data in result.get('segments', []):
                segments.append(TranscriptionSegment(
                    start=segment_data.get('start', 0),
                    end=segment_data.get('end', 0),
                    text=segment_data.get('text', ''),
                    confidence=segment_data.get('avg_logprob')  # Whisper uses log probability
                ))

            # Apply diarization if requested and available
            if enable_diarization and self.enable_diarization:
                segments = self._apply_diarization(audio_file, segments)

            # Extract speakers
            speakers = list(set(seg.speaker for seg in segments if seg.speaker))

            return TranscriptionResult(
                text=result['text'],
                segments=segments,
                metadata={
                    'provider': 'Whisper',
                    'model_size': self.model_size,
                    'language': result.get('language'),
                    'diarization': enable_diarization and self.enable_diarization,
                },
                provider='Whisper',
                speakers=speakers if speakers else None,
                confidence=self._calculate_average_confidence(segments)
            )

        except Exception as e:
            if isinstance(e, (APIError, ValidationError, ConfigurationError)):
                raise
            raise APIError(f"Whisper transcription failed: {str(e)}", provider="Whisper")

    def _apply_diarization(self, audio_file: Path, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        """Apply speaker diarization to segments using pyannote.audio."""
        try:
            diarization = self.diarization_pipeline(str(audio_file))

            # Map speakers to segments based on time overlap
            for segment in segments:
                segment_start = segment.start
                segment_end = segment.end

                # Find overlapping speakers
                overlapping_speakers = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if turn.start < segment_end and turn.end > segment_start:
                        overlapping_speakers.append(speaker)

                # Assign most common speaker or first one
                if overlapping_speakers:
                    segment.speaker = max(set(overlapping_speakers), key=overlapping_speakers.count)

            return segments

        except Exception as e:
            # Diarization failed, return segments without speaker labels
            return segments

    def _calculate_average_confidence(self, segments: List[TranscriptionSegment]) -> Optional[float]:
        """Calculate average confidence from segments."""
        confidences = [seg.confidence for seg in segments if seg.confidence is not None]
        if confidences:
            return sum(confidences) / len(confidences)
        return None

    def get_supported_formats(self) -> List[str]:
        """Get supported audio formats."""
        return ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac', 'wma', 'opus', 'mp4', 'avi', 'mov', 'mkv', 'webm']

    def get_max_file_size(self) -> Optional[int]:
        """Get maximum file size (None = unlimited for local processing)."""
        return None