# CLAUDE.md - Core Project Guide

This file provides essential guidance to Claude Code when working with this AI transcription system.

## Quick Start Commands (Essential)

```bash
# Primary entry points
python transcribe.py           # Interactive menu (9 modes)
python quick_url_transcribe.py # Clean UI single-URL processing

# Testing
python test_clean_ui.py                                    # Test clean UI
python test_new_architecture.py                            # Test new architecture (NEW!)
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

**🏗️ NEW CLEAN ARCHITECTURE (v2.0):** Refactored with provider pattern and modular design

**Primary Pipeline:** Audio Source → TranscriptionService → Provider (ElevenLabs/Whisper) → Analysis → Export

**Core Package Structure:**
- **`transcription/`** - Main package with clean interfaces
- **`transcription/providers/`** - ElevenLabs & Whisper with abstract base class
- **`transcription/config/`** - Centralized configuration management
- **`transcription/errors/`** - Standardized error hierarchy
- **`transcription/ui/`** - Clean UI components
- **`transcription/core/`** - TranscriptionService with automatic fallback

**Entry Points:**
1. `transcribe.py` - Interactive CLI menu (9 modes) - **UNCHANGED**
2. `quick_url_transcribe.py` - Clean UI single-URL processing ⭐ - **UNCHANGED**
3. `app.py` - Streamlit web interface - **UNCHANGED**
4. `mcp_transcription_server.py` - MCP server for AI agents - **UNCHANGED**

**Deprecated Files:** Moved to `deprecated/` folder with migration guide

## Quality Gates (Important)

```bash
# Essential validation
python test_new_architecture.py                            # New architecture (6 tests)
python test_clean_ui.py                                    # UI functionality
python -c "from transcription import TranscriptionService; print('✅ Architecture OK')"

# System health
python -c "import whisper, torch; print(f'Whisper+PyTorch: ✅')"
python -c "from transcription.providers import ElevenLabsProvider; print('✅ ElevenLabs' if ElevenLabsProvider().is_available() else '❌ No API key')"
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