"""
Transcription Package - Core Architecture

This package provides a clean, modular architecture for AI transcription services.

Key Components:
- providers: ElevenLabs Scribe and Whisper transcription providers
- analysis: AI-powered content analysis
- ui: User interface components (CLI, progress tracking)
- config: Configuration management
- errors: Standardized error handling

Usage:
    from transcription import TranscriptionService
    from transcription.providers import ElevenLabsProvider, WhisperProvider
    from transcription.ui import CleanUI

    service = TranscriptionService(
        provider=ElevenLabsProvider(),
        ui=CleanUI()
    )
    result = service.transcribe("audio.wav")
"""

from .core.service import TranscriptionService
from .providers.base import TranscriptionProvider
from .providers.elevenlabs import ElevenLabsProvider
from .providers.whisper import WhisperProvider
from .ui.clean import CleanUI
from .errors.base import TranscriptionError

__version__ = "2.0.0"
__all__ = [
    "TranscriptionService",
    "TranscriptionProvider",
    "ElevenLabsProvider",
    "WhisperProvider",
    "CleanUI",
    "TranscriptionError"
]