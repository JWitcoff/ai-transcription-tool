"""
Dynamic Progress Tracker with ETA calculations for transcription workflow
Provides real-time progress updates and estimated time remaining
"""

import time
import threading
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import sys

@dataclass
class ProgressStep:
    """Represents a single step in the transcription process"""
    name: str
    weight: float  # Relative weight of this step (0.0 to 1.0)
    estimated_seconds: float  # Estimated duration for this step
    completed: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class TranscriptionProgressTracker:
    """Dynamic progress tracker with ETA calculations"""

    def __init__(self, audio_duration_minutes: float = None):
        """
        Initialize progress tracker

        Args:
            audio_duration_minutes: Duration of audio in minutes for better ETA calculations
        """
        self.audio_duration = audio_duration_minutes
        self.start_time = time.time()
        self.current_step = 0
        self.total_progress = 0.0
        self.is_running = False
        self.animation_thread = None
        self.last_update = 0

        # Define the transcription workflow steps
        self.steps = self._initialize_steps(audio_duration_minutes)

    def _initialize_steps(self, audio_duration: Optional[float]) -> Dict[str, ProgressStep]:
        """Initialize progress steps with estimated timing"""

        # Base estimates (for ~3 minute audio)
        base_estimates = {
            "download": 5.0,     # Audio download
            "setup": 3.0,        # Model loading and setup
            "transcribe": 60.0,  # Main transcription (varies by provider)
            "diarize": 15.0,     # Speaker diarization (if enabled)
            "analyze": 10.0,     # AI analysis
            "save": 2.0          # File saving
        }

        # Adjust estimates based on audio duration
        if audio_duration:
            # Scale transcription time based on audio length
            base_estimates["transcribe"] = max(10.0, audio_duration * 0.5)  # ~30 seconds per minute
            base_estimates["diarize"] = max(5.0, audio_duration * 0.2)      # ~12 seconds per minute
            base_estimates["analyze"] = max(5.0, audio_duration * 0.1)      # ~6 seconds per minute

        # Calculate total estimated time
        total_time = sum(base_estimates.values())

        # Create steps with relative weights
        steps = {
            "download": ProgressStep(
                name="📥 Downloading audio",
                weight=0.10,
                estimated_seconds=base_estimates["download"]
            ),
            "setup": ProgressStep(
                name="🛠️ Loading transcription models",
                weight=0.05,
                estimated_seconds=base_estimates["setup"]
            ),
            "transcribe": ProgressStep(
                name="🎤 Transcribing audio",
                weight=0.60,
                estimated_seconds=base_estimates["transcribe"]
            ),
            "diarize": ProgressStep(
                name="👥 Identifying speakers",
                weight=0.15,
                estimated_seconds=base_estimates["diarize"]
            ),
            "analyze": ProgressStep(
                name="🧠 Generating analysis",
                weight=0.08,
                estimated_seconds=base_estimates["analyze"]
            ),
            "save": ProgressStep(
                name="💾 Saving results",
                weight=0.02,
                estimated_seconds=base_estimates["save"]
            )
        }

        return steps

    def start_step(self, step_name: str, custom_message: str = None):
        """Start a specific step"""
        if step_name not in self.steps:
            return

        step = self.steps[step_name]
        step.start_time = time.time()
        step.completed = False

        if custom_message:
            step.name = custom_message

        self.current_step = list(self.steps.keys()).index(step_name)
        self._start_progress_animation()

    def complete_step(self, step_name: str):
        """Complete a specific step"""
        if step_name not in self.steps:
            return

        step = self.steps[step_name]
        step.end_time = time.time()
        step.completed = True

        # Update progress
        completed_weight = sum(s.weight for s in self.steps.values() if s.completed)
        self.total_progress = min(completed_weight, 1.0)

        self._stop_progress_animation()
        self._show_completion_update(step_name)

    def update_step_progress(self, step_name: str, progress_percent: float, custom_message: str = None):
        """Update progress within a specific step"""
        if step_name not in self.steps:
            return

        step = self.steps[step_name]
        if custom_message:
            step.name = custom_message

        # Calculate total progress including current step
        completed_weight = sum(s.weight for s in self.steps.values() if s.completed)
        current_step_progress = step.weight * (progress_percent / 100.0)
        self.total_progress = min(completed_weight + current_step_progress, 1.0)

    def _start_progress_animation(self):
        """Start animated progress display"""
        self.is_running = True
        if self.animation_thread is None or not self.animation_thread.is_alive():
            self.animation_thread = threading.Thread(target=self._animate_progress)
            self.animation_thread.daemon = True
            self.animation_thread.start()

    def _stop_progress_animation(self):
        """Stop animated progress display"""
        self.is_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)

    def _animate_progress(self):
        """Animated progress bar display"""
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_idx = 0

        while self.is_running:
            current_step_name = list(self.steps.keys())[min(self.current_step, len(self.steps) - 1)]
            current_step = self.steps[current_step_name]

            # Calculate ETA
            eta = self._calculate_eta()
            eta_str = self._format_time(eta) if eta > 0 else "calculating..."

            # Build progress bar
            bar_width = 30
            filled_width = int(bar_width * self.total_progress)
            bar = "█" * filled_width + "░" * (bar_width - filled_width)

            # Format progress line
            progress_line = f"\r{spinner_chars[spinner_idx]} {current_step.name} │{bar}│ {self.total_progress*100:.1f}% │ ETA: {eta_str}"

            # Print with carriage return to update in place
            print(progress_line, end="", flush=True)

            spinner_idx = (spinner_idx + 1) % len(spinner_chars)
            time.sleep(0.1)

    def _show_completion_update(self, step_name: str):
        """Show step completion message"""
        step = self.steps[step_name]
        duration = step.end_time - step.start_time if step.start_time else 0

        # Clear the line and show completion
        print(f"\r✅ {step.name} │ Completed in {duration:.1f}s" + " " * 20)

    def _calculate_eta(self) -> float:
        """Calculate estimated time remaining"""
        if self.total_progress <= 0:
            return sum(step.estimated_seconds for step in self.steps.values())

        elapsed_time = time.time() - self.start_time

        # If we have actual progress, use it for better estimation
        if self.total_progress > 0.1:  # Only after 10% progress for better accuracy
            estimated_total_time = elapsed_time / self.total_progress
            return max(0, estimated_total_time - elapsed_time)

        # Use estimated remaining time for early stages
        completed_steps = [s for s in self.steps.values() if s.completed]
        remaining_steps = [s for s in self.steps.values() if not s.completed]

        return sum(step.estimated_seconds for step in remaining_steps)

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human readable time"""
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

    def finish(self):
        """Complete all progress tracking"""
        self.is_running = False
        self.total_progress = 1.0

        total_time = time.time() - self.start_time
        print(f"\n🎉 All steps completed in {self._format_time(total_time)}")

    def skip_step(self, step_name: str, reason: str = "skipped"):
        """Skip a step (e.g., if diarization is disabled)"""
        if step_name not in self.steps:
            return

        step = self.steps[step_name]
        step.completed = True
        step.end_time = time.time()

        print(f"⏭️  {step.name} │ {reason.title()}")

        # Update progress
        completed_weight = sum(s.weight for s in self.steps.values() if s.completed)
        self.total_progress = min(completed_weight, 1.0)

# Convenience functions for easy integration
_global_tracker: Optional[TranscriptionProgressTracker] = None

def start_transcription_progress(audio_duration_minutes: float = None) -> TranscriptionProgressTracker:
    """Start transcription progress tracking"""
    global _global_tracker
    _global_tracker = TranscriptionProgressTracker(audio_duration_minutes)
    return _global_tracker

def get_progress_tracker() -> Optional[TranscriptionProgressTracker]:
    """Get the current progress tracker"""
    return _global_tracker

def start_step(step_name: str, custom_message: str = None):
    """Start a progress step"""
    if _global_tracker:
        _global_tracker.start_step(step_name, custom_message)

def complete_step(step_name: str):
    """Complete a progress step"""
    if _global_tracker:
        _global_tracker.complete_step(step_name)

def update_progress(step_name: str, percent: float, message: str = None):
    """Update progress within a step"""
    if _global_tracker:
        _global_tracker.update_step_progress(step_name, percent, message)

def skip_step(step_name: str, reason: str = "skipped"):
    """Skip a progress step"""
    if _global_tracker:
        _global_tracker.skip_step(step_name, reason)

def finish_progress():
    """Finish progress tracking"""
    if _global_tracker:
        _global_tracker.finish()