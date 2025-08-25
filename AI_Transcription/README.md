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
5. Choose quality level 3 or 4 for speaker identification
6. Wait for transcription
7. Find your transcript in the `transcripts/` folder

### Example: Live Transcription

1. Run `python transcribe.py`
2. Choose option 2 (Live Transcription)
3. Start speaking into your microphone
4. Press Ctrl+C to stop
5. Save the transcript when prompted

### Speaker Diarization (Who Said What?)

When enabled (options 3 or 4 in quality selection), the tool identifies different speakers:

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

### Model Sizes

Choose appropriate Whisper model based on your needs:

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny  | 39 MB | Fastest | Good | Quick testing |
| base  | 74 MB | Fast | Better | General use |
| small | 244 MB | Medium | Good | Better accuracy |
| medium | 769 MB | Slow | Very Good | High accuracy |
| large | 1550 MB | Slowest | Best | Maximum accuracy |

## ⚙️ Configuration

### API Keys (Optional)

For AI analysis features, create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

Without an API key, the tool still works perfectly for transcription and basic analysis.

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