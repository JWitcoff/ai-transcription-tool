# Architecture Documentation

## System Overview

This is a multi-provider AI transcription system with intelligent fallback architecture:

**Primary Pipeline**: Audio Source → Transcription → Diarization → Analysis → Export

## Core Provider System

### ElevenLabs Scribe (Primary)
- Premium accuracy with built-in speaker diarization (up to 32 speakers)
- Handles file uploads (3GB limit) and cloud URLs (2GB limit)
- Critical API rule: `diarization_threshold` only when `diarize=True AND num_speakers=None`
- Multi-channel audio support with `channel_index` mapping
- Located in: `elevenlabs_scribe.py`

### OpenAI Whisper (Fallback)
- Local processing with multiple model sizes (tiny → large)
- Optional pyannote.audio integration for speaker diarization
- GPU acceleration support
- Located in: `audio_transcriber.py`

## Entry Points Architecture

1. **`transcribe.py`** - Interactive CLI menu with 9 transcription modes
2. **`quick_url_transcribe.py`** - Streamlined single-URL processing with clean UI
3. **`app.py`** - Streamlit web interface with real-time progress
4. **`live_cli.py`** - Real-time microphone transcription
5. **`simple_transcribe.py`** - Advanced CLI with quality tiers
6. **`mcp_transcription_server.py`** - MCP server for AI agents

## Clean UI Architecture

**Minimal Terminal Interface:**
- **CleanUI Class** (`clean_ui.py`) - Single-line progress tracking system
- **3-Stage Progress** - [🔊] Transcribing → [🧠] Analyzing → [✅] Complete
- **Dynamic ETA Updates** - Real-time countdown with human-readable formatting
- **Model Selection Display** - ElevenLabs Scribe ✅ or Whisper ⚠️ fallback indication
- **Output Suppression** - Context manager to silence verbose model loading/download logs
- **Professional Summary** - Duration, speakers, confidence stats in single line

**Key Features:**
- Reduces output from 50+ verbose lines to ~10 clean lines
- Single updating status line with in-place progress updates
- Global function interface for easy integration across modules
- Test suite (`test_clean_ui.py`) for UI functionality validation

## Analysis Engine

**Triple-Layer Analysis System:**
- **Enhanced Deep Extraction** (`extractors/enhanced_deep_extractor.py`) - Content-aware extraction with automatic rubric selection
- **OpenAI GPT-4** (`openai_analyzer.py`) - Advanced analysis with fallback to local
- **Local Models** (`analyzer.py`) - BART/RoBERTa models for offline analysis

## Enhanced Extraction System

**Pluggable Rubric Architecture:**
- **Rubric Selector** (`extractors/rubric_selector.py`) - Automatic content-type detection
- **Enhanced Validator** (`extractors/enhanced_validator.py`) - Fragment quality and schema compliance
- **Contract System** (`extractors/contracts.py`) - Pydantic-based output validation
- **Fragment Guards** (`extractors/guards.py`) - Smart guards against rubric leakage
- **Timestamp Alignment** (`extractors/align.py`) - Order-preserving fuzzy matching for SRT/VTT
- **Truthful Telemetry** (`extractors/truthful_telemetry.py`) - Verifiable metrics without fake data

**Available Rubrics:**
- `prompting_claude_v1` - Prompt engineering content (role, guardrails, templates)
- `yt_playbook_v1` - YouTube growth content (frameworks, metrics, case studies)

**Quality Pipeline:**
1. Content detection → Select appropriate rubric
2. Contract validation → Enforce strict output schema
3. Fragment validation → Reject broken text with smart guards
4. Schema compliance → Ensure structure
5. Timestamp alignment → Map chapters to SRT/VTT timestamps
6. Round-trip testing → Verify usability
7. Truthful telemetry → Log verifiable metrics only

## MCP Server Architecture

**Model Context Protocol Integration:**
- **FastMCP Server** - Exposes transcription tools to AI agents
- **Audio Download Tool** - `download_audio_only()` matches CLI Option 1
- **Transcription Tools** - Full transcription with custom analysis prompts
- **Resource Endpoints** - Access past sessions and files
- **Session Management** - Integrates with existing `downloads/` and `transcripts/` folders
- **Automatic Provider Selection** - Uses ElevenLabs → Whisper fallback like other entry points

## Output Formats

All transcripts saved to `transcripts/` directory:
- `.txt` - Human-readable with speaker labels
- `.json` - Complete data with metadata
- `.srt` - Subtitle format with timestamps
- `.vtt` - WebVTT format with voice tags
- `_segments.json` - Structured segment data

## Configuration

**Environment Variables** (`.env` file):
```bash
ELEVENLABS_SCRIBE_KEY=your_api_key_here  # Required for premium provider
OPENAI_API_KEY=your_openai_key           # Optional, for advanced analysis
USE_SCRIBE=true                          # Enable/disable ElevenLabs Scribe
```

## Key Implementation Details

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