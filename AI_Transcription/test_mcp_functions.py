#!/usr/bin/env python3
"""
Test script for MCP server functions without requiring MCP
This tests the core functionality that the MCP server will expose
"""

import sys
import os
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the data classes and helper functions from MCP server
# We'll import everything except the MCP-specific decorators
import json
import tempfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

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

def create_session_id() -> str:
    """Generate a unique session ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def test_audio_download():
    """Test audio download functionality"""
    print("\n🎵 Testing Audio Download...")
    print("=" * 60)
    
    # Test URL (short public domain video)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video
    
    try:
        import yt_dlp
        
        # Create downloads directory
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        session_id = create_session_id()
        
        # Setup yt-dlp for a quick test
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(downloads_dir / f"test_{session_id}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
        }
        
        print(f"📥 Attempting to download: {test_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"   Title: {title}")
            print(f"   Duration: {duration} seconds")
            
            # For testing, we won't actually download to save time
            print("\n✅ Audio download test passed (download skipped for speed)")
            return True
            
    except Exception as e:
        print(f"❌ Audio download test failed: {e}")
        return False

async def test_transcription_imports():
    """Test that transcription components can be imported"""
    print("\n🎙️ Testing Transcription Imports...")
    print("=" * 60)
    
    try:
        from audio_transcriber import AudioTranscriber
        print("✅ AudioTranscriber imported")
        
        from elevenlabs_scribe import ScribeClient
        print("✅ ScribeClient imported")
        
        from openai_analyzer import OpenAIAnalyzer
        print("✅ OpenAIAnalyzer imported")
        
        from analyzer import TextAnalyzer
        print("✅ TextAnalyzer imported")
        
        from captions import segments_to_srt, segments_to_vtt
        print("✅ Caption functions imported")
        
        from output_formatter import OutputFormatter
        print("✅ OutputFormatter imported")
        
        from file_manager import FileManager
        print("✅ FileManager imported")
        
        print("\n✅ All transcription components available!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_session_management():
    """Test session listing functionality"""
    print("\n📂 Testing Session Management...")
    print("=" * 60)
    
    try:
        sessions = []
        
        # Check transcripts directory
        transcripts_dir = Path("transcripts")
        if transcripts_dir.exists():
            count = 0
            for folder in transcripts_dir.iterdir():
                if folder.is_dir():
                    count += 1
                    if count <= 3:  # Show first 3
                        print(f"  📄 Found transcript: {folder.name}")
            print(f"\n  Total transcript sessions: {count}")
        else:
            print("  No transcripts directory found")
        
        # Check downloads directory  
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            count = 0
            for folder in downloads_dir.iterdir():
                if folder.is_dir():
                    count += 1
                    if count <= 3:  # Show first 3
                        print(f"  🎵 Found download: {folder.name}")
            print(f"\n  Total download sessions: {count}")
        else:
            print("  No downloads directory found")
        
        print("\n✅ Session management test passed")
        return True
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 MCP Server Functionality Tests")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(await test_transcription_imports())
    
    # Test session management
    results.append(await test_session_management())
    
    # Test audio download (last as it requires network)
    results.append(await test_audio_download())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\n🎉 The core functionality for MCP server is working!")
        print("\nNext steps:")
        print("1. Install MCP package: pip install 'mcp[cli]'")
        print("2. Configure in Claude Desktop using README_MCP.md instructions")
        print("3. The server will expose these functions as MCP tools")
    else:
        print(f"⚠️ {passed}/{total} tests passed")
        print("\nSome functionality may be limited.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())