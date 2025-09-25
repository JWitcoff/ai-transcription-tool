"""
Core transcription service with provider fallback logic.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from ..providers.base import TranscriptionProvider, TranscriptionResult
from ..providers.elevenlabs import ElevenLabsProvider
from ..providers.whisper import WhisperProvider
from ..errors import TranscriptionError, ValidationError, ConfigurationError


class TranscriptionService:
    """
    Main transcription service with automatic provider fallback.

    Provides a clean interface for transcription with intelligent provider selection.
    """

    def __init__(
        self,
        primary_provider: Optional[TranscriptionProvider] = None,
        fallback_provider: Optional[TranscriptionProvider] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize transcription service.

        Args:
            primary_provider: Primary transcription provider (defaults to ElevenLabs)
            fallback_provider: Fallback provider (defaults to Whisper)
            config: Service configuration
        """
        self.config = config or {}

        # Set up providers with intelligent defaults
        self.primary_provider = primary_provider or self._create_default_primary()
        self.fallback_provider = fallback_provider or self._create_default_fallback()

    def _create_default_primary(self) -> TranscriptionProvider:
        """Create default primary provider (ElevenLabs)."""
        try:
            provider = ElevenLabsProvider(self.config.get('elevenlabs', {}))
            if provider.is_available():
                return provider
        except ConfigurationError:
            pass

        # If ElevenLabs not available, use Whisper as primary
        return self._create_default_fallback()

    def _create_default_fallback(self) -> TranscriptionProvider:
        """Create default fallback provider (Whisper)."""
        return WhisperProvider(self.config.get('whisper', {}))

    def transcribe(
        self,
        audio_file: Union[str, Path],
        enable_diarization: bool = True,
        language: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio file with automatic provider fallback.

        Args:
            audio_file: Path to audio file
            enable_diarization: Enable speaker diarization
            language: Language code
            use_fallback: Whether to use fallback provider on failure
            **kwargs: Provider-specific options

        Returns:
            TranscriptionResult

        Raises:
            TranscriptionError: On transcription failure
        """
        audio_path = Path(audio_file)

        if not audio_path.exists():
            raise ValidationError(f"Audio file not found: {audio_path}")

        # Try primary provider first
        try:
            if self.primary_provider.validate_audio_file(audio_path):
                return self.primary_provider.transcribe(
                    audio_path,
                    enable_diarization=enable_diarization,
                    language=language,
                    **kwargs
                )
        except TranscriptionError as e:
            if not use_fallback:
                raise
            # Log primary provider failure (would use logging in production)
            pass

        # Try fallback provider
        if use_fallback and self.fallback_provider:
            try:
                if self.fallback_provider.validate_audio_file(audio_path):
                    return self.fallback_provider.transcribe(
                        audio_path,
                        enable_diarization=enable_diarization,
                        language=language,
                        **kwargs
                    )
            except TranscriptionError:
                pass

        # Both providers failed
        raise TranscriptionError(
            f"All transcription providers failed for file: {audio_path}",
            error_code="PROVIDER_EXHAUSTED"
        )

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        providers = []

        if self.primary_provider and self.primary_provider.is_available():
            providers.append(self.primary_provider.name)

        if (self.fallback_provider and
            self.fallback_provider.is_available() and
            self.fallback_provider.name not in providers):
            providers.append(self.fallback_provider.name)

        return providers

    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about configured providers."""
        info = {}

        if self.primary_provider:
            info['primary'] = {
                'name': self.primary_provider.name,
                'available': self.primary_provider.is_available(),
                'supported_formats': self.primary_provider.get_supported_formats(),
                'max_file_size': self.primary_provider.get_max_file_size()
            }

        if self.fallback_provider:
            info['fallback'] = {
                'name': self.fallback_provider.name,
                'available': self.fallback_provider.is_available(),
                'supported_formats': self.fallback_provider.get_supported_formats(),
                'max_file_size': self.fallback_provider.get_max_file_size()
            }

        return info