# Debugging & Troubleshooting Procedures

## Quick Diagnostics

### System Health Check
```bash
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

### Dependency Verification
```bash
# Check if required dependencies are installed
pip show openai-whisper streamlit yt-dlp

# Verify FFmpeg installation
ffmpeg -version

# Test import of critical modules
python -c "
try:
    from elevenlabs_scribe import ScribeClient
    print('✅ ElevenLabs Scribe module imported')
except Exception as e:
    print(f'❌ ElevenLabs Scribe import failed: {e}')

try:
    import whisper
    print('✅ Whisper module imported')
except Exception as e:
    print(f'❌ Whisper import failed: {e}')

try:
    from clean_ui import CleanUI
    print('✅ Clean UI module imported')
except Exception as e:
    print(f'❌ Clean UI import failed: {e}')
"
```

## Common Issues & Solutions

### ElevenLabs API Issues

**Problem: 400 Bad Request with diarization_threshold**
```bash
# Check API rule compliance
python -c "
from elevenlabs_scribe import ScribeClient
client = ScribeClient()
# This should NOT be done:
# payload['diarization_threshold'] = 0.5 when num_speakers is set
print('Remember: diarization_threshold only when diarize=True AND num_speakers=None')
"
```

**Solution:** Verify the critical API rule in `elevenlabs_scribe.py:142-145`

**Problem: File Size Exceeded**
- File uploads: 3GB limit
- Cloud URLs: 2GB limit
- Use appropriate method based on file size

### Model Loading Issues

**Problem: Whisper model download fails**
```bash
# Check available disk space
df -h .

# Test model loading manually
python -c "
import whisper
try:
    model = whisper.load_model('base')
    print('✅ Whisper model loaded successfully')
except Exception as e:
    print(f'❌ Whisper model loading failed: {e}')
"
```

**Problem: pyannote.audio not available**
```bash
# Install pyannote for local diarization
pip install pyannote.audio>=3.1.0

# Test diarization availability
python -c "
try:
    from pyannote.audio import Pipeline
    print('✅ pyannote.audio available')
except ImportError:
    print('❌ pyannote.audio not installed')
"
```

### Clean UI Issues

**Problem: Unicode errors in terminal output**
```bash
# Test terminal encoding
python -c "
import sys
print(f'Terminal encoding: {sys.stdout.encoding}')
print('Testing Unicode: 🔊 🧠 ✅')
"
```

**Problem: Progress bar not updating**
```bash
# Test clean UI functionality
python test_clean_ui.py

# Check if carriage returns work
python -c "
import time
for i in range(5):
    print(f'\rTesting progress: {i}/4', end='', flush=True)
    time.sleep(1)
print('\n✅ Progress test complete')
"
```

### File Processing Issues

**Problem: FFmpeg not found**
```bash
# Install FFmpeg
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# Test FFmpeg availability
ffmpeg -version
```

**Problem: Audio extraction fails**
```bash
# Test audio extraction manually
ffmpeg -i "test_video.mp4" -vn -acodec pcm_s16le -ar 16000 -ac 1 "test_audio.wav"

# Check file permissions
ls -la /path/to/audio/file
```

## Advanced Debugging

### Logging and Tracing

**Enable Verbose Logging:**
```bash
# Set environment variable for detailed logs
export CLAUDE_DEBUG=1

# Run with Python verbose mode
python -v quick_url_transcribe.py
```

**Check Log Files:**
```bash
# View recent extraction logs
ls -la truthful_telemetry/truthful_session_*.json | tail -5

# Monitor real-time logs
tail -f video_transcription.log
```

### Memory and Performance Issues

**Memory Usage Monitoring:**
```bash
# Check current memory usage
python -c "
import psutil
import os
memory = psutil.virtual_memory()
print(f'Total: {memory.total / 1e9:.1f}GB')
print(f'Available: {memory.available / 1e9:.1f}GB')
print(f'Used: {memory.percent}%')
"
```

**Large File Handling:**
- For files > 1GB, consider using smaller Whisper models (tiny, base)
- Monitor memory during processing
- Use GPU acceleration if available

### Network Issues

**YouTube Download Problems:**
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Test URL accessibility
python -c "
import yt_dlp
ydl_opts = {'quiet': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    try:
        info = ydl.extract_info('https://youtube.com/watch?v=TEST_URL', download=False)
        print(f'✅ URL accessible: {info.get(\"title\", \"Unknown\")}')
    except Exception as e:
        print(f'❌ URL access failed: {e}')
"
```

**API Connectivity Issues:**
```bash
# Test ElevenLabs API connectivity
python -c "
import requests
import os
api_key = os.getenv('ELEVENLABS_SCRIBE_KEY')
if not api_key:
    print('❌ ELEVENLABS_SCRIBE_KEY not set')
else:
    print(f'✅ API key configured: {api_key[:10]}...')
    # Test API endpoint (without actual request)
    print('Test connectivity with: curl -H \"Authorization: Bearer <key>\" <endpoint>')
"
```

## Session Recovery

### Recovering from Crashes

**Find Incomplete Sessions:**
```bash
# List recent session directories
ls -lat transcripts/ | head -10

# Check for incomplete sessions (missing analysis files)
find transcripts/ -name "transcript.txt" ! -exec test -f {}/analysis.txt \; -print
```

**Resume Processing:**
```bash
# Re-run analysis on existing transcript
python -c "
from openai_analyzer import OpenAIAnalyzer
with open('transcripts/SESSION_DIR/transcript.txt', 'r') as f:
    transcript = f.read()
analyzer = OpenAIAnalyzer()
summary = analyzer.summarize(transcript)
print('Analysis completed')
"
```

### Cleanup Procedures

**Remove Temporary Files:**
```bash
# Clean up temp audio files
find /tmp -name "transcribe_audio_*" -mtime +1 -delete

# Clean up old session logs
find truthful_telemetry/ -name "truthful_session_*.json" -mtime +30 -delete
```

**Reset Configuration:**
```bash
# Backup current config
cp .env .env.backup

# Reset to defaults
cp .env.example .env

# Verify clean startup
python -c "print('Testing clean startup...'); from clean_ui import CleanUI; ui = CleanUI(); print('✅ Clean startup successful')"
```

## Performance Optimization

### GPU Acceleration
```bash
# Check GPU availability
python -c "
import torch
if torch.cuda.is_available():
    print(f'✅ CUDA available: {torch.cuda.get_device_name()}')
    print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
else:
    print('❌ CUDA not available')
"
```

### Model Optimization
```bash
# Use smaller models for faster processing
python quick_url_transcribe.py
# Set model_size='tiny' for speed, 'large' for accuracy

# Test different model sizes
python -c "
import whisper
for size in ['tiny', 'base', 'small']:
    try:
        model = whisper.load_model(size)
        print(f'✅ {size} model: {model.dims.n_mels} mel bins')
    except Exception as e:
        print(f'❌ {size} model failed: {e}')
"
```