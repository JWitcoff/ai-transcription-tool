import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the video transcription tool"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Audio Settings
    DEFAULT_AUDIO_QUALITY = os.getenv('DEFAULT_AUDIO_QUALITY', 'best')
    DEFAULT_SAMPLE_RATE = int(os.getenv('DEFAULT_SAMPLE_RATE', '16000'))
    MAX_AUDIO_DURATION = int(os.getenv('MAX_AUDIO_DURATION', '3600'))  # 1 hour
    
    # Model Settings
    DEFAULT_WHISPER_MODEL = os.getenv('DEFAULT_WHISPER_MODEL', 'base')
    ENABLE_GPU = os.getenv('ENABLE_GPU', 'true').lower() == 'true'
    
    # Analysis Settings
    MAX_SUMMARY_LENGTH = int(os.getenv('MAX_SUMMARY_LENGTH', '150'))
    MIN_SUMMARY_LENGTH = int(os.getenv('MIN_SUMMARY_LENGTH', '30'))
    NUM_THEMES = int(os.getenv('NUM_THEMES', '5'))
    
    # File Settings
    TEMP_DIR = os.getenv('TEMP_DIR', '/tmp')
    CLEANUP_TEMP_FILES = os.getenv('CLEANUP_TEMP_FILES', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'video_transcription.log')
    
    # Supported file formats
    SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    # Limits
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_TEXT_LENGTH = 100000  # characters
    
    @classmethod
    def get_temp_dir(cls) -> Path:
        """Get temporary directory as Path object"""
        return Path(cls.TEMP_DIR)
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )
    
    @classmethod
    def validate_config(cls) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check API keys
        if not cls.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY not set (optional for Whisper)")
        
        # Check directories
        temp_dir = Path(cls.TEMP_DIR)
        if not temp_dir.exists():
            try:
                temp_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create temp directory: {e}")
        
        # Validate numeric settings
        if cls.MAX_AUDIO_DURATION <= 0:
            issues.append("MAX_AUDIO_DURATION must be positive")
        
        if cls.DEFAULT_SAMPLE_RATE not in [8000, 16000, 22050, 44100, 48000]:
            issues.append("DEFAULT_SAMPLE_RATE should be a standard rate")
        
        return issues