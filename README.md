# 🎬 AI Transcription Tool

A powerful, all-in-one audio/video transcription tool powered by ElevenLabs Scribe and OpenAI Whisper with advanced speaker diarization (up to 32 speakers), live transcription, and multiple export formats.

## ✨ Features

- 🎵 **Audio Only Mode**: Download audio from any URL without transcription (NEW!)
- 🎙️ **Multiple Input Sources**: YouTube videos, local files, live microphone
- 🎯 **Speaker Diarization**: Automatically identify different speakers
- ⚡ **Live Transcription**: Real-time speech-to-text from microphone
- 📊 **Batch Processing**: Transcribe multiple files at once
- 🤖 **AI Analysis**: Summarization, theme extraction, sentiment analysis
- 🧠 **Custom Analysis Prompts**: Ask specific questions about your content (NEW!)
- 📋 **Professional Templates**: Pre-built analysis for interviews, tutorials, meetings (NEW!)
- 📂 **Smart File Organization**: Organized session folders with metadata (NEW!)
- 📥 **Multiple Export Formats**: TXT, SRT subtitles, VTT captions, JSON, Markdown
- 🌐 **Web Interface**: Beautiful Streamlit app with download buttons
- 🚀 **Multiple Quality Modes**: From fast to ultra-accurate

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - Required for audio processing
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/JWitcoff/ai-transcription-tool.git
   cd ai-transcription-tool/AI_Transcription
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the tool**
   ```bash
   python transcribe.py
   ```

That's it! The interactive menu will guide you through all options.

## 🚀 Quick Start

### One Command to Rule Them All
```bash
python transcribe.py
```

This opens an interactive menu with all modes:

**🎵 Audio Only Modes:**
1. **🎵 Audio Download Only** - Download audio without transcription (MP3/WAV/FLAC)

**🎬 Transcription Modes:**
2. **🎯 Quick URL Transcription** ⭐ RECOMMENDED - Enter any video URL → Get complete analysis
3. **📁 Advanced File/URL Options** - Manual quality selection and batch processing  
4. **🎙️ Live Transcription** - Real-time from your microphone
5. **🌐 Web Interface** - Browser-based with downloads
6. **📊 Batch Processing** - Multiple files at once
7. **📋 Template Analysis** - Professional structured output
8. **🗂️ Session Management** - View and organize past transcriptions
9. **⚙️ Settings & Help** - Configure and learn

## 📖 Detailed Usage

### Example: Audio Download Only (NEW!) 🎵

**Fast audio extraction without transcription:**
```bash
python transcribe.py
```
1. Choose option 1 (Audio Download Only)
2. Enter your video URL (YouTube, Twitch, etc.)
3. Select format: MP3 (compressed), WAV (uncompressed), or FLAC (lossless)
4. Audio downloads to `downloads/` folder with metadata

**Perfect for:**
- Building audio libraries for later processing
- Getting high-quality audio files quickly
- Podcast episode downloads
- Music/interview extraction

### Example: Quick YouTube Video Transcription ⭐ RECOMMENDED

**The fastest workflow:**
```bash
python quick_url_transcribe.py
```
1. Enter your YouTube URL
2. Get complete transcription + speaker identification + AI analysis
3. Find results in the `transcripts/` folder

**Or via the main menu:**
1. Run `python transcribe.py`  
2. Choose option 2 (Quick URL Transcription)
3. Enter your YouTube URL  
4. Choose custom analysis prompt or use defaults

### Example: Live Transcription

1. Run `python transcribe.py`
2. Choose option 4 (Live Transcription)
3. Start speaking into your microphone
4. Press Ctrl+C to stop
5. Save the transcript when prompted

### Speaker Diarization (Who Said What?)

**Quick URL Transcription automatically includes speaker diarization** when ElevenLabs Scribe is available. Manual advanced options 3, 4, and 5 also support speaker identification:

```
Speaker A:
Hello, welcome to our podcast.

Speaker B:
Thanks for having me! I'm excited to be here.

Speaker A:
Let's dive into today's topic...
```

## 📊 Output Formats

All transcripts are automatically saved to the `transcripts/` folder in multiple formats:

- **TXT**: Clean, human-readable text with speaker labels
- **JSON**: Complete data with timestamps, metadata, and segments  
- **SRT**: SubRip subtitle files for video editors
- **VTT**: WebVTT captions for web players and browsers
- **Segments JSON**: Structured segment data with speaker mapping

**Example output files:**
```
transcripts/transcript_20240126_143052.txt      # Main transcript
transcripts/transcript_20240126_143052.json     # Raw data  
transcripts/transcript_20240126_143052.srt      # Subtitles
transcripts/transcript_20240126_143052.vtt      # Web captions
transcripts/transcript_20240126_143052_segments.json  # Segment data
```

### Supported Platforms

The tool supports audio extraction from:
- YouTube (including live streams)
- Local audio/video files (MP3, WAV, MP4, etc.)
- Live microphone input
- And many more via yt-dlp

## 🎯 How Transcription Works

The AI Transcription Tool uses an intelligent **automatic provider selection** system:

### 🚀 Quick URL Transcription (Recommended Workflow) ⭐

**Default behavior when you run `python quick_url_transcribe.py` or choose Option 1 from menu:**

1. **🏆 Tries ElevenLabs Scribe first** (if API key configured)
   - 96.7% accuracy with built-in speaker diarization (up to 32 speakers)
   - Cloud processing, fast results  
   - Audio event detection
   - Cost: ~$0.40/hour of audio

2. **🔄 Falls back to Whisper automatically** (if Scribe unavailable)
   - Whisper base model (74MB) for good speed/accuracy balance
   - Local processing, completely free
   - ~90-93% accuracy, no speaker identification

**Result:** You get the best available transcription automatically with zero configuration needed.

---

### ⚙️ Advanced Manual Options (For Power Users)

**Only available via `python transcribe.py` → Option 3 (Advanced File/URL Options):**

| Option | Tech Stack | Accuracy | Speakers | Cost | Best For |
|--------|------------|----------|----------|------|----------|
| 1. Fast | Whisper tiny (39MB) | ~85-90% | 0 | Free | Quick tests |
| 2. Balanced | Whisper base (74MB) | ~90-93% | 0 | Free | Daily use |
| 3. Accurate | Whisper base + pyannote | ~94% | 2-8 | Free* | Meetings |
| 4. Best | Whisper large + pyannote | ~95-96% | 2-8 | Free* | Research |
| 5. Premium | ElevenLabs Scribe | ~96.7% | 32 | Paid | Professional |

*Requires HuggingFace token for pyannote diarization

### 💡 Which Should I Use?

- **🎯 For 99% of users:** Just use Quick URL Transcription (`python quick_url_transcribe.py`)
- **⚙️ For specific quality needs:** Use Advanced Options to manually select models

## 🧠 Custom Analysis & Templates (NEW!)

Ask specific questions about your content instead of generic summaries:

### Custom Analysis Prompts
```bash
python quick_url_transcribe.py
# Enter URL, then specify what you want to learn:
# "Extract all YouTube growth tips"
# "List the main arguments and evidence" 
# "What are the action items mentioned?"
```

### Professional Templates
Pre-built analysis templates for common use cases:
- **📋 Interview Analysis**: Extract key insights, quotes, themes
- **🎓 Tutorial Breakdown**: Learning objectives, steps, examples  
- **🤝 Meeting Notes**: Action items, decisions, follow-ups
- **📊 Business Content**: Frameworks, metrics, case studies

Access via menu option 7 (Template Analysis).

## ⚙️ Configuration

### API Keys Configuration

Create a `.env` file in the project directory:

```bash
# For AI analysis features (optional)
OPENAI_API_KEY=your_openai_api_key_here

# For ElevenLabs Scribe - Premium transcription with speaker diarization
ELEVENLABS_SCRIBE_KEY=your_elevenlabs_api_key_here
```

**API Key Setup:**

**ElevenLabs Scribe (for premium transcription):**
1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Go to your [API Keys page](https://elevenlabs.io/app/settings/api-keys)
3. Create a new API key
4. Add it to your `.env` file as `ELEVENLABS_SCRIBE_KEY`

**OpenAI (optional - for analysis features):**
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys section
3. Create a new secret key
4. Add it to your `.env` file as `OPENAI_API_KEY`

**Without API keys:** All local Whisper options work perfectly for transcription and basic analysis. Quick URL workflow will automatically fall back to Whisper.

## 🔧 Troubleshooting

### Common Issues

1. **"FFmpeg not found"**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   ```

2. **"pyannote.audio not available" (Only affects advanced manual options 3-4)**
   - pyannote.audio should install automatically with `pip install -r requirements.txt`
   - If missing: `pip install pyannote.audio>=3.1.0`
   - Quick URL transcription uses ElevenLabs Scribe instead

3. **First run is slow**
   - This is normal! Whisper models are downloaded (~1-2GB)
   - Subsequent runs are much faster

4. **Memory issues**
   - Use smaller models (tiny/base) for less RAM usage
   - Process shorter audio segments

### GPU Acceleration

For faster transcription, ensure you have:
- NVIDIA GPU with CUDA support
- PyTorch with CUDA enabled
- Set `ENABLE_GPU=true` in configuration

## File Formats

### Input Formats
- **Video**: MP4, AVI, MOV, MKV, WebM
- **Audio**: WAV, MP3, M4A, FLAC, OGG
- **Streams**: Any URL supported by yt-dlp

### Output Formats
- **TXT**: Plain text transcript with speaker labels
- **JSON**: Complete transcription data with timestamps and metadata
- **SRT**: SubRip subtitle files for video editors  
- **VTT**: WebVTT captions for web players and browsers
- **Segments JSON**: Structured segment data with speaker mapping

## API Usage

You can also use the components programmatically:

```python
from audio_transcriber import AudioTranscriber
from analyzer import TextAnalyzer
from openai_analyzer import OpenAIAnalyzer
import yt_dlp
import tempfile

# Download audio from YouTube
def download_audio(url):
    temp_audio = tempfile.mktemp(suffix='.wav')
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return temp_audio

# Transcribe with ElevenLabs Scribe (premium)
transcriber = AudioTranscriber(
    model_size='base',
    enable_diarization=True,
    diarization_provider='elevenlabs'  # or 'pyannote' or 'auto'
)

audio_file = download_audio("https://youtube.com/watch?v=example")
result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)

# Analyze with OpenAI (with local fallback)
analyzer = OpenAIAnalyzer()  # Falls back to TextAnalyzer if no API key
summary = analyzer.summarize(result["text"])
themes = analyzer.extract_themes(result["text"])
sentiment = analyzer.analyze_sentiment(result["text"])
```

## Performance Tips

1. **Model Selection**: Use smaller models for faster processing
2. **GPU Usage**: Enable GPU acceleration for large models
3. **Duration Limits**: Longer audio takes more time and memory
4. **Internet Speed**: Fast connection improves stream capture
5. **Storage**: Ensure sufficient disk space for temporary files

### Additional Help

1. Check the logs in `video_transcription.log`
2. Verify all dependencies are installed
3. Test with shorter audio clips first
4. Check system requirements

5. **Out of memory errors**
   - Use smaller Whisper models (tiny/base) in advanced options
   - Process shorter audio segments
   - Close other applications

6. **Slow transcription**
   - Quick URL workflow uses cloud processing (faster)
   - For local: Enable GPU acceleration if available
   - Use smaller models for testing

7. **Audio capture fails**
   - Check internet connection
   - Verify URL is accessible
   - Some streams may be region-locked

## System Requirements

### Minimum
- Python 3.8+
- 4GB RAM
- 2GB free disk space
- Internet connection

### Recommended
- Python 3.9+
- 8GB+ RAM
- NVIDIA GPU with 4GB+ VRAM
- SSD storage
- Fast internet connection

## License

This project is for educational and research purposes. Please respect the terms of service of video platforms when extracting content.

## Acknowledgments

- [ElevenLabs Scribe](https://elevenlabs.io) for premium transcription and speaker diarization
- [OpenAI Whisper](https://github.com/openai/whisper) for local speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video/audio extraction
- [Streamlit](https://streamlit.io/) for the web interface
- [Transformers](https://huggingface.co/transformers/) for text analysis
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) for local speaker diarization