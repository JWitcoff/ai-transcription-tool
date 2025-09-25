"""
Configuration management for transcription system.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class ElevenLabsConfig:
    """Configuration for ElevenLabs Scribe provider."""
    api_key: Optional[str] = None
    default_diarization: bool = True
    default_language: Optional[str] = None
    max_file_size: int = 3 * 1024 * 1024 * 1024  # 3GB

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv('ELEVENLABS_SCRIBE_KEY')


@dataclass
class WhisperConfig:
    """Configuration for Whisper provider."""
    model_size: str = 'base'
    device: Optional[str] = None
    enable_diarization: bool = False
    language: Optional[str] = None

    def __post_init__(self):
        # Auto-detect device if not specified
        if self.device is None:
            try:
                import torch
                self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            except ImportError:
                self.device = 'cpu'


@dataclass
class UIConfig:
    """Configuration for user interface."""
    use_clean_ui: bool = True
    show_progress: bool = True
    suppress_verbose: bool = True
    emoji_support: bool = True


@dataclass
class TranscriptionConfig:
    """Main configuration for transcription system."""
    elevenlabs: ElevenLabsConfig = field(default_factory=ElevenLabsConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    # Provider selection
    prefer_elevenlabs: bool = True
    use_fallback: bool = True

    # Output settings
    output_dir: str = "transcripts"
    save_formats: list = field(default_factory=lambda: ['txt', 'json', 'srt', 'vtt'])

    # Analysis settings
    enable_analysis: bool = True
    openai_api_key: Optional[str] = None

    def __post_init__(self):
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')

    @classmethod
    def from_env(cls) -> 'TranscriptionConfig':
        """Create configuration from environment variables."""
        # Load .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)

        return cls(
            elevenlabs=ElevenLabsConfig(),
            whisper=WhisperConfig(
                model_size=os.getenv('WHISPER_MODEL_SIZE', 'base'),
                enable_diarization=os.getenv('WHISPER_DIARIZATION', 'false').lower() == 'true'
            ),
            ui=UIConfig(
                use_clean_ui=os.getenv('USE_CLEAN_UI', 'true').lower() == 'true',
                suppress_verbose=os.getenv('SUPPRESS_VERBOSE', 'true').lower() == 'true'
            ),
            prefer_elevenlabs=os.getenv('USE_SCRIBE', 'true').lower() == 'true',
            output_dir=os.getenv('OUTPUT_DIR', 'transcripts'),
            enable_analysis=os.getenv('ENABLE_ANALYSIS', 'true').lower() == 'true'
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'TranscriptionConfig':
        """Create configuration from dictionary."""
        elevenlabs_config = ElevenLabsConfig(**config_dict.get('elevenlabs', {}))
        whisper_config = WhisperConfig(**config_dict.get('whisper', {}))
        ui_config = UIConfig(**config_dict.get('ui', {}))

        # Extract top-level settings
        top_level = {k: v for k, v in config_dict.items() if k not in ['elevenlabs', 'whisper', 'ui']}

        return cls(
            elevenlabs=elevenlabs_config,
            whisper=whisper_config,
            ui=ui_config,
            **top_level
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'elevenlabs': {
                'api_key': self.elevenlabs.api_key,
                'default_diarization': self.elevenlabs.default_diarization,
                'default_language': self.elevenlabs.default_language,
                'max_file_size': self.elevenlabs.max_file_size
            },
            'whisper': {
                'model_size': self.whisper.model_size,
                'device': self.whisper.device,
                'enable_diarization': self.whisper.enable_diarization,
                'language': self.whisper.language
            },
            'ui': {
                'use_clean_ui': self.ui.use_clean_ui,
                'show_progress': self.ui.show_progress,
                'suppress_verbose': self.ui.suppress_verbose,
                'emoji_support': self.ui.emoji_support
            },
            'prefer_elevenlabs': self.prefer_elevenlabs,
            'use_fallback': self.use_fallback,
            'output_dir': self.output_dir,
            'save_formats': self.save_formats,
            'enable_analysis': self.enable_analysis,
            'openai_api_key': self.openai_api_key
        }

    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is properly configured."""
        if provider_name.lower() == 'elevenlabs':
            return bool(self.elevenlabs.api_key)
        elif provider_name.lower() == 'whisper':
            try:
                import whisper
                return True
            except ImportError:
                return False
        return False