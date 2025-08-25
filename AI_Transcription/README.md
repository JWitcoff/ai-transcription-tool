# Video Transcription & Analysis Tool

A powerful tool that captures audio from live video streams, transcribes speech to text, and extracts key themes and insights from the content.

## Features

- 🎬 **Live Stream Audio Capture**: Extract audio from YouTube, Twitch, and other live streaming platforms
- 🎙️ **Speech-to-Text Transcription**: High-quality transcription using OpenAI Whisper
- 📝 **Text Summarization**: Generate concise summaries of transcribed content
- 🎯 **Theme Extraction**: Identify key themes and topics automatically
- 😊 **Sentiment Analysis**: Analyze emotional tone and sentiment
- 📊 **Export Options**: Save transcripts in TXT, JSON, SRT, and VTT formats
- 🖥️ **Web Interface**: User-friendly Streamlit interface

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

### Setup

1. **Clone or download the project**
   ```bash
   cd /Users/justinwitcoff/Coding\ Projects/video-transcription-tool
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

### Web Interface

1. Open your browser to `http://localhost:8501`
2. Navigate through the three main tabs:

#### 🎥 Live Capture Tab
- Enter a video URL (YouTube, Twitch, etc.)
- Set capture duration and start time
- Click "Start Capture" to extract audio

#### 📝 Transcription Tab
- Select Whisper model size (tiny to large)
- Choose language or use auto-detection
- Click "Start Transcription" to convert audio to text
- Download results in multiple formats

#### 📊 Analysis Tab
- Generate text summaries
- Extract key themes and topics
- Analyze sentiment and emotional tone

### Supported Platforms

The tool supports audio extraction from:
- YouTube (including live streams)
- Twitch
- Vimeo
- Facebook
- Instagram
- TikTok
- Twitter
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

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# API Keys (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Audio Settings
DEFAULT_AUDIO_QUALITY=best
DEFAULT_SAMPLE_RATE=16000
MAX_AUDIO_DURATION=3600

# Model Settings
DEFAULT_WHISPER_MODEL=base
ENABLE_GPU=true

# Analysis Settings
MAX_SUMMARY_LENGTH=150
MIN_SUMMARY_LENGTH=30
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