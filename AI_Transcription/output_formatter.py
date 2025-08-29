"""
Output Formatter - Properly format transcripts and analysis for saving
Handles both diarized (with speakers) and non-diarized transcripts
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

class OutputFormatter:
    """Format transcripts and analysis for readable output"""
    
    def __init__(self):
        self.paragraph_sentences = 3  # Sentences per paragraph for non-diarized
        self.max_line_length = 100  # Max characters per line for readability
    
    def format_transcript(self, result: Dict[str, Any], source_url: str = "") -> str:
        """
        Format a transcript for saving to file
        
        Args:
            result: Transcription result dictionary
            source_url: Optional source URL
            
        Returns:
            Formatted transcript string
        """
        # Build header
        header = self._build_header(result, source_url)
        
        # Format body based on whether we have diarization
        if result.get("has_diarization") and result.get("segments"):
            body = self._format_diarized_transcript(result["segments"])
        else:
            body = self._format_non_diarized_transcript(
                result.get("text", ""),
                result.get("segments", [])
            )
        
        return header + body
    
    def _build_header(self, result: Dict[str, Any], source_url: str) -> str:
        """Build the header section of the transcript"""
        header_lines = []
        header_lines.append("=" * 70)
        header_lines.append("TRANSCRIPT")
        header_lines.append("=" * 70)
        
        if source_url:
            header_lines.append(f"Source: {source_url}")
        
        header_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        header_lines.append(f"Provider: {result.get('provider', 'unknown')}")
        
        if result.get('language'):
            header_lines.append(f"Language: {result.get('language')}")
        
        if result.get('has_diarization'):
            num_speakers = len(set(s.get('speaker', '') for s in result.get('segments', [])))
            header_lines.append(f"Speakers Detected: {num_speakers}")
        
        header_lines.append("=" * 70)
        header_lines.append("")  # Empty line before content
        
        return "\n".join(header_lines) + "\n"
    
    def _format_diarized_transcript(self, segments: List[Dict]) -> str:
        """Format transcript with speaker labels"""
        formatted_lines = []
        current_speaker = None
        current_paragraph = []
        
        for segment in segments:
            speaker = segment.get("speaker", "Unknown")
            text = segment.get("text", "").strip()
            
            if not text:
                continue
            
            # Check for speaker change
            if speaker != current_speaker:
                # Save current paragraph if exists
                if current_paragraph:
                    formatted_lines.append(" ".join(current_paragraph))
                    formatted_lines.append("")  # Empty line after paragraph
                    current_paragraph = []
                
                # Add speaker label with nice formatting
                formatted_lines.append(f"\n{speaker}:")
                current_speaker = speaker
            
            # Add text to current paragraph
            current_paragraph.append(text)
            
            # Check if we should break paragraph (e.g., long pause, punctuation)
            if text.endswith(('.', '?', '!')) and len(current_paragraph) >= self.paragraph_sentences:
                formatted_lines.append(" ".join(current_paragraph))
                formatted_lines.append("")  # Empty line for readability
                current_paragraph = []
        
        # Don't forget last paragraph
        if current_paragraph:
            formatted_lines.append(" ".join(current_paragraph))
        
        return "\n".join(formatted_lines)
    
    def _format_non_diarized_transcript(self, text: str, segments: List[Dict] = None) -> str:
        """
        Format transcript without speaker labels into readable paragraphs
        """
        if not text:
            return ""
        
        # First, try to use segments if available (they have natural breaks)
        if segments:
            return self._format_with_segments(segments)
        
        # Otherwise, intelligently split into paragraphs
        return self._smart_paragraph_split(text)
    
    def _format_with_segments(self, segments: List[Dict]) -> str:
        """Format using segment boundaries for natural breaks"""
        formatted_lines = []
        current_paragraph = []
        last_end_time = 0
        
        for segment in segments:
            text = segment.get("text", "").strip()
            start_time = segment.get("start", 0)
            
            if not text:
                continue
            
            # Check for natural break (pause > 2 seconds)
            if start_time - last_end_time > 2.0 and current_paragraph:
                formatted_lines.append(" ".join(current_paragraph))
                formatted_lines.append("")  # Empty line
                current_paragraph = []
            
            current_paragraph.append(text)
            last_end_time = segment.get("end", start_time)
            
            # Also break on sentence count
            sentence_count = len(re.findall(r'[.!?]+', " ".join(current_paragraph)))
            if sentence_count >= self.paragraph_sentences:
                formatted_lines.append(" ".join(current_paragraph))
                formatted_lines.append("")  # Empty line
                current_paragraph = []
        
        # Don't forget last paragraph
        if current_paragraph:
            formatted_lines.append(" ".join(current_paragraph))
        
        return "\n".join(formatted_lines)
    
    def _smart_paragraph_split(self, text: str) -> str:
        """
        Intelligently split text into paragraphs based on sentence boundaries
        """
        # Clean up the text first
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into sentences (handling abbreviations)
        sentences = self._split_sentences(text)
        
        formatted_lines = []
        current_paragraph = []
        
        for sentence in sentences:
            current_paragraph.append(sentence)
            
            # Check if we should start a new paragraph
            if len(current_paragraph) >= self.paragraph_sentences:
                # Join sentences with proper spacing
                paragraph_text = " ".join(current_paragraph)
                
                # Wrap long lines for readability
                wrapped = self._wrap_text(paragraph_text)
                formatted_lines.append(wrapped)
                formatted_lines.append("")  # Empty line between paragraphs
                
                current_paragraph = []
        
        # Don't forget the last paragraph
        if current_paragraph:
            paragraph_text = " ".join(current_paragraph)
            wrapped = self._wrap_text(paragraph_text)
            formatted_lines.append(wrapped)
        
        return "\n".join(formatted_lines)
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, handling common edge cases
        """
        # Handle common abbreviations
        text = re.sub(r'\bDr\.\s', 'Dr^ ', text)
        text = re.sub(r'\bMr\.\s', 'Mr^ ', text)
        text = re.sub(r'\bMs\.\s', 'Ms^ ', text)
        text = re.sub(r'\bMrs\.\s', 'Mrs^ ', text)
        text = re.sub(r'\be\.g\.\s', 'e^g^ ', text)
        text = re.sub(r'\bi\.e\.\s', 'i^e^ ', text)
        
        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restore abbreviations
        sentences = [s.replace('^', '.') for s in sentences]
        
        # Filter out empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def _wrap_text(self, text: str, width: int = None) -> str:
        """
        Wrap text to specified width for better readability
        """
        if width is None:
            width = self.max_line_length
        
        # Don't wrap if text is short enough
        if len(text) <= width:
            return text
        
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            # Check if adding this word would exceed the width
            if current_length + word_length + len(current_line) > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    # Word is longer than width, add it anyway
                    lines.append(word)
            else:
                current_line.append(word)
                current_length += word_length
        
        # Don't forget the last line
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    def format_analysis(self, analysis_result: Dict[str, Any], include_metadata: bool = True) -> str:
        """
        Format analysis results for saving
        
        Args:
            analysis_result: Result from CustomAnalyzer
            include_metadata: Whether to include header metadata
            
        Returns:
            Formatted analysis string
        """
        lines = []
        
        if include_metadata:
            lines.append("=" * 70)
            lines.append("ANALYSIS")
            lines.append("=" * 70)
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if analysis_result.get('prompt'):
                lines.append(f"\nUser Request: {analysis_result['prompt']}")
            
            if analysis_result.get('provider'):
                lines.append(f"Analysis Provider: {analysis_result['provider']}")
            
            lines.append("=" * 70)
            lines.append("")
        
        # Add the actual analysis
        if analysis_result.get('analysis'):
            lines.append(analysis_result['analysis'])
        else:
            lines.append("No analysis generated.")
        
        # Add any notes
        if analysis_result.get('note'):
            lines.append("")
            lines.append(f"Note: {analysis_result['note']}")
        
        return "\n".join(lines)
    
    def format_combined_output(self, transcript: str, analysis: str) -> str:
        """
        Combine transcript and analysis into a single formatted output
        
        Args:
            transcript: Formatted transcript
            analysis: Formatted analysis
            
        Returns:
            Combined formatted string
        """
        combined = []
        combined.append(transcript)
        
        if analysis:
            combined.append("\n" * 3)  # Three line breaks between sections
            combined.append(analysis)
        
        return "\n".join(combined)
    
    def create_markdown_output(self, result: Dict, analysis_result: Dict = None, source_url: str = "") -> str:
        """
        Create a markdown-formatted version of the transcript and analysis
        """
        md_lines = []
        
        # Title
        md_lines.append("# Transcript")
        
        if source_url:
            md_lines.append(f"\n**Source:** {source_url}")
        
        md_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"**Provider:** {result.get('provider', 'unknown')}")
        
        md_lines.append("\n---\n")
        
        # Transcript content
        md_lines.append("## Content\n")
        
        if result.get("has_diarization") and result.get("segments"):
            current_speaker = None
            for segment in result["segments"]:
                speaker = segment.get("speaker", "Unknown")
                text = segment.get("text", "").strip()
                
                if speaker != current_speaker:
                    md_lines.append(f"\n**{speaker}:**")
                    current_speaker = speaker
                
                md_lines.append(f"{text}")
        else:
            # Format non-diarized as paragraphs
            text = result.get("text", "")
            paragraphs = self._smart_paragraph_split(text).split("\n\n")
            for para in paragraphs:
                if para.strip():
                    md_lines.append(f"\n{para}")
        
        # Analysis section
        if analysis_result and analysis_result.get('analysis'):
            md_lines.append("\n---\n")
            md_lines.append("## Analysis\n")
            
            if analysis_result.get('prompt'):
                md_lines.append(f"**User Request:** {analysis_result['prompt']}\n")
            
            md_lines.append(analysis_result['analysis'])
        
        return "\n".join(md_lines)