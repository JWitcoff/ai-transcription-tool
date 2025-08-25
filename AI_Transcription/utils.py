import os
import logging
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoTranscriptionError(Exception):
    """Base exception for video transcription errors"""
    pass

class AudioCaptureError(VideoTranscriptionError):
    """Error during audio capture"""
    pass

class TranscriptionError(VideoTranscriptionError):
    """Error during transcription"""
    pass

class AnalysisError(VideoTranscriptionError):
    """Error during text analysis"""
    pass

def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def validate_file_path(file_path: str) -> bool:
    """Validate if file path exists"""
    return os.path.exists(file_path)

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def get_file_hash(file_path: str) -> str:
    """Get MD5 hash of file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except OSError:
        return ""

def create_safe_filename(filename: str, max_length: int = 100) -> str:
    """Create a safe filename by removing invalid characters"""
    # Remove or replace invalid characters
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in ' -_.()':
            safe_chars.append(char)
        else:
            safe_chars.append('_')
    
    safe_filename = ''.join(safe_chars).strip()
    
    # Limit length
    if len(safe_filename) > max_length:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:max_length-len(ext)] + ext
    
    return safe_filename

def format_duration(seconds: float) -> str:
    """Format duration in seconds to readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def save_json(data: Dict[Any, Any], file_path: str) -> bool:
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False

def load_json(file_path: str) -> Optional[Dict[Any, Any]]:
    """Load data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return None

def create_session_id() -> str:
    """Create a unique session ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + hashlib.md5(
        str(datetime.now().timestamp()).encode()
    ).hexdigest()[:8]

def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24):
    """Clean up old temporary files"""
    try:
        temp_path = Path(temp_dir)
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in temp_path.glob("*.wav"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up old temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {file_path}: {e}")
                        
    except Exception as e:
        logger.error(f"Error during temp file cleanup: {e}")

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available"""
    dependencies = {}
    
    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        dependencies['ffmpeg'] = result.returncode == 0
    except:
        dependencies['ffmpeg'] = False
    
    # Check Python packages
    packages = ['whisper', 'yt_dlp', 'streamlit', 'transformers', 'torch']
    
    for package in packages:
        try:
            __import__(package)
            dependencies[package] = True
        except ImportError:
            dependencies[package] = False
    
    return dependencies

def log_system_info():
    """Log system information for debugging"""
    import platform
    import sys
    
    logger.info("System Information:")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Python: {sys.version}")
    logger.info(f"  Architecture: {platform.architecture()}")
    
    # Check GPU availability
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        logger.info(f"  CUDA available: {gpu_available}")
        if gpu_available:
            logger.info(f"  GPU device: {torch.cuda.get_device_name()}")
    except:
        logger.info("  CUDA: Not available")

class ProgressTracker:
    """Simple progress tracker for long-running operations"""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, step: int, message: str = ""):
        """Update progress"""
        self.current_step = step
        progress = (step / self.total_steps) * 100
        elapsed = datetime.now() - self.start_time
        
        logger.info(f"{self.description}: {progress:.1f}% ({step}/{self.total_steps}) - {message}")
        
        if step == self.total_steps:
            logger.info(f"{self.description} completed in {elapsed}")
    
    def get_progress(self) -> float:
        """Get current progress as percentage"""
        return (self.current_step / self.total_steps) * 100

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on error"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator