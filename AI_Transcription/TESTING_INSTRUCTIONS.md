# Testing Instructions

## Quick Start

The Streamlit app is running at: **http://localhost:8501**

Open this URL in your browser to access the web interface.

## About Your Livestorm URL

The Livestorm URL you provided:
```
https://app.livestorm.co/elevenlabs/how-to-create-personalised-shopping-experiences-with-conversational-ai/live?s=0c7de087-dec6-44ca-b3ec-8011627526d1#/transcript
```

**Unfortunately, Livestorm is not supported** by the direct URL extraction method because:
- It requires JavaScript execution
- Uses proprietary streaming protocols
- Has access controls and authentication

## Alternative Solutions for Livestorm Content

### Option 1: File Upload (Recommended)
1. If you have a recording of the Livestorm session:
   - Go to the web interface at http://localhost:8501
   - Select "Upload File" option
   - Upload your audio/video file
   - Process and transcribe

### Option 2: Screen Recording
1. Use macOS screen recording or other tools to record the Livestorm session
2. Save as MP4/MOV file
3. Upload to the tool

### Option 3: Check for YouTube/Vimeo Replays
- Sometimes Livestorm sessions are reposted on YouTube or Vimeo
- These URLs would work directly with the tool

## Testing with Supported Platforms

To test the tool's functionality, try these URLs:

### YouTube Examples:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=jNQXAC9IVRw
```

### How to Test:
1. Open http://localhost:8501
2. Go to "Audio/Video Input" tab
3. Select "Stream URL"
4. Paste a YouTube URL
5. Set duration (30-60 seconds for testing)
6. Click "Start Capture"
7. Move to "Transcription" tab
8. Select model size (use "tiny" for speed)
9. Click "Start Transcription"
10. Go to "Analysis" tab for summaries and themes

## Command Line Testing

You can also test from command line:

```bash
cd "/Users/justinwitcoff/Coding Projects/video-transcription-tool"
source venv/bin/activate
python demo.py
```

Choose option 2 to see how the tool handles Livestorm URLs.

## Supported Platforms

✅ **Fully Supported:**
- YouTube (including live streams)
- Twitch
- Vimeo
- Facebook Videos
- Instagram
- TikTok
- Twitter Videos
- Reddit Videos
- And 1000+ more platforms

❌ **Not Supported:**
- Livestorm
- Zoom recordings (without direct links)
- Teams recordings
- Password-protected content
- Corporate streaming platforms

## File Upload Formats

If you have local files, these formats are supported:
- **Video:** MP4, AVI, MOV, MKV, WebM
- **Audio:** MP3, WAV, M4A, FLAC, OGG

## Performance Tips

- Use "tiny" or "base" Whisper models for faster processing
- Start with short durations (30-60 seconds) for testing
- GPU acceleration will work if you have compatible hardware

## Getting the Livestorm Content

For your specific Livestorm session, you could:

1. **Contact ElevenLabs directly** - They may provide recordings
2. **Check their YouTube channel** - Sessions are sometimes reposted
3. **Use screen recording** during live sessions
4. **Ask attendees** if anyone recorded it

## Need Help?

The tool is fully functional and ready to use. The main limitation is that Livestorm isn't a supported platform for direct URL extraction, but the file upload feature provides a complete workaround.