# 🎬 AI Transcription Tool

A powerful, all-in-one audio/video transcription tool powered by OpenAI Whisper with speaker diarization, live transcription, and multiple export formats.

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

1. **📁 File/URL Transcription** - YouTube videos or local files
2. **🎙️ Live Transcription** - Real-time from your microphone
3. **🌐 Web Interface** - Browser-based with downloads
4. **🚀 Quick Transcribe** - Fastest mode for quick results
5. **📊 Batch Processing** - Multiple files at once
6. **⚙️ Settings & Help** - Configure and learn

## 📖 Detailed Usage

### Example: Transcribe a YouTube Video

1. Run `python transcribe.py`
2. Choose option 1 (File/URL Transcription)
3. Select option 1 (YouTube URL)
4. Paste your YouTube URL
5. Choose option 3, 4, or 5 for speaker identification
6. Wait for transcription
7. Find your transcript in the `transcripts/` folder

### Example: Live Transcription

1. Run `python transcribe.py`
2. Choose option 2 (Live Transcription)
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

All transcripts are saved to the `transcripts/` folder with timestamps:

- **TXT**: Clean text with speaker labels
- **SRT**: Subtitle files for video editors
- **JSON**: Complete data with timestamps

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
NUM_THEMES=5
```

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
from audio_capture import AudioCapture
from transcriber import Transcriber
from analyzer import TextAnalyzer

# Capture audio
capture = AudioCapture()
audio_file, info = capture.capture_from_url(
    "https://youtube.com/watch?v=example",
    duration=300
)

# Transcribe
transcriber = Transcriber()
transcript = transcriber.transcribe(audio_file, model_size="base")

# Analyze
analyzer = TextAnalyzer()
summary = analyzer.summarize(transcript["text"])
themes = analyzer.extract_themes(transcript["text"])
sentiment = analyzer.analyze_sentiment(transcript["text"])
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

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video/audio extraction
- [Streamlit](https://streamlit.io/) for the web interface
- [Transformers](https://huggingface.co/transformers/) for text analysis