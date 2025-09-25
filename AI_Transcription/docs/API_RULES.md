# Critical API Rules & Implementation Constraints

## ElevenLabs Scribe API Rules

### CRITICAL Rule: diarization_threshold Parameter
```python
# CRITICAL: Only set threshold when diarize=True AND num_speakers=None
if diarize and num_speakers is None and diarization_threshold is not None:
    payload["diarization_threshold"] = diarization_threshold
```

**Why This Matters:**
- ElevenLabs API rejects requests with `diarization_threshold` when `num_speakers` is specified
- This combination will cause a 400 Bad Request error
- Located in: `elevenlabs_scribe.py:142-145`

### File Size Limits
- **File Upload**: 3GB maximum
- **Cloud URL**: 2GB maximum
- Use appropriate method based on file size

### Multi-Channel Audio
- Use `channel_index` parameter to map speakers to audio channels
- Only available with `use_multi_channel=True`
- Useful for interview recordings with separate mic channels

## Provider Fallback Logic

### Automatic Fallback Sequence
```python
if self.diarization_provider == 'elevenlabs':
    # Try ElevenLabs Scribe first
    return self.elevenlabs_scribe.transcribe(...)
else:
    # Fall back to Whisper + optional pyannote
    return self._transcribe_with_whisper(...)
```

**Implementation Location:** `audio_transcriber.py:98-115`

### Environment Variable Control
```bash
USE_SCRIBE=true   # Enable ElevenLabs Scribe (default)
USE_SCRIBE=false  # Force Whisper fallback
```

## Critical Configuration Requirements

### Required Environment Variables
```bash
# Required for ElevenLabs Scribe
ELEVENLABS_SCRIBE_KEY=your_api_key_here

# Optional for advanced analysis
OPENAI_API_KEY=your_openai_key

# Provider control
USE_SCRIBE=true
```

### File Path Handling
- Always use absolute paths for audio files
- Temporary files are marked with `is_temp_file` flag for safe cleanup
- Local files vs downloaded files have different cleanup rules

## Error Handling Patterns

### Silent Fallback Strategy
- ElevenLabs failures silently fall back to Whisper
- No verbose error messages in clean UI mode
- Errors logged but not displayed to user

### Output Suppression
- Use `OutputSuppressor` context manager for silent operations
- Prevents verbose model loading messages
- Maintains clean terminal experience

## Word-to-Segment Processing

### Timestamp Alignment Rules
- Groups consecutive words by speaker
- Configurable gap threshold for segment boundaries
- Maintains precise timestamps for SRT/VTT generation
- **Implementation:** `elevenlabs_scribe.py:222-255`

## Clean UI Integration Rules

### Model Display Logic
```python
if 'scribe' in model_name.lower() or 'elevenlabs' in model_name.lower():
    icon = "✅" if success else "⚠️"
    display_name = "ElevenLabs Scribe"
elif 'whisper' in model_name.lower():
    icon = "⚠️"  # Whisper is fallback
    display_name = "Whisper fallback"
```

### Progress Stage Requirements
- Must use exact stage names: `transcribe`, `analyze`, `complete`
- ETA updates should be realistic (not inflated)
- Single updating line using carriage returns