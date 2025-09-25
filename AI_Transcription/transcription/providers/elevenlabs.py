"""
ElevenLabs Scribe provider implementation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import TranscriptionProvider, TranscriptionResult, TranscriptionSegment
from ..errors import APIError, ConfigurationError, ValidationError


class ElevenLabsProvider(TranscriptionProvider):
    """ElevenLabs Scribe transcription provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key') or os.getenv('ELEVENLABS_SCRIBE_KEY')
        self._scribe_client = None

    @property
    def scribe_client(self):
        """Lazy-load the ElevenLabs Scribe client."""
        if self._scribe_client is None:
            try:
                from elevenlabs_scribe import ScribeClient
                self._scribe_client = ScribeClient()
            except ImportError:
                raise ConfigurationError(
                    "ElevenLabs Scribe client not available. Install with: pip install elevenlabs",
                    provider="ElevenLabs"
                )
        return self._scribe_client

    def is_available(self) -> bool:
        """Check if ElevenLabs Scribe is available and configured."""
        try:
            return bool(self.api_key and hasattr(self.scribe_client, 'api_key'))
        except ConfigurationError:
            return False

    def transcribe(
        self,
        audio_file: Path,
        enable_diarization: bool = True,
        language: Optional[str] = None,
        num_speakers: Optional[int] = None,
        diarization_threshold: Optional[float] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio using ElevenLabs Scribe.

        Args:
            audio_file: Path to audio file
            enable_diarization: Enable speaker diarization
            language: Language code (optional)
            num_speakers: Number of speakers (optional)
            diarization_threshold: Confidence threshold for diarization
            **kwargs: Additional options

        Returns:
            TranscriptionResult with segments and speaker information
        """
        if not self.validate_audio_file(audio_file):
            raise ValidationError(f"Invalid audio file: {audio_file}", provider="ElevenLabs")

        try:
            # CRITICAL: ElevenLabs API rule - only set threshold when diarize=True AND num_speakers=None
            scribe_kwargs = {
                'diarize': enable_diarization,
                'language': language,
            }

            if enable_diarization:
                if num_speakers is not None:
                    scribe_kwargs['num_speakers'] = num_speakers
                elif diarization_threshold is not None:
                    # Only set threshold when num_speakers is None
                    scribe_kwargs['diarization_threshold'] = diarization_threshold

            # Add any additional provider-specific options
            scribe_kwargs.update(kwargs)

            # Transcribe using file upload method
            result = self.scribe_client.transcribe_from_file(
                str(audio_file),
                **scribe_kwargs
            )

            if not result or not result.get('text'):
                raise APIError("Empty transcription result", provider="ElevenLabs")

            # Convert to standard format
            segments = []
            for segment_data in result.get('segments', []):
                segments.append(TranscriptionSegment(
                    start=segment_data.get('start', 0),
                    end=segment_data.get('end', 0),
                    text=segment_data.get('text', ''),
                    speaker=segment_data.get('speaker'),
                    confidence=segment_data.get('confidence')
                ))

            # Extract speakers list
            speakers = list(set(seg.speaker for seg in segments if seg.speaker))

            return TranscriptionResult(
                text=result['text'],
                segments=segments,
                metadata={
                    'provider': 'ElevenLabs',
                    'diarization': enable_diarization,
                    'language': language,
                    'processing_time': result.get('processing_time'),
                    'audio_events': result.get('audio_events', [])
                },
                provider='ElevenLabs',
                duration=result.get('duration'),
                speakers=speakers,
                confidence=result.get('confidence')
            )

        except Exception as e:
            if isinstance(e, (APIError, ValidationError)):
                raise
            raise APIError(f"ElevenLabs transcription failed: {str(e)}", provider="ElevenLabs")

    def get_supported_formats(self) -> List[str]:
        """Get supported audio formats."""
        return ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac', 'wma', 'opus', 'mp4', 'avi', 'mov']

    def get_max_file_size(self) -> Optional[int]:
        """Get maximum file size (3GB for file uploads)."""
        return 3 * 1024 * 1024 * 1024  # 3GB