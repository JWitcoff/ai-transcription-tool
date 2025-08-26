# 🎬 AI Transcription Tool

A powerful, all-in-one audio/video transcription tool powered by ElevenLabs Scribe and OpenAI Whisper with advanced speaker diarization (up to 32 speakers), live transcription, and multiple export formats.

## ✨ Features

- 🎙️ **Multiple Input Sources**: YouTube videos, local files, live microphone
- 🎯 **Speaker Diarization**: Automatically identify different speakers
- ⚡ **Live Transcription**: Real-time speech-to-text from microphone
- 📊 **Batch Processing**: Transcribe multiple files at once
- 🤖 **AI Analysis**: Summarization, theme extraction, sentiment analysis
- 📥 **Smart Downloads**: Export as TXT, SRT subtitles, or JSON
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

This opens an interactive menu with all transcription modes:

1. **🎯 Quick URL Transcription** ⭐ RECOMMENDED - Enter any video URL → Get complete analysis
2. **📁 Advanced File/URL Options** - Manual quality selection and batch processing  
3. **🎙️ Live Transcription** - Real-time from your microphone
4. **🌐 Web Interface** - Browser-based with downloads
5. **📊 Batch Processing** - Multiple files at once
6. **⚙️ Settings & Help** - Configure and learn

## 📖 Detailed Usage

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
2. Choose option 1 (Quick URL Transcription)
3. Enter your YouTube URL
4. Complete analysis is generated automatically

### Example: Live Transcription

1. Run `python transcribe.py`
2. Choose option 3 (Live Transcription)
3. Start speaking into your microphone
4. Press Ctrl+C to stop
5. Save the transcript when prompted

### Speaker Diarization (Who Said What?)

When enabled (options 3, 4, or 5), the tool identifies different speakers:

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

## 🎯 Transcription Options

Choose the best option for your needs:

### Option 1: Fast (Tiny Model)
**Tech Stack:** OpenAI Whisper tiny (39MB) • Local processing • No diarization  
**Best For:** Quick testing, demos, resource-constrained environments  
**Performance:** ~3x real-time • ~85-90% accuracy • No speaker identification  
**Cost:** Free

### Option 2: Balanced (Base Model) ⭐ Recommended
**Tech Stack:** OpenAI Whisper base (74MB) • Local processing • No diarization  
**Best For:** General transcription, daily use, good speed/accuracy balance  
**Performance:** ~1.5x real-time • ~90-93% accuracy • No speaker identification  
**Cost:** Free

### Option 3: Accurate (Base + pyannote)
**Tech Stack:** Whisper base + pyannote.audio diarization • HuggingFace token required  
**Best For:** Meetings, interviews, podcasts with 2-8 speakers  
**Performance:** ~0.5x real-time • ~94% accuracy • Speaker identification  
**Cost:** Free (requires HuggingFace account)

### Option 4: Best (Large + pyannote)
**Tech Stack:** Whisper large (1.55GB) + pyannote.audio • Heavy processing  
**Best For:** Critical transcriptions, research, legal documents  
**Performance:** ~0.2x real-time • ~95-96% accuracy • Speaker identification  
**Cost:** Free (requires significant RAM/storage)

### Option 5: Premium (ElevenLabs Scribe) 🎆
**Tech Stack:** ElevenLabs API • Cloud processing • Integrated transcription + diarization  
**Best For:** Professional use, large meetings (up to 32 speakers), commercial projects  
**Performance:** 3x faster • 96.7% accuracy • Up to 32 speakers • Audio event detection  
**Cost:** $0.40/hour of audio

### 📊 Quick Comparison

| Option | Speed | Accuracy | Speakers | Cost | Setup Complexity |
|--------|-------|----------|----------|------|------------------|
| 1. Fast | ⚡⚡⚡ | ⭐⭐ | 0 | Free | ✅ Simple |
| 2. Balanced | ⚡⚡ | ⭐⭐⭐ | 0 | Free | ✅ Simple |
| 3. Accurate | ⚡ | ⭐⭐⭐⭐ | 2-8 | Free | 🔑 HF Token |
| 4. Best | 🐌 | ⭐⭐⭐⭐⭐ | 2-8 | Free | 🔑 HF Token + RAM |
| 5. Premium | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 32 | Paid | 🔑 API Key |

### 🎯 Which Option Should I Choose?

**For quick tests or demos:** Option 1 (Fast)  
**For everyday transcription:** Option 2 (Balanced)  
**For meetings with speaker ID:** Option 3 (Accurate) or 5 (Premium)  
**For maximum local accuracy:** Option 4 (Best)  
**For professional/commercial use:** Option 5 (Premium)

## ⚙️ Configuration

### API Keys Configuration

Create a `.env` file in the project directory:

```bash
# For AI analysis features (optional)
OPENAI_API_KEY=your_openai_api_key_here

# For ElevenLabs Scribe (Option 5) - Premium transcription
ELEVENLABS_SCRIBE_KEY=your_elevenlabs_api_key_here
```

**API Key Setup:**

**ElevenLabs Scribe (for Option 5):**
1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Go to your [API Keys page](https://elevenlabs.io/app/settings/api-keys)
3. Create a new API key
4. Add it to your `.env` file as `ELEVENLABS_SCRIBE_KEY`

**OpenAI (optional - for analysis features):**
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys section
3. Create a new secret key
4. Add it to your `.env` file as `OPENAI_API_KEY`

**Without API keys:** Options 1-4 work perfectly for local transcription and basic analysis.

## 🔧 Troubleshooting

### Common Issues

1. **"FFmpeg not found"**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   ```

2. **"pyannote.audio not found" (Speaker diarization disabled)**
   ```bash
   pip install pyannote.audio>=3.1.0
   ```

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
- **TXT**: Plain text transcript
- **JSON**: Detailed transcription with timestamps
- **SRT**: Subtitle file for video players
- **VTT**: Web-compatible subtitle format

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

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Install FFmpeg and ensure it's in your PATH
   - Test with: `ffmpeg -version`

2. **Out of memory errors**
   - Use smaller Whisper models (tiny/base)
   - Reduce audio duration
   - Close other applications

3. **Slow transcription**
   - Enable GPU acceleration
   - Use smaller models for testing
   - Ensure adequate RAM

4. **Audio capture fails**
   - Check internet connection
   - Verify URL is accessible
   - Some streams may be region-locked

### Getting Help

1. Check the logs in `video_transcription.log`
2. Verify all dependencies are installed
3. Test with shorter audio clips first
4. Check system requirements

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