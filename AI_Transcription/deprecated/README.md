# Deprecated Files

This directory contains files that have been deprecated during architectural refactoring.

## Reason for Deprecation

These files were creating architectural complexity through:
- **Entry Point Proliferation**: Multiple overlapping CLI interfaces
- **Code Duplication**: Similar functionality spread across files
- **Maintenance Overhead**: Multiple files to update for feature changes

## Migration Path

### Deprecated Entry Points (`entry_points/`)

| Deprecated File | Replacement | Migration Notes |
|----------------|-------------|-----------------|
| `quick_url_transcribe_old.py` | `quick_url_transcribe.py` | Old version replaced by clean UI implementation |
| `working_cli.py` | `transcribe.py` (mode selection) | Functionality merged into main CLI |
| `cli_transcribe.py` | `transcribe.py` (mode selection) | Functionality merged into main CLI |
| `fast_transcriber.py` | `audio_transcriber.py` | Consolidated into single transcriber class |
| `hybrid_transcriber.py` | `audio_transcriber.py` | Consolidated into single transcriber class |
| `transcriber.py` | `audio_transcriber.py` | Consolidated into single transcriber class |

### New Architecture

The refactored architecture provides:
- **Single Entry Points**: Clear separation of CLI, web, and MCP interfaces
- **Provider Pattern**: Clean interfaces for ElevenLabs/Whisper
- **Modular Design**: Core transcription package with clean separation
- **Configuration Management**: Centralized config layer

## Recovery Instructions

If you need to restore any deprecated functionality:
1. Check the replacement file for equivalent features
2. If needed, copy specific functions from deprecated files
3. Update imports and dependencies to match new architecture

## Cleanup Schedule

These files will be permanently removed in a future release after:
- [ ] Verification that all functionality is preserved in new architecture
- [ ] Migration of any remaining dependencies
- [ ] User testing of new interface