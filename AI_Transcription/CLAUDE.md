# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Main interactive menu (recommended)
python transcribe.py

# Audio Only Mode (new!)
# - Option 1: Download audio without transcription
# - Choose MP3, WAV, or FLAC format

# Transcription Modes
# - Option 2: Quick URL transcription (direct workflow)
# - Options 3-9: All existing transcription features

# Quick URL transcription (direct workflow)
python quick_url_transcribe.py

# Web interface
streamlit run app.py

# MCP Server for AI Agents (NEW!)
python mcp_transcription_server.py
# Note: Usually managed automatically by Claude Desktop
```

### Testing
```bash
# Run comprehensive ElevenLabs integration tests
cd tests && python test_elevenlabs.py

# Run enhanced extraction tests (NEW!)
cd tests && python test_enhanced_extraction.py

# Run specific test level
cd tests && python -c "from test_elevenlabs import *; test_level_1_connectivity()"

# Test truthful telemetry system
cd tests && python -c "from extractors.truthful_telemetry import TruthfulTelemetryCollector; collector = TruthfulTelemetryCollector(); print('✅ Truthful telemetry test passed')"

# Test contract validation
cd tests && python -c "from extractors.contracts import validate_with_repair; print('✅ Contract system test passed')"

# Test fragment guards
cd tests && python -c "from extractors.guards import filter_valid_fragments; print('✅ Fragment guards test passed')"

# Test MCP server functionality (NEW!)
python test_mcp_functions.py

# Test MCP package installation
python -c "from mcp.server.fastmcp import FastMCP; print('✅ MCP package available')"

# Test MCP server startup (manual testing)
python mcp_transcription_server.py --help
```

### Debugging & Troubleshooting
```bash
# Check system status
python -c "
import sys
print(f'Python version: {sys.version}')
try:
    import torch
    print(f'PyTorch available: {torch.__version__}')
except ImportError:
    print('PyTorch not available')
try:
    from elevenlabs_scribe import ScribeClient
    client = ScribeClient()
    print(f'ElevenLabs Scribe: {"✅ Available" if client.client else "❌ Not configured"}')
except Exception as e:
    print(f'ElevenLabs Scribe: ❌ Error - {e}')
"

# Check truthful telemetry session
python -c "from extractors.truthful_telemetry import get_global_collector; collector = get_global_collector(); report = collector.get_session_report(); print(f'Session: {report[\"session_stats\"][\"session_id\"]}, Extractions: {report[\"session_stats\"][\"total_extractions_attempted\"]}')"

# View recent extraction logs
ls -la truthful_telemetry/truthful_session_*.json | tail -5

# Check contract validation errors
python -c "
from extractors.contracts import ChaptersAdvicePayload
try:
    test_payload = {'chapters': [{'title': 'Test', 'summary': 'A test chapter with sufficient length to meet requirements'}], 'advice': [{'category': 'acquisition', 'point': 'Test advice that is actionable and meets length requirements'}]}
    validated = ChaptersAdvicePayload(**test_payload)
    print('✅ Contract validation working')
except Exception as e:
    print(f'❌ Contract validation error: {e}')
"

# Test fragment quality validation
python -c "
from extractors.guards import comprehensive_fragment_check, GuardResult
test_cases = [
    'This is a complete sentence with proper content.',
    \"'m part of the Applied\",
    'Coverage: 101.0%',
    'Found: 539 frameworks'
]
for test in test_cases:
    result = comprehensive_fragment_check(test)
    print(f'Fragment: \"{test[:30]}...\" → {result.value}')
"
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
# Test audio download only mode
python transcribe.py
# Choose option 1, enter a YouTube URL, select format (MP3/WAV/FLAC)

# Test with sample YouTube URL (transcription)
python quick_url_transcribe.py "https://www.youtube.com/watch?v=6KOxyJlgbyw"

# Test enhanced extraction with explicit rubric
python transcribe.py --rubric prompting_claude_v1

# Validate ElevenLabs API
python -c "from elevenlabs_scribe import ScribeClient; client = ScribeClient(); print('API OK' if client.client else 'API Not Available')"

# Test rubric selection
python -c "from extractors.rubric_selector import RubricSelector; s = RubricSelector(); print(s.get_available_rubrics())"

# Test enhanced extraction directly
python -c "from extractors.enhanced_deep_extractor import extract_with_best_practices; help(extract_with_best_practices)"

# Test contract validation system
python -c "from extractors.contracts import ChaptersAdvicePayload; print('Contract system loaded')"

# Test fragment guards
python -c "from extractors.guards import comprehensive_fragment_check; print(comprehensive_fragment_check('This is a test fragment.'))"

# Test timestamp alignment
python -c "from extractors.align import TimestampAligner; aligner = TimestampAligner(); print('Alignment system ready')"

# Test truthful telemetry
python -c "from extractors.truthful_telemetry import get_global_collector; collector = get_global_collector(); print('Truthful telemetry active')"
```

### Development Workflow & Documentation Tools
```bash
# Smart commit with documentation reminders
./commit-with-docs.sh "Your commit message"

# Regular git workflow (will show doc reminders via pre-commit hook)
git add your_files.py
git commit -m "Your commit message"

# Push current branch
git push origin $(git branch --show-current)

# Create pull request (if gh CLI installed)
gh pr create --title "Your PR title" --body "Description"
```

**Documentation Update Reminders:**
- Pre-commit hook automatically detects significant changes
- Prompts to update CLAUDE.md and README.md when needed
- Smart commit script offers to auto-stage documentation files
- Commit template includes documentation checklist

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

1. **`transcribe.py`** - Interactive CLI menu with 9 transcription modes
2. **`quick_url_transcribe.py`** - Streamlined single-URL processing
3. **`app.py`** - Streamlit web interface with real-time progress
4. **`live_cli.py`** - Real-time microphone transcription
5. **`simple_transcribe.py`** - Advanced CLI with quality tiers
6. **`mcp_transcription_server.py`** - MCP server for AI agents (NEW!)

### MCP Server Architecture (NEW!)

**Model Context Protocol Integration:**
- **FastMCP Server** - Exposes transcription tools to AI agents
- **Audio Download Tool** - `download_audio_only()` matches CLI Option 1
- **Transcription Tools** - Full transcription with custom analysis prompts
- **Resource Endpoints** - Access past sessions and files
- **Session Management** - Integrates with existing `downloads/` and `transcripts/` folders
- **Automatic Provider Selection** - Uses ElevenLabs → Whisper fallback like other entry points

### Analysis Engine

**Triple-Layer Analysis System:**
- **Enhanced Deep Extraction** (`extractors/enhanced_deep_extractor.py`) - Content-aware extraction with automatic rubric selection
- **OpenAI GPT-4** (`openai_analyzer.py`) - Advanced analysis with fallback to local
- **Local Models** (`analyzer.py`) - BART/RoBERTa models for offline analysis

### Enhanced Extraction System (NEW!)

**Pluggable Rubric Architecture:**
- **Rubric Selector** (`extractors/rubric_selector.py`) - Automatic content-type detection
- **Enhanced Validator** (`extractors/enhanced_validator.py`) - Fragment quality and schema compliance
- **Contract System** (`extractors/contracts.py`) - Pydantic-based output validation
- **Fragment Guards** (`extractors/guards.py`) - Smart guards against rubric leakage
- **Timestamp Alignment** (`extractors/align.py`) - Order-preserving fuzzy matching for SRT/VTT
- **Truthful Telemetry** (`extractors/truthful_telemetry.py`) - Verifiable metrics without fake data
- **Legacy Telemetry** (`extractors/telemetry.py`) - Full provenance tracking

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

### Truthful Telemetry System (NEW!)

The system now uses **truthful, verifiable metrics** instead of fake coverage percentages:

**Before (Fake):**
```
Coverage: 101.0% of key elements extracted
Found: 539 frameworks, 2 metrics
```

**After (Truthful):**
```
Content: 3 frameworks, 2 metrics, 1 case studies
Key Concepts: CCN fit, 7/15/30
Method: openai_gpt4
```

**Using Truthful Telemetry:**
```python
from extractors.truthful_telemetry import get_global_collector, finalize_session

# Get session statistics
collector = get_global_collector()
report = collector.get_session_report()
print(f"Success rate: {report['session_stats']['success_rate']:.1%}")
print(f"Contract compliance: {report['session_stats']['contract_compliance_rate']:.1%}")

# Finalize session (prints summary and saves report)
finalize_session()
```

**Key Benefits:**
- ✅ Only counts actual extracted items (no inflation)
- ✅ Boolean quality indicators instead of fake percentages  
- ✅ Honest error reporting with specific issues
- ✅ Verifiable processing metadata (provider, method, timing)
- ✅ Session-level statistics for quality monitoring

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

# Test contract validation
from extractors.contracts import validate_with_repair
payload = {"chapters": [...], "advice": [...]}
validated = validate_with_repair(payload, "extract business advice")
print(validated.provenance)  # "contract_based"

# Test truthful telemetry
from extractors.truthful_telemetry import TruthfulTelemetryCollector
collector = TruthfulTelemetryCollector()
metrics = collector.record_extraction_attempt(
    extraction_result={"chapters": [{"title": "Test", "summary": "A test chapter"}]},
    transcript_metadata={"provider": "whisper", "text": "sample transcript"},
    processing_metadata={"method": "openai_gpt4", "duration_ms": 1500}
)
print(f"Items extracted: {metrics.total_items_extracted}")
```

### Quality Monitoring & Session Management

**Monitor extraction quality in real-time:**
```bash
# View current session status
python -c "
from extractors.truthful_telemetry import get_global_collector
collector = get_global_collector()
stats = collector.session_stats
print(f'📊 Session {stats.session_id}')
print(f'   Extractions: {stats.total_extractions_successful}/{stats.total_extractions_attempted}')
print(f'   Success rate: {stats.success_rate:.1%}')
print(f'   Contract compliance: {stats.contract_compliance_rate:.1%}')
print(f'   Providers: Scribe({stats.elevenlabs_scribe_used}) Whisper({stats.whisper_used})')
"

# Finalize session and generate report
python -c "from extractors.truthful_telemetry import finalize_session; finalize_session()"

# View session reports
ls -la truthful_telemetry/truthful_session_*.json
```

**Quality Gates & Validation:**
```bash
# Test contract enforcement
python -c "
from extractors.contracts import validate_with_repair
# This should pass
good_payload = {
    'chapters': [{'title': 'Valid Chapter', 'summary': 'This is a proper chapter summary with sufficient detail and length.'}],
    'advice': [{'category': 'monetization', 'point': 'This is actionable advice that meets the length requirements.'}]
}
try:
    result = validate_with_repair(good_payload)
    print('✅ Contract validation: PASS')
except Exception as e:
    print(f'❌ Contract validation: FAIL - {e}')
"

# Test rubric leakage detection
python -c "
from extractors.guards import has_rubric_leakage
test_cases = [
    'This is clean content without artifacts.',
    '## 🔧 CORE FRAMEWORKS',
    'Coverage: 101.0% of key elements',
    'Found: 539 frameworks, 2 metrics'
]
for test in test_cases:
    leaked = has_rubric_leakage(test)
    status = '❌ LEAKED' if leaked else '✅ CLEAN'
    print(f'{status}: \"{test[:40]}...\"')
"
```

**Performance & Error Tracking:**
```bash
# Check processing performance
python -c "
import time
from extractors.truthful_telemetry import TruthfulTelemetryCollector
collector = TruthfulTelemetryCollector()
start_time = time.time()
# Simulate extraction metrics
metrics = collector.record_extraction_attempt(
    extraction_result={'chapters': [{'title': 'Test', 'summary': 'Test summary with adequate length'}]},
    transcript_metadata={'provider': 'whisper', 'text': 'sample transcript'},
    processing_metadata={'method': 'test', 'duration_ms': (time.time() - start_time) * 1000}
)
print(f'✅ Processing time: {metrics.processing_time_ms:.0f}ms')
"

# Monitor extraction errors
tail -f video_transcription.log | grep -E "(ERROR|WARNING|Failed)"

# Check system health
python -c "
import psutil
import os
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk space: {psutil.disk_usage(os.getcwd()).percent}%')
"
```