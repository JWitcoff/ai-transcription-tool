"""
Caption generation utilities for VTT and SRT formats
"""

from typing import List
from dataclasses import dataclass

@dataclass
class Segment:
    """Segment with speaker and timing info"""
    speaker_id: str
    start: float
    end: float
    text: str
    channel_index: int = None

def format_srt_time(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (HH:MM:SS,mmm)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        SRT formatted timestamp (e.g., "00:01:23,450")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_vtt_time(seconds: float) -> str:
    """
    Format seconds to WebVTT timestamp format (HH:MM:SS.mmm)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        VTT formatted timestamp (e.g., "00:01:23.450")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def segments_to_srt(segments: List[Segment], include_speaker: bool = True) -> str:
    """
    Convert segments to SRT (SubRip) subtitle format.
    
    Example output:
    1
    00:00:00,000 --> 00:00:02,500
    [Speaker 1] Hello, welcome to the show
    
    2
    00:00:03,000 --> 00:00:05,000
    [Speaker 2] Thanks for having me
    
    Args:
        segments: List of Segment objects
        include_speaker: Whether to include speaker labels
        
    Returns:
        SRT formatted string
    """
    if not segments:
        return ""
    
    srt_lines = []
    
    for i, segment in enumerate(segments, 1):
        # Subtitle number
        srt_lines.append(str(i))
        
        # Timestamps
        start_time = format_srt_time(segment.start)
        end_time = format_srt_time(segment.end)
        srt_lines.append(f"{start_time} --> {end_time}")
        
        # Text with optional speaker label
        text = segment.text.strip()
        if include_speaker and segment.speaker_id != "speaker_1":
            # Only include speaker label if not default or if multiple speakers
            text = f"[{segment.speaker_id}] {text}"
        
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between subtitles
    
    return "\n".join(srt_lines)

def segments_to_vtt(segments: List[Segment], include_speaker: bool = True) -> str:
    """
    Convert segments to WebVTT subtitle format.
    
    Example output:
    WEBVTT
    
    00:00:00.000 --> 00:00:02.500
    <v Speaker 1>Hello, welcome to the show</v>
    
    00:00:03.000 --> 00:00:05.000
    <v Speaker 2>Thanks for having me</v>
    
    Args:
        segments: List of Segment objects
        include_speaker: Whether to include speaker labels
        
    Returns:
        VTT formatted string
    """
    if not segments:
        return "WEBVTT\n\n"
    
    vtt_lines = ["WEBVTT", ""]
    
    for segment in segments:
        # Timestamps
        start_time = format_vtt_time(segment.start)
        end_time = format_vtt_time(segment.end)
        vtt_lines.append(f"{start_time} --> {end_time}")
        
        # Text with optional speaker voice tag
        text = segment.text.strip()
        if include_speaker and segment.speaker_id != "speaker_1":
            # Use WebVTT voice tag for speaker identification
            text = f"<v {segment.speaker_id}>{text}</v>"
        
        vtt_lines.append(text)
        vtt_lines.append("")  # Empty line between captions
    
    return "\n".join(vtt_lines)

def save_captions(segments: List[Segment], base_filename: str, 
                  formats: List[str] = ["srt", "vtt"]) -> List[str]:
    """
    Save caption files in multiple formats.
    
    Args:
        segments: List of Segment objects
        base_filename: Base filename without extension
        formats: List of formats to save ("srt", "vtt")
        
    Returns:
        List of saved filenames
    """
    saved_files = []
    
    for fmt in formats:
        if fmt.lower() == "srt":
            content = segments_to_srt(segments)
            filename = f"{base_filename}.srt"
        elif fmt.lower() == "vtt":
            content = segments_to_vtt(segments)
            filename = f"{base_filename}.vtt"
        else:
            continue
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        saved_files.append(filename)
    
    return saved_files

def test_caption_generation():
    """Test caption generation with sample data"""
    
    # Sample segments
    segments = [
        Segment("Speaker 1", 0.0, 2.5, "Hello, welcome to the show"),
        Segment("Speaker 2", 3.0, 5.0, "Thanks for having me"),
        Segment("Speaker 1", 5.5, 8.0, "Let's talk about AI transcription"),
    ]
    
    print("=== SRT Format ===")
    srt = segments_to_srt(segments)
    print(srt)
    
    print("\n=== VTT Format ===")
    vtt = segments_to_vtt(segments)
    print(vtt)
    
    return True

if __name__ == "__main__":
    test_caption_generation()