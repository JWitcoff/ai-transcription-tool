"""
Base interfaces for transcription providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio."""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class TranscriptionResult:
    """Complete result from transcription process."""
    text: str
    segments: List[TranscriptionSegment]
    metadata: Dict[str, Any]
    provider: str
    duration: Optional[float] = None
    speakers: Optional[List[str]] = None
    confidence: Optional[float] = None

    @property
    def speaker_count(self) -> int:
        """Get number of unique speakers identified."""
        if self.speakers:
            return len(self.speakers)
        if self.segments:
            unique_speakers = set(seg.speaker for seg in self.segments if seg.speaker)
            return len(unique_speakers) if unique_speakers else 1
        return 1


class TranscriptionProvider(ABC):
    """Abstract base class for transcription providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._name = self.__class__.__name__.replace('Provider', '')

    @property
    def name(self) -> str:
        """Get provider name."""
        return self._name

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is properly configured and available."""
        pass

    @abstractmethod
    def transcribe(
        self,
        audio_file: Path,
        enable_diarization: bool = True,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio file.

        Args:
            audio_file: Path to audio file
            enable_diarization: Whether to enable speaker diarization
            language: Language code (if supported)
            **kwargs: Provider-specific options

        Returns:
            TranscriptionResult with segments and metadata

        Raises:
            TranscriptionError: On transcription failure
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        pass

    @abstractmethod
    def get_max_file_size(self) -> Optional[int]:
        """Get maximum file size in bytes, None if unlimited."""
        pass

    def validate_audio_file(self, audio_file: Path) -> bool:
        """
        Validate if audio file can be processed by this provider.

        Args:
            audio_file: Path to audio file

        Returns:
            True if file is valid for this provider
        """
        if not audio_file.exists():
            return False

        # Check file extension
        supported_formats = self.get_supported_formats()
        if supported_formats:
            file_ext = audio_file.suffix.lower().lstrip('.')
            if file_ext not in supported_formats:
                return False

        # Check file size
        max_size = self.get_max_file_size()
        if max_size and audio_file.stat().st_size > max_size:
            return False

        return True