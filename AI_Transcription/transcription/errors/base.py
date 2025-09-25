"""
Base error classes for the transcription system.
"""

class TranscriptionError(Exception):
    """Base exception for all transcription-related errors."""

    def __init__(self, message: str, provider: str = None, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.error_code = error_code

    def __str__(self):
        if self.provider:
            return f"[{self.provider}] {self.message}"
        return self.message


class ProviderError(TranscriptionError):
    """Errors related to transcription providers (ElevenLabs, Whisper, etc.)."""
    pass


class APIError(ProviderError):
    """Errors from external API calls."""

    def __init__(self, message: str, provider: str, status_code: int = None, response_data: dict = None):
        super().__init__(message, provider)
        self.status_code = status_code
        self.response_data = response_data


class ConfigurationError(TranscriptionError):
    """Errors related to configuration and setup."""
    pass


class AudioProcessingError(TranscriptionError):
    """Errors related to audio file processing."""
    pass


class ValidationError(TranscriptionError):
    """Errors related to input validation."""
    pass


class AnalysisError(TranscriptionError):
    """Errors related to transcript analysis."""
    pass