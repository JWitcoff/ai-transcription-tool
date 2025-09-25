"""
Clean UI Module - Minimal, single-line terminal output for transcription tool
Provides a simple 3-stage progress indicator without clutter
"""

import sys
import time
from typing import Optional, Dict, Any
from datetime import datetime
import threading

class CleanUI:
    """Simple, clean terminal UI with minimal output"""

    def __init__(self):
        self.current_stage = None
        self.start_time = None
        self.stage_start_time = None
        self.model_name = None
        self.input_source = None
        self.suppress_output = False
        self._last_line_length = 0

        # Stage definitions
        self.stages = {
            'transcribe': {'icon': '🔊', 'text': 'Transcribing audio'},
            'analyze': {'icon': '🧠', 'text': 'Analyzing transcript'},
            'complete': {'icon': '✅', 'text': 'Complete – results saved'}
        }

        # ETA tracking
        self.stage_estimates = {
            'transcribe': 120,  # Default 2 minutes
            'analyze': 45,      # Default 45 seconds
        }

    def start_session(self, input_source: str, model_name: str = None):
        """Initialize a new transcription session"""
        self.start_time = time.time()
        self.input_source = input_source
        self.model_name = model_name

        # Clear screen and show header
        self._clear_screen()
        print("🎬 QUICK TRANSCRIPTION")
        print(f"Input: {self._truncate_path(input_source)}")

        if model_name:
            self.show_model_status(model_name)

        print()  # Empty line before progress

    def show_model_status(self, model_name: str, success: bool = True):
        """Display which transcription model is being used"""
        self.model_name = model_name

        # Determine icon based on model type
        if 'scribe' in model_name.lower() or 'elevenlabs' in model_name.lower():
            icon = "✅" if success else "⚠️"
            display_name = "ElevenLabs Scribe"
        elif 'whisper' in model_name.lower():
            icon = "⚠️"  # Whisper is fallback
            display_name = "Whisper fallback"
        else:
            icon = "ℹ️"
            display_name = model_name

        print(f"Using transcription model: {display_name} {icon}")

    def update_stage(self, stage: str, eta_seconds: Optional[float] = None):
        """Update the current progress stage"""
        if stage not in self.stages:
            return

        self.current_stage = stage
        self.stage_start_time = time.time()

        # Update ETA if provided
        if eta_seconds:
            self.stage_estimates[stage] = eta_seconds

        # Show the status line
        self._show_progress(eta_seconds)

    def _show_progress(self, eta_seconds: Optional[float] = None):
        """Display the current progress line"""
        if self.current_stage == 'complete':
            # Final stage doesn't need ETA
            line = f"[{self.stages[self.current_stage]['icon']}] {self.stages[self.current_stage]['text']}"
        else:
            # Calculate or use provided ETA
            if eta_seconds is None:
                eta_seconds = self.stage_estimates.get(self.current_stage, 60)

            eta_str = self._format_time(eta_seconds)
            stage_info = self.stages[self.current_stage]
            line = f"[{stage_info['icon']}] {stage_info['text']}... (ETA: {eta_str})"

        # Clear previous line and print new one
        self._clear_line()
        print(f"\r{line}", end='', flush=True)
        self._last_line_length = len(line)

    def complete(self, stats: Optional[Dict[str, Any]] = None):
        """Mark the session as complete and show summary"""
        self.update_stage('complete')
        print()  # New line after status

        if stats:
            self.show_summary(stats)

    def show_summary(self, stats: Dict[str, Any]):
        """Display the final summary statistics"""
        print("\n📝 Summary:")

        # Build summary line
        summary_parts = []

        if 'duration' in stats:
            summary_parts.append(f"Duration: {stats['duration']}")

        if 'speakers' in stats:
            speaker_count = stats['speakers']
            if isinstance(speaker_count, int):
                summary_parts.append(f"Speakers: {speaker_count}")
            else:
                summary_parts.append(f"Speakers: {speaker_count}")

        if 'confidence' in stats:
            confidence = stats['confidence']
            if isinstance(confidence, (int, float)):
                summary_parts.append(f"Confidence: {confidence:.1%}")
            else:
                summary_parts.append(f"Confidence: {confidence}")

        if summary_parts:
            print(" | ".join(summary_parts))

        # Show file save location
        if 'output_dir' in stats:
            file_count = stats.get('file_count', 5)
            output_dir = self._truncate_path(stats['output_dir'])
            print(f"Saved {file_count} output files to: {output_dir}")

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def _truncate_path(self, path: str, max_length: int = 60) -> str:
        """Truncate long paths for display"""
        if len(path) <= max_length:
            return path

        # Try to keep the important parts (filename and immediate parent)
        parts = path.split('/')
        if len(parts) > 3:
            return f".../{'/'.join(parts[-2:])}"
        return f"...{path[-max_length:]}"

    def _clear_line(self):
        """Clear the current line in the terminal"""
        if self._last_line_length > 0:
            print('\r' + ' ' * self._last_line_length, end='\r', flush=True)

    def _clear_screen(self):
        """Clear the terminal screen"""
        # We'll just add some spacing instead of full clear
        # to preserve scrollback history
        print("\n" * 2)

    def suppress_next_output(self):
        """Temporarily suppress verbose output from other modules"""
        self.suppress_output = True

    def restore_output(self):
        """Restore normal output"""
        self.suppress_output = False

# Global instance for easy access
_ui = None

def get_ui() -> CleanUI:
    """Get or create the global UI instance"""
    global _ui
    if _ui is None:
        _ui = CleanUI()
    return _ui

def start_transcription(input_source: str, model_name: str = None):
    """Start a new transcription session with clean UI"""
    ui = get_ui()
    ui.start_session(input_source, model_name)
    return ui

def update_status(stage: str, eta_seconds: Optional[float] = None):
    """Update the current status stage"""
    ui = get_ui()
    ui.update_stage(stage, eta_seconds)

def show_model(model_name: str, success: bool = True):
    """Show which model is being used"""
    ui = get_ui()
    ui.show_model_status(model_name, success)

def complete_with_stats(duration: str = None, speakers: int = None,
                       confidence: float = None, output_dir: str = None,
                       file_count: int = 5):
    """Complete the session and show statistics"""
    ui = get_ui()

    stats = {}
    if duration:
        stats['duration'] = duration
    if speakers is not None:
        stats['speakers'] = speakers
    if confidence is not None:
        stats['confidence'] = confidence
    if output_dir:
        stats['output_dir'] = output_dir
        stats['file_count'] = file_count

    ui.complete(stats)

class OutputSuppressor:
    """Context manager to suppress verbose print statements"""

    def __init__(self):
        self._original_stdout = None
        self._original_stderr = None

    def __enter__(self):
        """Redirect stdout/stderr to devnull"""
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        # Create a dummy file object that discards everything
        class DummyFile:
            def write(self, x): pass
            def flush(self): pass

        sys.stdout = DummyFile()
        sys.stderr = DummyFile()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original stdout/stderr"""
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

def suppress_output(func):
    """Decorator to suppress output from a function"""
    def wrapper(*args, **kwargs):
        with OutputSuppressor():
            return func(*args, **kwargs)
    return wrapper

# Convenience function for calculating duration
def format_duration(seconds: float) -> str:
    """Format duration in seconds to readable string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if secs > 0:
            return f"{hours}h {minutes}m {secs}s"
        return f"{hours}h {minutes}m"