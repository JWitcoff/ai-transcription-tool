# 🎬 AI Transcription Tool

A powerful, all-in-one audio/video transcription tool powered by ElevenLabs Scribe and OpenAI Whisper with clean architecture, advanced speaker diarization (up to 32 speakers), minimal UI, and multiple export formats.

🏗️ **NEW in v2.0**: Clean architecture with provider pattern, centralized configuration, and modular design for better maintainability and extensibility.

## ✨ Features

- 🤖 **MCP Server**: Direct agent access via Model Context Protocol (NEW!)
- 🎵 **Audio Only Mode**: Download audio from any URL without transcription (NEW!)
- ⏱️ **Clean Terminal UI**: Minimal 3-stage progress with dynamic ETA updates (NEW!)
- 🎙️ **Multiple Input Sources**: YouTube videos, local files, live microphone
- 🎯 **Speaker Diarization**: Automatically identify different speakers
- ⚡ **Live Transcription**: Real-time speech-to-text from microphone
- 📊 **Batch Processing**: Transcribe multiple files at once
- 🤖 **AI Analysis**: Summarization, theme extraction, sentiment analysis
- 🧠 **Custom Analysis Prompts**: Ask specific questions about your content (NEW!)
- 📋 **Professional Templates**: Pre-built analysis for interviews, tutorials, meetings (NEW!)
- 🛡️ **Fact-Grounded Analysis**: Prevents AI hallucinations with extractive summarization (NEW!)
- 📊 **Named Entity Recognition**: Extracts dates, metrics, companies, and quotes with validation (NEW!)
- 🎯 **Blacklist Filtering**: Filters unrealistic terms to prevent false information (NEW!)
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

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate    # macOS/Linux
   # OR on Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the tool**
   ```bash
   python transcribe.py
   ```

> **Note:** Always activate the virtual environment with `source venv/bin/activate` before running the tool. When you're done, you can deactivate it with `deactivate`.

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
2. Watch the **clean progress display** with real-time ETA:
```
🎬 QUICK TRANSCRIPTION
Input: https://youtube.com/watch?v=example123
Using transcription model: ElevenLabs Scribe ✅

[🔊] Transcribing audio... (ETA: 2m 30s)
[🧠] Analyzing transcript... (ETA: 45s)
[✅] Complete – results saved

📝 Summary:
Duration: 5m 32s | Speakers: 2 | Confidence: 94.3%
Saved 6 output files to: /Users/user/transcripts/example
```
3. Get complete transcription + speaker identification + AI analysis
4. Find results in the `transcripts/` folder

**Or via the main menu:**
1. Run `python transcribe.py`
2. Choose option 2 (Quick URL Transcription)
3. Enter your YouTube URL
4. Choose custom analysis prompt or use defaults
5. Watch the clean UI guide you through each step

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

### ⏱️ Progress Tracking (NEW!)
**Real-time visibility into processing:**
- **Dynamic ETA calculations** that improve accuracy as processing continues
- **Step-by-step progress**: Download → Setup → Transcription → Analysis → Save
- **Completion times** for each phase to help you understand performance
- **Audio duration awareness**: Automatically adjusts estimates based on video length

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

## 🛡️ Fact-Grounded Analysis System (NEW!)

**Prevents AI hallucinations and ensures factual accuracy in transcript analysis.**

### 🎯 Problem Solved

Traditional AI analysis can "hallucinate" - creating false information that sounds realistic:
- ❌ **Before**: AI might claim "Apple announced iPhone 17" when transcript actually mentioned "CommaCon 2025"
- ❌ **Before**: Generic themes like "Theme 1: Technology"
- ❌ **Before**: Speculative summaries that invent details not in the transcript

- ✅ **After**: Only real facts extracted and validated against source
- ✅ **After**: Specific themes like "Business Strategy: Revenue (3 data points)"
- ✅ **After**: Extractive summaries using only actual transcript sentences

### 🔍 How It Works

**1. Named Entity Recognition**
- **Dates & Events**: WWDC 2024, June 2024, CommaCon 2025
- **Metrics & Numbers**: $383 billion, 15% growth, 32 speakers
- **Companies**: Apple, Google, Microsoft (with context validation)
- **Quotes**: Memorable statements with speaker attribution

**2. Blacklist Filtering**
Automatically filters unrealistic terms that AI commonly hallucinates:
```
iPhone 17, iPhone 18, Tesla Phone, Vision Pro 2,
ChatGPT 10, Windows 20, etc.
```

**3. Source Validation**
- Every fact must be findable in the original transcript
- Confidence scoring (0-1) for each extracted element
- Evidence counting for theme generation

**4. Extractive Summarization**
- Uses actual sentences from transcript instead of generating new ones
- Prevents AI from inventing information not present in source
- Maintains factual accuracy while providing concise overviews

### 📊 Example: Before vs After

**Input Transcript Excerpt:**
> "At CommaCon 2025, we announced new factory efficiency metrics showing 23% improvement. Apple's revenue reached $383 billion. Google reported 15% cloud growth."

**❌ Old System Output:**
```
Summary: Apple unveiled the revolutionary iPhone 17 with advanced features...
Theme 1: Technology
Theme 2: Innovation
```

**✅ New Fact-Grounded Output:**
```
EXTRACTED FACTS:
• Events: CommaCon 2025
• Metrics: 23% improvement, $383 billion, 15%
• Companies: Apple, Google

EXTRACTIVE SUMMARY:
At CommaCon 2025, we announced new factory efficiency metrics showing 23% improvement. Apple's revenue reached $383 billion.

EVIDENCE-BASED THEMES:
1. Business Metrics: Financial (2 data points)
2. Key Events & Announcements (1 event)
3. Companies & Organizations (2 entities)
```

### 🎯 Confidence & Validation

Each analysis includes:
- **Confidence Score**: Overall reliability (0-100%)
- **Evidence Count**: Number of factual references supporting each theme
- **Source Attribution**: Every claim traceable to transcript content
- **Blacklist Status**: Confirmation that joke terms were filtered out

This ensures users receive accurate, evidence-based insights instead of AI speculation.

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

**Processing Time Estimates (NEW!)** ⏱️
The tool now shows real-time progress with dynamic ETA calculations:

**For a 36-minute video:**
- **ElevenLabs Scribe (Premium)**: 3-7 minutes total
  - Audio Download: 30-60 seconds
  - Transcription: 2-5 minutes (cloud processing)
  - Analysis: 30-60 seconds
- **Local Whisper (Free)**: 18-30 minutes (CPU) / 6-13 minutes (GPU)
  - Audio Download: 30-60 seconds
  - Transcription: 15-25 minutes (CPU) / 3-8 minutes (GPU)
  - Analysis: 2-4 minutes

**Clean UI Features:**
- 🎯 **Minimal 3-Stage Progress**: [🔊] Transcribing → [🧠] Analyzing → [✅] Complete
- ⏱️ **Dynamic ETA Updates**: Real-time countdown (2m 30s → 1m 45s → 30s)
- 🤖 **Model Selection Display**: ElevenLabs Scribe ✅ or Whisper ⚠️ fallback indication
- 🔇 **Silent Processing**: Suppressed verbose model loading and upload logs
- 📊 **Professional Summary**: Duration, speakers, confidence stats in single line
- ✨ **Minimal Output**: Reduced from 50+ verbose lines to ~10 clean lines

## 🏗️ Architecture (v2.0)

**Clean Architecture Benefits:**
- **Provider Pattern**: ElevenLabs and Whisper behind common interface
- **Dependency Injection**: Configurable components with clean interfaces
- **Error Hierarchy**: Standardized error handling across the system
- **Configuration Layer**: Environment-based settings management
- **Modular Design**: Each component has single responsibility

**New Usage (Advanced):**
```python
from transcription import TranscriptionService
from transcription.config import TranscriptionConfig

# Configure from environment
config = TranscriptionConfig.from_env()
service = TranscriptionService()

# Transcribe with automatic provider fallback
result = service.transcribe("audio.wav")
print(f"Transcribed by {result.provider}: {len(result.segments)} segments")
```

**Migration:** Existing CLI tools (`transcribe.py`, `app.py`) work unchanged. Deprecated files moved to `deprecated/` folder.

**Optimization Tips:**
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

## 🤖 MCP Server for AI Agents (NEW!)

Give AI agents direct access to YouTube transcription with the included MCP (Model Context Protocol) server.

### Quick Setup for Claude Desktop

1. **Install MCP package:**
   ```bash
   pip install "mcp[cli]"
   ```

2. **Configure Claude Desktop** - Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "youtube-transcription": {
         "command": "python",
         "args": ["/path/to/AI_Transcription/mcp_transcription_server.py"],
         "env": {
           "ELEVENLABS_SCRIBE_KEY": "your_api_key",
           "OPENAI_API_KEY": "your_openai_key"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** and start chatting:
   - "Download the audio from this YouTube video: https://..."
   - "Transcribe this video and tell me the key points: https://..."

### MCP Tools Available

- **`download_audio_only`** - Extract audio without transcription (MP3/WAV/FLAC)
- **`transcribe_youtube`** - Full transcription with speaker diarization
- **`transcribe_with_custom_prompt`** - Custom analysis questions
- **`get_video_segments`** - Export as SRT/VTT subtitles

See [README_MCP.md](README_MCP.md) for complete MCP documentation.

## License

This project is for educational and research purposes. Please respect the terms of service of video platforms when extracting content.

## Acknowledgments

- [ElevenLabs Scribe](https://elevenlabs.io) for premium transcription and speaker diarization
- [OpenAI Whisper](https://github.com/openai/whisper) for local speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video/audio extraction
- [Streamlit](https://streamlit.io/) for the web interface
- [Transformers](https://huggingface.co/transformers/) for text analysis
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) for local speaker diarization