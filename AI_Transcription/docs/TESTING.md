# Comprehensive Testing Procedures

## Core System Testing

### Quick Health Checks
```bash
# Test clean UI implementation
python test_clean_ui.py

# Test ElevenLabs connectivity
python -c "from elevenlabs_scribe import ScribeClient; client = ScribeClient(); print('API OK' if client.client else 'API Not Available')"

# Test system status
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
```

### ElevenLabs Integration Testing

**4-Level Health Check System** (`tests/test_elevenlabs.py`):

```bash
# Run comprehensive ElevenLabs integration tests
cd tests && python test_elevenlabs.py

# Run specific test level
cd tests && python -c "from test_elevenlabs import *; test_level_1_connectivity()"
```

**Test Levels:**
- **Level 1**: API connectivity and validation
- **Level 2**: Basic transcription without diarization
- **Level 3A**: Speaker diarization with threshold testing
- **Level 3B**: Multi-channel audio processing
- **Level 4**: End-to-end YouTube pipeline validation

### Enhanced Extraction Testing

```bash
# Run enhanced extraction tests
cd tests && python test_enhanced_extraction.py

# Test rubric selection
python -c "from extractors.rubric_selector import RubricSelector; s = RubricSelector(); print(s.get_available_rubrics())"

# Test fragment validation
python -c "
from extractors.enhanced_validator import EnhancedValidator
validator = EnhancedValidator('prompting_claude_v1')
quality = validator._validate_fragment_quality('Set temperature=0')
print(quality.quality)  # FragmentQuality.VALID
"

# Test contract validation
python -c "from extractors.contracts import validate_with_repair
payload = {'chapters': [...], 'advice': [...]}
validated = validate_with_repair(payload, 'extract business advice')
print(validated.provenance)  # 'contract_based'
"
```

### Truthful Telemetry Testing

```bash
# Test truthful telemetry system
python -c "from extractors.truthful_telemetry import TruthfulTelemetryCollector; collector = TruthfulTelemetryCollector(); print('✅ Truthful telemetry test passed')"

# View session report
python -c "
from extractors.truthful_telemetry import get_global_collector
collector = get_global_collector()
report = collector.get_session_report()
print(f'Session: {report[\"session_stats\"][\"session_id\"]}, Extractions: {report[\"session_stats\"][\"total_extractions_attempted\"]}')
"

# Check recent extraction logs
ls -la truthful_telemetry/truthful_session_*.json | tail -5
```

### MCP Server Testing

```bash
# Test MCP server functionality
python test_mcp_functions.py

# Test MCP package installation
python -c "from mcp.server.fastmcp import FastMCP; print('✅ MCP package available')"

# Test MCP server startup (manual testing)
python mcp_transcription_server.py --help
```

## Component Testing

### Contract System Testing
```bash
# Test contract validation errors
python -c "
from extractors.contracts import ChaptersAdvicePayload
try:
    test_payload = {'chapters': [{'title': 'Test', 'summary': 'A test chapter with sufficient length to meet requirements'}], 'advice': [{'category': 'acquisition', 'point': 'Test advice that is actionable and meets length requirements'}]}
    validated = ChaptersAdvicePayload(**test_payload)
    print('✅ Contract validation working')
except Exception as e:
    print(f'❌ Contract validation error: {e}')
"
```

### Fragment Quality Testing
```bash
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

### Session Management Testing

```bash
# Monitor extraction quality in real-time
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

## Quality Gates & Validation

### Contract Enforcement Testing
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
```

### Rubric Leakage Detection
```bash
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

## Performance & Error Tracking

### Processing Performance Testing
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
```

### Error Monitoring
```bash
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

## Development Testing

### Sample Usage Testing
```bash
# Test audio download only mode
python transcribe.py
# Choose option 1, enter a YouTube URL, select format (MP3/WAV/FLAC)

# Test with sample YouTube URL (transcription)
python quick_url_transcribe.py "https://www.youtube.com/watch?v=6KOxyJlgbyw"

# Test enhanced extraction with explicit rubric
python transcribe.py --rubric prompting_claude_v1
```

### Direct Component Testing
```bash
# Test enhanced extraction directly
python -c "from extractors.enhanced_deep_extractor import extract_with_best_practices; help(extract_with_best_practices)"

# Test timestamp alignment
python -c "from extractors.align import TimestampAligner; aligner = TimestampAligner(); print('Alignment system ready')"

# Validate ElevenLabs API
python -c "from elevenlabs_scribe import ScribeClient; client = ScribeClient(); print('API OK' if client.client else 'API Not Available')"
```