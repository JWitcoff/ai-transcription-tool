# MCP Server for YouTube Transcription

This MCP (Model Context Protocol) server provides AI agents with direct access to YouTube video transcription and audio download capabilities.

## Features

- **Audio Download**: Extract audio from any video URL without transcription (MP3/WAV/FLAC)
- **High-Accuracy Transcription**: 96.7% accuracy with ElevenLabs Scribe
- **Speaker Diarization**: Identify up to 32 different speakers
- **Custom Analysis**: Apply specific analysis prompts to transcripts
- **Session Management**: Store and retrieve past transcriptions
- **Multiple Formats**: Export as SRT, VTT, JSON, or plain text

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** (required for audio processing):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows - download from https://ffmpeg.org/download.html
   ```

### Setup

1. **Install MCP package**:
   ```bash
   pip install "mcp[cli]"
   ```

2. **Install transcription dependencies**:
   ```bash
   cd AI_Transcription
   pip install -r requirements.txt
   ```

3. **Configure API keys** (optional, for premium features):
   Create a `.env` file in the AI_Transcription directory:
   ```bash
   # For premium transcription with speaker diarization
   ELEVENLABS_SCRIBE_KEY=your_elevenlabs_api_key
   
   # For AI analysis features
   OPENAI_API_KEY=your_openai_api_key
   ```

## Configuration for Claude Desktop

Add to your Claude Desktop configuration file:

### macOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Location: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration:
```json
{
  "mcpServers": {
    "youtube-transcription": {
      "command": "python",
      "args": ["/absolute/path/to/AI_Transcription/mcp_transcription_server.py"],
      "env": {
        "ELEVENLABS_SCRIBE_KEY": "your_key_here",
        "OPENAI_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Available Tools

### 1. `download_audio_only`
Download audio from any video URL without transcription.

**Parameters:**
- `url` (required): Video/audio URL to download from
- `format` (optional): Audio format - "mp3", "wav", or "flac" (default: "mp3")

**Example:**
```python
result = await download_audio_only(
    url="https://youtube.com/watch?v=...",
    format="mp3"
)
```

**Returns:**
```json
{
  "file_path": "/path/to/audio.mp3",
  "title": "Video Title",
  "duration": 1234,
  "format": "mp3",
  "file_size": 12345678,
  "metadata": {...},
  "session_id": "20250829_123456"
}
```

### 2. `transcribe_youtube`
Transcribe YouTube video with high accuracy and speaker diarization.

**Parameters:**
- `url` (required): YouTube video URL
- `include_analysis` (optional): Include AI analysis (default: true)

**Example:**
```python
result = await transcribe_youtube(
    url="https://youtube.com/watch?v=...",
    include_analysis=True
)
```

**Returns:**
```json
{
  "transcript": "Full transcript text...",
  "speakers": ["Speaker A", "Speaker B"],
  "segments": [...],
  "analysis": {
    "summary": "...",
    "themes": [...],
    "sentiment": {...}
  },
  "metadata": {...},
  "session_id": "20250829_123456"
}
```

### 3. `transcribe_with_custom_prompt`
Transcribe and analyze with custom questions.

**Parameters:**
- `url` (required): Video URL
- `analysis_prompt` (required): Custom analysis prompt

**Example:**
```python
result = await transcribe_with_custom_prompt(
    url="https://youtube.com/watch?v=...",
    analysis_prompt="Extract all growth strategies mentioned"
)
```

### 4. `get_video_segments`
Get timestamped segments in SRT or VTT format.

**Parameters:**
- `url` (required): Video URL
- `format` (optional): "srt" or "vtt" (default: "srt")

**Example:**
```python
segments = await get_video_segments(
    url="https://youtube.com/watch?v=...",
    format="srt"
)
```

## Available Resources

### 1. `transcript://{session_id}`
Retrieve past transcription by session ID.

**Example:**
```python
transcript = await get_resource("transcript://20250829_123456")
```

### 2. `audio://{session_id}`
Retrieve downloaded audio file info by session ID.

**Example:**
```python
audio_info = await get_resource("audio://20250829_123456")
```

### 3. `sessions://list`
List all transcription and audio download sessions.

**Example:**
```python
sessions = await get_resource("sessions://list")
```

## Usage Examples

### For AI Agents

1. **Download audio only:**
   ```
   User: "Download the audio from this YouTube video"
   Agent: Uses download_audio_only() tool
   Result: Audio file saved locally with metadata
   ```

2. **Full transcription with analysis:**
   ```
   User: "Transcribe this video and tell me the key points"
   Agent: Uses transcribe_youtube() tool
   Result: Complete transcript with speaker labels and AI analysis
   ```

3. **Custom analysis:**
   ```
   User: "What growth strategies are mentioned in this video?"
   Agent: Uses transcribe_with_custom_prompt() with specific prompt
   Result: Transcript with targeted analysis
   ```

4. **Get subtitles:**
   ```
   User: "Generate SRT subtitles for this video"
   Agent: Uses get_video_segments() tool
   Result: Properly formatted SRT file content
   ```

## Testing the Server

### Basic Test
```bash
# Test server startup
python mcp_transcription_server.py

# In another terminal, test with MCP CLI
mcp-cli call youtube-transcription download_audio_only '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp3"}'
```

### Test All Functions
```python
# Create a test script
python -c "
import asyncio
from mcp_transcription_server import (
    download_audio_only,
    transcribe_youtube,
    list_sessions
)

async def test():
    # Test audio download
    audio = await download_audio_only(
        url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        format='mp3'
    )
    print('Audio download:', audio.get('title'))
    
    # Test transcription
    transcript = await transcribe_youtube(
        url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        include_analysis=True
    )
    print('Transcription:', len(transcript.get('transcript', '')), 'characters')
    
    # List sessions
    sessions = await list_sessions()
    print('Sessions found:', len(sessions))

asyncio.run(test())
"
```

## Troubleshooting

### Common Issues

1. **"FFmpeg not found"**
   - Install FFmpeg using the commands in Prerequisites

2. **"Module 'mcp' not found"**
   - Install with: `pip install "mcp[cli]"`

3. **"ElevenLabs API key not set"**
   - The server works without API keys using Whisper
   - For premium features, add keys to `.env` file

4. **Slow first run**
   - Whisper models download on first use (~1-2GB)
   - Subsequent runs are much faster

### Performance Tips

- **With API Keys**: Uses cloud-based ElevenLabs Scribe (faster, more accurate)
- **Without API Keys**: Uses local Whisper models (free, good accuracy)
- **GPU Acceleration**: Enable CUDA for faster local transcription
- **Audio-Only Mode**: Use when transcription isn't needed to save time

## API Key Information

### ElevenLabs Scribe (Optional)
- Provides 96.7% accuracy with speaker diarization
- Sign up at [elevenlabs.io](https://elevenlabs.io)
- Get API key from Settings → API Keys
- Cost: ~$0.40 per hour of audio

### OpenAI (Optional)
- Enables advanced AI analysis features
- Sign up at [platform.openai.com](https://platform.openai.com)
- Create API key in dashboard
- Used for summaries, themes, custom analysis

## Architecture

The MCP server integrates with the existing AI Transcription Tool:

```
MCP Client (Claude Desktop, etc.)
    ↓
mcp_transcription_server.py
    ↓
┌─────────────────────────────────┐
│  Audio Download │ Transcription  │
├─────────────────┼─────────────────┤
│    yt-dlp       │ ElevenLabs API │
│    FFmpeg       │ Whisper Models │
│                 │ Speaker Diariz. │
└─────────────────┴─────────────────┘
    ↓
Session Storage (downloads/ & transcripts/)
```

## Support

- **Documentation**: See main [README.md](README.md)
- **Issues**: Report at project repository
- **Logs**: Check `video_transcription.log` for detailed errors

## License

This MCP server is part of the AI Transcription Tool project.