"""
Error handling for transcription system.
"""

from .base import (
    TranscriptionError,
    ProviderError,
    APIError,
    ConfigurationError,
    AudioProcessingError,
    ValidationError,
    AnalysisError
)

__all__ = [
    "TranscriptionError",
    "ProviderError",
    "APIError",
    "ConfigurationError",
    "AudioProcessingError",
    "ValidationError",
    "AnalysisError"
]