"""
Timestamp alignment with order-preserving fuzzy matching
Maps extracted chapters back to SRT/VTT timestamps with drift prevention
"""

import difflib
import re
from typing import List, Tuple, Optional, Dict, Any
import json
from pathlib import Path


def normalize_for_matching(text: str) -> str:
    """
    Normalize text for fuzzy matching alignment
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text suitable for sequence matching
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def parse_srt_file(srt_path: str) -> List[Tuple[float, float, str]]:
    """
    Parse SRT subtitle file to extract timestamps and text
    
    Args:
        srt_path: Path to SRT file
        
    Returns:
        List of (start_time, end_time, text) tuples in seconds
    """
    if not Path(srt_path).exists():
        return []
    
    segments = []
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newlines to get individual subtitle blocks
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # Parse timestamp line (format: 00:01:23,456 --> 00:01:26,789)
        timestamp_line = lines[1]
        timestamp_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_line)
        
        if not timestamp_match:
            continue
        
        # Convert to seconds
        start_h, start_m, start_s, start_ms, end_h, end_m, end_s, end_ms = map(int, timestamp_match.groups())
        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
        
        # Join text lines (may be multiple lines per subtitle)
        text = ' '.join(lines[2:])
        
        segments.append((start_time, end_time, text))
    
    return segments


def parse_vtt_file(vtt_path: str) -> List[Tuple[float, float, str]]:
    """
    Parse VTT subtitle file to extract timestamps and text
    
    Args:
        vtt_path: Path to VTT file
        
    Returns:
        List of (start_time, end_time, text) tuples in seconds
    """
    if not Path(vtt_path).exists():
        return []
    
    segments = []
    
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header
    start_processing = False
    current_block = []
    
    for line in lines:
        line = line.strip()
        
        if line == "WEBVTT":
            start_processing = True
            continue
        
        if not start_processing:
            continue
        
        if not line:  # Empty line indicates end of block
            if current_block:
                process_vtt_block(current_block, segments)
                current_block = []
        else:
            current_block.append(line)
    
    # Process final block
    if current_block:
        process_vtt_block(current_block, segments)
    
    return segments


def process_vtt_block(block: List[str], segments: List[Tuple[float, float, str]]):
    """Process a single VTT subtitle block"""
    if len(block) < 2:
        return
    
    # Find timestamp line (may not be first line due to speaker tags)
    timestamp_line = None
    text_lines = []
    
    for line in block:
        if '-->' in line:
            timestamp_line = line
        else:
            # Skip speaker tags like <v Speaker1>
            if not (line.startswith('<v ') and line.endswith('>')):
                text_lines.append(line)
    
    if not timestamp_line or not text_lines:
        return
    
    # Parse timestamp (format: 00:01:23.456 --> 00:01:26.789)
    timestamp_match = re.match(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})', timestamp_line)
    
    if not timestamp_match:
        return
    
    # Convert to seconds
    start_h, start_m, start_s, start_ms, end_h, end_m, end_s, end_ms = map(int, timestamp_match.groups())
    start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
    end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
    
    # Join text lines
    text = ' '.join(text_lines)
    
    segments.append((start_time, end_time, text))


def build_transcript_corpus(segments: List[Tuple[float, float, str]]) -> Tuple[str, List[int]]:
    """
    Build searchable corpus from subtitle segments with position tracking
    
    Args:
        segments: List of (start_time, end_time, text) tuples
        
    Returns:
        Tuple of (normalized_corpus, char_to_segment_map)
    """
    corpus_parts = []
    char_to_segment = []
    
    for i, (start_time, end_time, text) in enumerate(segments):
        normalized_text = normalize_for_matching(text)
        if normalized_text:
            # Track which segment each character belongs to
            for _ in range(len(normalized_text) + 1):  # +1 for space separator
                char_to_segment.append(i)
            
            corpus_parts.append(normalized_text)
    
    corpus = ' '.join(corpus_parts)
    return corpus, char_to_segment


def align_chapters_to_timestamps(
    chapters: List[Dict[str, Any]], 
    segments: List[Tuple[float, float, str]],
    confidence_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Align chapter summaries to subtitle timestamps using order-preserving fuzzy matching
    
    Args:
        chapters: List of chapter dictionaries with 'title' and 'summary'
        segments: List of (start_time, end_time, text) tuples from SRT/VTT
        confidence_threshold: Minimum confidence for alignment
        
    Returns:
        List of chapters with added 'start_ts' fields where alignment succeeded
    """
    if not segments or not chapters:
        return chapters
    
    # Build searchable corpus
    corpus, char_to_segment = build_transcript_corpus(segments)
    
    if not corpus:
        return chapters
    
    aligned_chapters = []
    last_position = 0  # Ensure monotonic progression
    
    print(f"🔍 Aligning {len(chapters)} chapters to {len(segments)} subtitle segments...")
    
    for i, chapter in enumerate(chapters):
        chapter_copy = chapter.copy()
        
        # Create search cue from chapter summary (first 180 chars work well)
        search_text = chapter.get('summary', '') or chapter.get('title', '')
        if not search_text:
            aligned_chapters.append(chapter_copy)
            continue
        
        search_cue = normalize_for_matching(search_text)[:180]
        
        if not search_cue:
            aligned_chapters.append(chapter_copy)
            continue
        
        # Find best match in corpus using sequence matcher
        matcher = difflib.SequenceMatcher(None, corpus[last_position:], search_cue)
        match = matcher.find_longest_match(0, len(corpus) - last_position, 0, len(search_cue))
        
        if match.size < min(len(search_cue) * confidence_threshold, 30):
            print(f"⚠️ Chapter {i+1}: Low confidence match for '{chapter.get('title', 'Unknown')[:40]}...'")
            aligned_chapters.append(chapter_copy)
            continue
        
        # Calculate absolute position in corpus
        absolute_char_pos = last_position + match.a
        
        # Map character position back to segment
        if absolute_char_pos < len(char_to_segment):
            segment_idx = char_to_segment[absolute_char_pos]
            
            # Ensure we don't go backwards (monotonic constraint)
            if segment_idx >= 0 and segment_idx < len(segments):
                start_time = segments[segment_idx][0]
                chapter_copy['start_ts'] = start_time
                
                # Update last position for next search (monotonic progression)
                last_position = max(absolute_char_pos, last_position)
                
                print(f"✅ Chapter {i+1}: '{chapter.get('title', '')[:40]}...' → {start_time:.1f}s")
            else:
                print(f"⚠️ Chapter {i+1}: Invalid segment index {segment_idx}")
        else:
            print(f"⚠️ Chapter {i+1}: Character position {absolute_char_pos} out of range")
        
        aligned_chapters.append(chapter_copy)
    
    # Summary stats
    aligned_count = sum(1 for c in aligned_chapters if 'start_ts' in c)
    print(f"📊 Timestamp alignment: {aligned_count}/{len(chapters)} chapters aligned ({aligned_count/len(chapters)*100:.1f}%)")
    
    return aligned_chapters


def align_to_srt(chapter_summaries: List[str], srt_segments: List[Tuple[float, str]]) -> List[float]:
    """
    Simplified alignment function for direct use (maintaining backward compatibility)
    
    Args:
        chapter_summaries: List of chapter summary text
        srt_segments: List of (start_time, text) tuples
        
    Returns:
        List of aligned start times
    """
    # Convert to expected format
    segments = [(start, start + 5.0, text) for start, text in srt_segments]  # Assume 5s duration
    chapters = [{"summary": summary, "title": f"Chapter {i+1}"} for i, summary in enumerate(chapter_summaries)]
    
    aligned = align_chapters_to_timestamps(chapters, segments)
    
    return [c.get('start_ts', 0.0) for c in aligned]


def find_subtitle_files(transcript_dir: str) -> Dict[str, str]:
    """
    Find available subtitle files in transcript directory
    
    Args:
        transcript_dir: Directory containing transcript files
        
    Returns:
        Dictionary with subtitle format as key and file path as value
    """
    subtitle_files = {}
    transcript_path = Path(transcript_dir)
    
    if not transcript_path.exists():
        return subtitle_files
    
    # Look for SRT files
    srt_files = list(transcript_path.glob("*.srt"))
    if srt_files:
        subtitle_files["srt"] = str(srt_files[0])
    
    # Look for VTT files
    vtt_files = list(transcript_path.glob("*.vtt"))
    if vtt_files:
        subtitle_files["vtt"] = str(vtt_files[0])
    
    return subtitle_files


def add_timestamps_to_extraction(extraction_data: Dict[str, Any], transcript_dir: str = "") -> Dict[str, Any]:
    """
    Add timestamp information to extraction data if subtitle files are available
    
    Args:
        extraction_data: Extraction output with chapters
        transcript_dir: Directory containing subtitle files
        
    Returns:
        Updated extraction data with timestamps where possible
    """
    if not transcript_dir:
        # Mark as partial segment
        extraction_data["partial_segment"] = True
        return extraction_data
    
    # Find available subtitle files
    subtitle_files = find_subtitle_files(transcript_dir)
    
    if not subtitle_files:
        extraction_data["partial_segment"] = True
        return extraction_data
    
    # Parse subtitle file (prefer VTT over SRT for speaker info)
    segments = []
    if "vtt" in subtitle_files:
        segments = parse_vtt_file(subtitle_files["vtt"])
        print(f"📄 Loaded {len(segments)} segments from VTT file")
    elif "srt" in subtitle_files:
        segments = parse_srt_file(subtitle_files["srt"])
        print(f"📄 Loaded {len(segments)} segments from SRT file")
    
    if not segments:
        extraction_data["partial_segment"] = True
        return extraction_data
    
    # Align chapters if present
    if "chapters" in extraction_data and extraction_data["chapters"]:
        aligned_chapters = align_chapters_to_timestamps(extraction_data["chapters"], segments)
        extraction_data["chapters"] = aligned_chapters
        
        # Check alignment success rate
        aligned_count = sum(1 for c in aligned_chapters if 'start_ts' in c)
        if aligned_count < len(aligned_chapters) * 0.5:  # Less than 50% aligned
            extraction_data["partial_segment"] = True
        else:
            extraction_data["partial_segment"] = False
    else:
        extraction_data["partial_segment"] = True
    
    return extraction_data


def validate_monotonic_timestamps(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure chapter timestamps are monotonically increasing
    
    Args:
        chapters: List of chapters with potential start_ts fields
        
    Returns:
        Chapters with corrected timestamps
    """
    corrected_chapters = []
    last_timestamp = 0.0
    
    for chapter in chapters:
        chapter_copy = chapter.copy()
        
        if 'start_ts' in chapter_copy:
            current_ts = chapter_copy['start_ts']
            
            # Ensure monotonic progression
            if current_ts < last_timestamp:
                print(f"⚠️ Correcting non-monotonic timestamp: {current_ts:.1f}s → {last_timestamp + 1.0:.1f}s")
                chapter_copy['start_ts'] = last_timestamp + 1.0
                last_timestamp = last_timestamp + 1.0
            else:
                last_timestamp = current_ts
        
        corrected_chapters.append(chapter_copy)
    
    return corrected_chapters


class TimestampAligner:
    """Main class for timestamp alignment with caching and optimization"""
    
    def __init__(self):
        self.cache = {}  # Cache parsed subtitle files
        self.stats = {
            "alignments_attempted": 0,
            "alignments_successful": 0,
            "cache_hits": 0
        }
    
    def align_extraction(self, extraction_data: Dict[str, Any], subtitle_path: str = "") -> Dict[str, Any]:
        """
        Main method to add timestamps to extraction
        
        Args:
            extraction_data: Raw extraction output
            subtitle_path: Path to subtitle file or directory
            
        Returns:
            Extraction with timestamps added
        """
        self.stats["alignments_attempted"] += 1
        
        # Handle directory vs file path
        if subtitle_path and Path(subtitle_path).is_dir():
            return add_timestamps_to_extraction(extraction_data, subtitle_path)
        elif subtitle_path and Path(subtitle_path).exists():
            # Single file - determine format and parse
            if subtitle_path.endswith('.srt'):
                segments = self._get_cached_segments(subtitle_path, 'srt')
            elif subtitle_path.endswith('.vtt'):
                segments = self._get_cached_segments(subtitle_path, 'vtt')
            else:
                extraction_data["partial_segment"] = True
                return extraction_data
            
            # Align chapters
            if segments and "chapters" in extraction_data:
                aligned_chapters = align_chapters_to_timestamps(extraction_data["chapters"], segments)
                extraction_data["chapters"] = validate_monotonic_timestamps(aligned_chapters)
                
                aligned_count = sum(1 for c in aligned_chapters if 'start_ts' in c)
                if aligned_count > 0:
                    self.stats["alignments_successful"] += 1
                    extraction_data["partial_segment"] = aligned_count < len(aligned_chapters) * 0.8
                else:
                    extraction_data["partial_segment"] = True
            else:
                extraction_data["partial_segment"] = True
        else:
            extraction_data["partial_segment"] = True
        
        return extraction_data
    
    def _get_cached_segments(self, file_path: str, file_type: str) -> List[Tuple[float, float, str]]:
        """Get segments with caching"""
        cache_key = f"{file_path}:{file_type}"
        
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]
        
        if file_type == 'srt':
            segments = parse_srt_file(file_path)
        elif file_type == 'vtt':
            segments = parse_vtt_file(file_path)
        else:
            segments = []
        
        self.cache[cache_key] = segments
        return segments
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alignment statistics"""
        stats = self.stats.copy()
        if stats["alignments_attempted"] > 0:
            stats["success_rate"] = stats["alignments_successful"] / stats["alignments_attempted"]
        else:
            stats["success_rate"] = 0.0
        return stats