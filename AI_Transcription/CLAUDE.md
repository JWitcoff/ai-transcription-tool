# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Main interactive menu (recommended)
python transcribe.py

# Quick URL transcription (direct workflow)
python quick_url_transcribe.py

# Web interface
streamlit run app.py
```

### Testing
```bash
# Run comprehensive ElevenLabs integration tests
cd tests && python test_elevenlabs.py

# Run specific test level
cd tests && python -c "from test_elevenlabs import *; test_level_1_connectivity()"
```

### Dependencies
```bash
# Install requirements
pip install -r requirements.txt

# System dependency (required)
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Linux
```

### Development Testing
```bash
# Test with sample YouTube URL
python quick_url_transcribe.py "https://www.youtube.com/watch?v=6KOxyJlgbyw"

# Validate ElevenLabs API
python -c "from elevenlabs_scribe import ScribeClient; client = ScribeClient(); print('API OK' if client.client else 'API Not Available')"
```

## Architecture Overview

This is a multi-provider AI transcription system with intelligent fallback architecture:

**Primary Pipeline**: Audio Source → Transcription → Diarization → Analysis → Export

### Core Provider System

**ElevenLabs Scribe (Primary)**
- Premium accuracy with built-in speaker diarization (up to 32 speakers)
- Handles file uploads (3GB limit) and cloud URLs (2GB limit)
- Critical API rule: `diarization_threshold` only when `diarize=True AND num_speakers=None`
- Multi-channel audio support with `channel_index` mapping
- Located in: `elevenlabs_scribe.py`

**OpenAI Whisper (Fallback)**
- Local processing with multiple model sizes (tiny → large)
- Optional pyannote.audio integration for speaker diarization
- GPU acceleration support
- Located in: `audio_transcriber.py`

### Entry Points Architecture

1. **`transcribe.py`** - Interactive CLI menu with 6 transcription modes
2. **`quick_url_transcribe.py`** - Streamlined single-URL processing
3. **`app.py`** - Streamlit web interface with real-time progress
4. **`live_cli.py`** - Real-time microphone transcription
5. **`simple_transcribe.py`** - Advanced CLI with quality tiers

### Analysis Engine

**Dual Analysis System:**
- **OpenAI GPT-4** (`openai_analyzer.py`) - Advanced analysis with fallback to local
- **Local Models** (`analyzer.py`) - BART/RoBERTa models for offline analysis

### Output Formats

All transcripts saved to `transcripts/` directory:
- `.txt` - Human-readable with speaker labels
- `.json` - Complete data with metadata
- `.srt` - Subtitle format with timestamps
- `.vtt` - WebVTT format with voice tags
- `_segments.json` - Structured segment data

### Configuration

**Environment Variables** (`.env` file):
```bash
ELEVENLABS_SCRIBE_KEY=your_api_key_here  # Required for premium provider
OPENAI_API_KEY=your_openai_key           # Optional, for advanced analysis
USE_SCRIBE=true                          # Enable/disable ElevenLabs Scribe
```

### Testing Architecture

**4-Level Health Check System** (`tests/test_elevenlabs.py`):
- **Level 1**: API connectivity and validation
- **Level 2**: Basic transcription without diarization  
- **Level 3A**: Speaker diarization with threshold testing
- **Level 3B**: Multi-channel audio processing
- **Level 4**: End-to-end YouTube pipeline validation

### Key Implementation Details

**ElevenLabs API Critical Rule** (`elevenlabs_scribe.py:142-145`):
```python
# CRITICAL: Only set threshold when diarize=True AND num_speakers=None
if diarize and num_speakers is None and diarization_threshold is not None:
    payload["diarization_threshold"] = diarization_threshold
```

**Provider Fallback Logic** (`audio_transcriber.py:98-115`):
```python
if self.diarization_provider == 'elevenlabs':
    # Use ElevenLabs Scribe with built-in diarization
    return self.elevenlabs_scribe.transcribe(...)
else:
    # Fall back to Whisper + optional pyannote
    return self._transcribe_with_whisper(...)
```

**Word-to-Segment Grouping** (`elevenlabs_scribe.py:222-255`):
- Groups consecutive words by speaker with configurable gap threshold
- Handles speaker transitions and silence periods
- Maintains precise timestamps for caption generation

### Dependencies

**Core ML/AI:**
- `openai-whisper` - Speech recognition
- `transformers`, `torch` - Local ML models
- `pyannote.audio>=3.1.0` - Speaker diarization

**Audio/Video Processing:**
- `yt-dlp` - Video/audio downloading
- `ffmpeg-python` - Audio format conversion

**API/Web:**
- `streamlit>=1.28.0` - Web interface
- `requests` - HTTP clients
- `openai` - GPT integration

**Analysis:**
- `numpy`, `pandas` - Data processing
- `matplotlib`, `seaborn` - Visualization (web interface)