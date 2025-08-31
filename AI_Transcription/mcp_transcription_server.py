#!/usr/bin/env python3
"""
MCP Server for YouTube Transcription and Audio Download
Provides agents with direct access to high-accuracy transcription and audio extraction
"""

import os
import sys
import json
import tempfile
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import MCP, provide helpful error if not available
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: MCP package not found. Please install with:")
    print("  pip install 'mcp[cli]'")
    print("\nOr if using virtual environment:")
    print("  source venv/bin/activate")
    print("  pip install 'mcp[cli]'")
    sys.exit(1)

# Import existing components
import yt_dlp
from audio_transcriber import AudioTranscriber
from elevenlabs_scribe import ScribeClient
from openai_analyzer import OpenAIAnalyzer
from analyzer import TextAnalyzer
from captions import segments_to_srt, segments_to_vtt, Segment as CaptionSegment
from custom_analyzer import CustomAnalyzer
from output_formatter import OutputFormatter
from file_manager import FileManager

# Initialize MCP server
mcp = FastMCP("YouTube Transcription")

# Initialize components
file_manager = FileManager()
output_formatter = OutputFormatter()

@dataclass
class AudioDownloadResult:
    """Result from audio download operation"""
    file_path: str
    title: str
    duration: int
    format: str
    file_size: int
    metadata: Dict[str, Any]
    session_id: str

@dataclass
class TranscriptionResult:
    """Result from transcription operation"""
    transcript: str
    speakers: Optional[List[str]]
    segments: Optional[List[Dict]]
    analysis: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: str

# Helper functions
def create_session_id() -> str:
    """Generate a unique session ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def download_audio_from_url(url: str, format: str = "mp3") -> AudioDownloadResult:
    """Download audio from URL using yt-dlp"""
    
    # Create downloads directory
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    # Generate session ID
    session_id = create_session_id()
    
    # Setup format configuration
    format_map = {
        "mp3": {"ext": "mp3", "codec": "mp3", "quality": "192"},
        "wav": {"ext": "wav", "codec": "wav", "quality": "192"},
        "flac": {"ext": "flac", "codec": "flac", "quality": "192"}
    }
    
    audio_format = format_map.get(format.lower(), format_map["mp3"])
    
    # Setup yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(downloads_dir / f"{session_id}_%(title)s.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format['codec'],
            'preferredquality': audio_format['quality'],
        }],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            description = info.get('description', '')
            uploader = info.get('uploader', 'Unknown')
            upload_date = info.get('upload_date', '')
            
            # Download the audio
            ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = list(downloads_dir.glob(f"{session_id}_*.{audio_format['ext']}"))
            
            if downloaded_files:
                audio_file = downloaded_files[0]
                file_size = audio_file.stat().st_size
                
                # Create session folder
                safe_title = title[:50].replace('/', '_').replace('\\', '_')
                session_folder = downloads_dir / f"{session_id}_{safe_title}"
                session_folder.mkdir(exist_ok=True)
                
                # Move file to session folder
                final_file = session_folder / f"{safe_title}.{audio_format['ext']}"
                shutil.move(str(audio_file), str(final_file))
                
                # Create metadata
                metadata = {
                    'title': title,
                    'duration': duration,
                    'description': description,
                    'uploader': uploader,
                    'upload_date': upload_date,
                    'url': url,
                    'download_date': datetime.now().isoformat(),
                    'format': audio_format['ext'],
                    'file_size': file_size,
                    'file_path': str(final_file)
                }
                
                # Save metadata
                metadata_file = session_folder / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                return AudioDownloadResult(
                    file_path=str(final_file),
                    title=title,
                    duration=duration,
                    format=audio_format['ext'],
                    file_size=file_size,
                    metadata=metadata,
                    session_id=session_id
                )
            else:
                raise Exception("Audio file not found after download")
                
    except Exception as e:
        raise Exception(f"Audio download failed: {str(e)}")

async def transcribe_from_url(url: str, include_analysis: bool = True, 
                             custom_prompt: Optional[str] = None) -> TranscriptionResult:
    """Transcribe audio from URL with optional analysis"""
    
    session_id = create_session_id()
    
    # First download the audio
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_audio = os.path.join(temp_dir, f"transcribe_audio_{timestamp}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Find the output file
            audio_file = None
            for file in Path(temp_dir).glob(f"transcribe_audio_{timestamp}.*"):
                audio_file = str(file)
                break
            
            if not audio_file:
                raise Exception("Audio file not found after download")
            
            # Transcribe with best available method
            use_scribe = os.getenv("USE_SCRIBE", "true").lower() == "true"
            
            if use_scribe:
                try:
                    # Try ElevenLabs Scribe first
                    transcriber = AudioTranscriber(
                        model_size='base',
                        enable_diarization=True,
                        diarization_provider='elevenlabs'
                    )
                    
                    if transcriber.diarization_provider == 'elevenlabs':
                        result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)
                        if result and result.get('text'):
                            provider = 'elevenlabs_scribe'
                        else:
                            raise Exception("Scribe transcription failed")
                    else:
                        raise Exception("Scribe not available")
                        
                except:
                    # Fall back to Whisper
                    transcriber = AudioTranscriber(
                        model_size='base',
                        enable_diarization=False
                    )
                    result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)
                    provider = 'whisper'
            else:
                # Use Whisper directly
                transcriber = AudioTranscriber(
                    model_size='base',
                    enable_diarization=False
                )
                result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)
                provider = 'whisper'
            
            # Extract speakers if available
            speakers = None
            if result.get('segments'):
                unique_speakers = set()
                for segment in result['segments']:
                    if 'speaker' in segment:
                        unique_speakers.add(segment['speaker'])
                if unique_speakers:
                    speakers = sorted(list(unique_speakers))
            
            # Perform analysis if requested
            analysis = None
            if include_analysis and result.get('text'):
                try:
                    # Try OpenAI first
                    analyzer = OpenAIAnalyzer()
                    if custom_prompt:
                        # Use custom analyzer for specific prompts
                        custom_analyzer = CustomAnalyzer(openai_analyzer=analyzer)
                        analysis = custom_analyzer.analyze_with_prompt(result['text'], custom_prompt)
                    else:
                        # Standard analysis
                        summary = analyzer.summarize(result['text'])
                        themes = analyzer.extract_themes(result['text'])
                        sentiment = analyzer.analyze_sentiment(result['text'])
                        analysis = {
                            'summary': summary,
                            'themes': themes,
                            'sentiment': sentiment
                        }
                except:
                    # Fall back to local analyzer
                    analyzer = TextAnalyzer()
                    summary = analyzer.summarize(result['text'])
                    themes = analyzer.extract_themes(result['text'])
                    sentiment = analyzer.analyze_sentiment(result['text'])
                    analysis = {
                        'summary': summary,
                        'themes': themes,
                        'sentiment': sentiment
                    }
            
            # Save transcription to files
            output_dir = Path("transcripts")
            output_dir.mkdir(exist_ok=True)
            
            # Create session folder
            safe_title = title[:50].replace('/', '_').replace('\\', '_')
            session_folder = output_dir / f"{session_id}_youtube_{safe_title}"
            session_folder.mkdir(exist_ok=True)
            
            # Save files
            output_formatter.save_all_formats(
                result=result,
                output_dir=str(session_folder),
                prefix="",
                metadata={
                    'title': title,
                    'url': url,
                    'duration': duration,
                    'provider': provider,
                    'analysis': analysis
                }
            )
            
            # Clean up temp file
            try:
                os.remove(audio_file)
            except:
                pass
            
            return TranscriptionResult(
                transcript=result['text'],
                speakers=speakers,
                segments=result.get('segments'),
                analysis=analysis,
                metadata={
                    'title': title,
                    'duration': duration,
                    'url': url,
                    'provider': provider,
                    'timestamp': datetime.now().isoformat()
                },
                session_id=session_id
            )
            
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

# MCP Tool Definitions

@mcp.tool()
async def download_audio_only(url: str, format: str = "mp3") -> Dict[str, Any]:
    """
    Download audio from URL without transcription
    
    Args:
        url: Video/audio URL to download from (YouTube, Twitch, Vimeo, etc.)
        format: Audio format - 'mp3', 'wav', or 'flac' (default: mp3)
    
    Returns:
        Dictionary containing file_path, metadata, and download information
    """
    try:
        result = await download_audio_from_url(url, format)
        return asdict(result)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def transcribe_youtube(url: str, include_analysis: bool = True) -> Dict[str, Any]:
    """
    Transcribe YouTube video with high accuracy and speaker diarization
    
    Args:
        url: YouTube video URL to transcribe
        include_analysis: Whether to include AI analysis (summary, themes, sentiment)
    
    Returns:
        Dictionary containing transcript, speakers, segments, and optional analysis
    """
    try:
        result = await transcribe_from_url(url, include_analysis)
        return asdict(result)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def transcribe_with_custom_prompt(url: str, analysis_prompt: str) -> Dict[str, Any]:
    """
    Transcribe video and analyze with custom questions
    
    Args:
        url: Video URL to transcribe
        analysis_prompt: Custom analysis prompt (e.g., "Extract all growth strategies mentioned")
    
    Returns:
        Dictionary containing transcript and custom analysis results
    """
    try:
        result = await transcribe_from_url(url, include_analysis=True, custom_prompt=analysis_prompt)
        return asdict(result)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_video_segments(url: str, format: str = "srt") -> str:
    """
    Get timestamped segments in SRT or VTT format
    
    Args:
        url: Video URL to process
        format: Output format - 'srt' or 'vtt' (default: srt)
    
    Returns:
        String containing formatted subtitles/captions
    """
    try:
        # Transcribe to get segments
        result = await transcribe_from_url(url, include_analysis=False)
        
        if not result.segments:
            return "No segments available - transcription may not include timestamps"
        
        # Convert segments to caption format
        caption_segments = []
        for seg in result.segments:
            if 'start' in seg and 'end' in seg and 'text' in seg:
                caption_segments.append(CaptionSegment(
                    start=seg['start'],
                    end=seg['end'],
                    text=seg['text'],
                    speaker=seg.get('speaker')
                ))
        
        if format.lower() == "vtt":
            return segments_to_vtt(caption_segments)
        else:
            return segments_to_srt(caption_segments)
            
    except Exception as e:
        return f"Error generating segments: {str(e)}"

# MCP Resource Definitions

@mcp.resource("transcript://{session_id}")
async def get_transcript(session_id: str) -> Dict[str, Any]:
    """
    Retrieve past transcription by session ID
    
    Args:
        session_id: Session ID of the transcription (format: YYYYMMDD_HHMMSS)
    
    Returns:
        Dictionary containing transcript and metadata
    """
    try:
        # Look for transcript in transcripts directory
        transcripts_dir = Path("transcripts")
        
        # Find matching session folder
        for folder in transcripts_dir.glob(f"{session_id}_*"):
            if folder.is_dir():
                # Load transcript
                transcript_file = folder / "transcript.txt"
                metadata_file = folder / "metadata.json"
                
                if transcript_file.exists():
                    transcript = transcript_file.read_text(encoding='utf-8')
                    
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    
                    return {
                        "session_id": session_id,
                        "transcript": transcript,
                        "metadata": metadata,
                        "folder": str(folder)
                    }
        
        return {"error": f"Transcript not found for session {session_id}"}
        
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("audio://{session_id}")
async def get_audio_file(session_id: str) -> Dict[str, Any]:
    """
    Retrieve downloaded audio file info by session ID
    
    Args:
        session_id: Session ID of the audio download
    
    Returns:
        Dictionary containing file path and metadata
    """
    try:
        # Look for audio in downloads directory
        downloads_dir = Path("downloads")
        
        # Find matching session folder
        for folder in downloads_dir.glob(f"{session_id}_*"):
            if folder.is_dir():
                # Load metadata
                metadata_file = folder / "metadata.json"
                
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    return {
                        "session_id": session_id,
                        "file_path": metadata.get('file_path'),
                        "metadata": metadata,
                        "folder": str(folder)
                    }
        
        return {"error": f"Audio file not found for session {session_id}"}
        
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("sessions://list")
async def list_sessions() -> List[Dict[str, Any]]:
    """
    List all transcription and audio download sessions
    
    Returns:
        List of session information dictionaries
    """
    sessions = []
    
    try:
        # Get transcription sessions
        transcripts_dir = Path("transcripts")
        if transcripts_dir.exists():
            for folder in transcripts_dir.iterdir():
                if folder.is_dir() and folder.name.count('_') >= 2:
                    # Extract session ID from folder name
                    parts = folder.name.split('_')
                    if len(parts[0]) == 8 and len(parts[1]) == 6:  # YYYYMMDD_HHMMSS format
                        session_id = f"{parts[0]}_{parts[1]}"
                        
                        # Load metadata if available
                        metadata_file = folder / "metadata.json"
                        metadata = {}
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        
                        sessions.append({
                            "session_id": session_id,
                            "type": "transcription",
                            "title": metadata.get('title', folder.name),
                            "timestamp": metadata.get('timestamp', session_id),
                            "folder": str(folder)
                        })
        
        # Get audio download sessions
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            for folder in downloads_dir.iterdir():
                if folder.is_dir() and folder.name.count('_') >= 2:
                    # Extract session ID from folder name
                    parts = folder.name.split('_')
                    if len(parts[0]) == 8 and len(parts[1]) == 6:  # YYYYMMDD_HHMMSS format
                        session_id = f"{parts[0]}_{parts[1]}"
                        
                        # Load metadata if available
                        metadata_file = folder / "metadata.json"
                        metadata = {}
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        
                        sessions.append({
                            "session_id": session_id,
                            "type": "audio_download",
                            "title": metadata.get('title', folder.name),
                            "format": metadata.get('format', 'unknown'),
                            "timestamp": metadata.get('download_date', session_id),
                            "folder": str(folder)
                        })
        
        # Sort by timestamp (most recent first)
        sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return sessions
        
    except Exception as e:
        return [{"error": str(e)}]

# Main entry point
if __name__ == "__main__":
    # Run the MCP server
    import asyncio
    asyncio.run(mcp.run())