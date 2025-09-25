# CLAUDE.md - Core Project Guide

This file provides essential guidance to Claude Code when working with this AI transcription system.

## Quick Start Commands (Essential)

```bash
# Primary entry points
python transcribe.py           # Interactive menu (9 modes)
python quick_url_transcribe.py # Clean UI single-URL processing

# Testing
python test_clean_ui.py                                    # Test clean UI
python -c "from elevenlabs_scribe import ScribeClient; client = ScribeClient(); print('✅ ElevenLabs OK' if hasattr(client, 'api_key') and client.api_key else '❌ No API key')"

# MCP Server
python mcp_transcription_server.py                        # For AI agents
```

## Critical Rules (Must Know)

### ElevenLabs API Constraint
```python
# CRITICAL: Only set threshold when diarize=True AND num_speakers=None
if diarize and num_speakers is None and diarization_threshold is not None:
    payload["diarization_threshold"] = diarization_threshold
```
**Location:** `elevenlabs_scribe.py:142-145` - This will cause 400 errors if violated!

### Provider Fallback Logic
```python
if self.diarization_provider == 'elevenlabs':
    # Use ElevenLabs Scribe (preferred)
else:
    # Fall back to Whisper + pyannote
```

### Clean UI Integration
- Use `OutputSuppressor` context manager for silent operations
- Show model selection: ElevenLabs ✅ or Whisper ⚠️
- 3 stages only: `transcribe` → `analyze` → `complete`

## Architecture Summary (Context)

**Primary Pipeline:** Audio Source → Transcription → Diarization → Analysis → Export

**Key Components:**
- **ElevenLabs Scribe** (primary): Premium accuracy, built-in diarization up to 32 speakers
- **OpenAI Whisper** (fallback): Local processing with optional pyannote diarization
- **Clean UI** (`clean_ui.py`): Minimal 3-stage progress display, reduces 50+ lines to ~10
- **Enhanced Extraction** (`extractors/`): Content-aware analysis with rubric selection
- **MCP Server**: Direct agent access via Model Context Protocol

**Entry Points:**
1. `transcribe.py` - Interactive CLI menu (9 modes)
2. `quick_url_transcribe.py` - Clean UI single-URL processing ⭐
3. `app.py` - Streamlit web interface
4. `mcp_transcription_server.py` - MCP server for AI agents

## Quality Gates (Important)

```bash
# Essential validation
python test_clean_ui.py                                    # UI functionality
python -c "from extractors.contracts import validate_with_repair; print('✅')"  # Contract system
python -c "from extractors.truthful_telemetry import get_global_collector; print('✅')"  # Telemetry

# System health
python -c "import whisper, torch; print(f'Whisper+PyTorch: ✅')"
```

## Environment Setup

```bash
# Required
ELEVENLABS_SCRIBE_KEY=your_api_key_here  # For premium provider
OPENAI_API_KEY=your_openai_key           # For advanced analysis
USE_SCRIBE=true                          # Enable/disable ElevenLabs

# Dependencies
pip install -r requirements.txt
brew install ffmpeg  # macOS
```

## For Deep Dives

- **CLAUDE.detailed.md** - Complete documentation (all original content)
- **docs/ARCHITECTURE.md** - Detailed system design
- **docs/API_RULES.md** - Critical implementation constraints
- **docs/TESTING.md** - Comprehensive testing procedures
- **docs/DEBUGGING.md** - Troubleshooting and diagnostics

---
*This streamlined guide focuses on essential information Claude Code needs for effective development. See referenced files for comprehensive details.*