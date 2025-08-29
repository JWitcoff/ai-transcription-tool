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

# Run enhanced extraction tests (NEW!)
cd tests && python test_enhanced_extraction.py

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

# Test enhanced extraction with explicit rubric
python transcribe.py --rubric prompting_claude_v1

# Validate ElevenLabs API
python -c "from elevenlabs_scribe import ScribeClient; client = ScribeClient(); print('API OK' if client.client else 'API Not Available')"

# Test rubric selection
python -c "from extractors.rubric_selector import RubricSelector; s = RubricSelector(); print(s.get_available_rubrics())"

# Test enhanced extraction directly
python -c "from extractors.enhanced_deep_extractor import extract_with_best_practices; help(extract_with_best_practices)"
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

**Triple-Layer Analysis System:**
- **Enhanced Deep Extraction** (`extractors/enhanced_deep_extractor.py`) - Content-aware extraction with automatic rubric selection
- **OpenAI GPT-4** (`openai_analyzer.py`) - Advanced analysis with fallback to local
- **Local Models** (`analyzer.py`) - BART/RoBERTa models for offline analysis

### Enhanced Extraction System (NEW!)

**Pluggable Rubric Architecture:**
- **Rubric Selector** (`extractors/rubric_selector.py`) - Automatic content-type detection
- **Enhanced Validator** (`extractors/enhanced_validator.py`) - Fragment quality and schema compliance
- **Telemetry Collector** (`extractors/telemetry.py`) - Full provenance tracking

**Available Rubrics:**
- `prompting_claude_v1` - Prompt engineering content (role, guardrails, templates)
- `yt_playbook_v1` - YouTube growth content (frameworks, metrics, case studies)

**Quality Pipeline:**
1. Content detection → Select appropriate rubric
2. Fragment validation → Reject broken text
3. Schema compliance → Ensure structure
4. Round-trip testing → Verify usability
5. Telemetry logging → Track quality metrics

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

## Enhanced Extraction Implementation Details

### Using the Enhanced Extractor

```python
from extractors.enhanced_deep_extractor import EnhancedDeepExtractor

# Initialize with automatic rubric selection
extractor = EnhancedDeepExtractor()

# Or force a specific rubric
extractor = EnhancedDeepExtractor(explicit_rubric="prompting_claude_v1")

# Extract with full pipeline
result = extractor.extract_all_lenses(
    transcript=transcript_text,
    user_prompt="extract key lessons",
    video_title="Prompting 101",
    metadata={"provider": "whisper", "source": "youtube"}
)

# Check quality metrics
print(result["_metadata"]["quality"])
# {'fragment_quality': 0.85, 'schema_compliance': 0.92, 'round_trip_valid': True}
```

### Fragment Validation Rules

The system validates all extracted fragments for quality:

1. **Sentence Boundaries**: Must start with capital/number, end with punctuation
2. **Verb Presence**: Must contain grammatical verbs (not just fragments)
3. **No Speaker Tags**: Rejects "Speaker A:" or timestamp artifacts
4. **Concept Whitelist**: Must contain domain-relevant terminology
5. **Minimum Length**: At least 2 words

### Telemetry Tracking

Every extraction creates detailed telemetry:

```python
from extractors.telemetry import TelemetryCollector

telemetry = TelemetryCollector()

# View session report
report = telemetry.generate_session_report()
print(f"Success rate: {report['summary']['success_rate']}%")
print(f"Fallback rate: {report['summary']['fallback_rate']}%")
```

### Adding New Rubrics

To add a new content type rubric:

1. Create `extractors/[domain]_rubric.json` with schema
2. Add detection patterns to `rubric_selector.py`
3. Create extraction prompts in `extractors/[domain]_prompts.py`
4. Add validation rules to `enhanced_validator.py`

### Testing

Run comprehensive tests:
```bash
cd tests
python test_enhanced_extraction.py -v
```

Test specific components:
```python
# Test rubric selection
from extractors.rubric_selector import RubricSelector
selector = RubricSelector()
result = selector.select_rubric("Set the role upfront...")
print(result.rubric_name)  # "prompting_claude_v1"

# Test fragment validation
from extractors.enhanced_validator import EnhancedValidator
validator = EnhancedValidator("prompting_claude_v1")
quality = validator._validate_fragment_quality("Set temperature=0")
print(quality.quality)  # FragmentQuality.VALID
```