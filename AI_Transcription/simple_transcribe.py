#!/usr/bin/env python3
"""
Simple transcription script - No Streamlit, just transcribe and analyze
For recorded videos or audio files
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import platform
import yt_dlp

# Import components
from audio_transcriber import AudioTranscriber
from openai_analyzer import OpenAIAnalyzer
from analyzer import TextAnalyzer

def transcribe_url(url: str):
    """Transcribe a video URL"""
    print(f"\n🎥 Processing URL: {url}")
    print("-" * 50)
    
    # Download audio first
    print("📥 Downloading audio...")
    audio_file = download_audio(url)
    
    if not audio_file:
        print("❌ Failed to download audio")
        return
    
    # Transcribe
    transcribe_file(audio_file)
    
    # Clean up
    try:
        os.unlink(audio_file)
    except:
        pass

def download_audio(url: str) -> str:
    """Download audio from URL"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Find the output file
            for file in Path('.').glob('temp_audio.*'):
                return str(file)
        return None
    except Exception as e:
        print(f"Download error: {e}")
        return None

def transcribe_file(file_path: str):
    """Transcribe an audio/video file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"\n📁 Processing file: {file_path}")
    print("-" * 50)
    
    # Choose options
    print("\n⚙️  Transcription Options:")
    print("1. Fast (tiny model, no diarization)")
    print("2. Balanced (base model, no diarization)")
    print("3. Accurate (base model + speaker diarization)")
    print("4. Best (large model + diarization) [slow]")
    
    choice = input("Choose option (1-4) [2]: ").strip() or "2"
    
    # Map choices
    options = {
        "1": ("tiny", False),
        "2": ("base", False),
        "3": ("base", True),
        "4": ("large", True)
    }
    
    model_size, enable_diarization = options.get(choice, ("base", False))
    
    # Initialize transcriber
    print(f"\n🔄 Transcribing with {model_size} model...")
    if enable_diarization:
        print("   Including speaker diarization (this may take longer)...")
    
    transcriber = AudioTranscriber(
        model_size=model_size,
        enable_diarization=enable_diarization
    )
    
    # Transcribe
    try:
        result = transcriber.transcribe_from_file(
            file_path,
            include_timestamps=True
        )
        
        print("\n✅ Transcription complete!")
        
        # Display results
        print("\n" + "=" * 60)
        print("TRANSCRIPT")
        print("=" * 60)
        
        if result.get("has_diarization") and result.get("segments"):
            # With speakers
            current_speaker = None
            for segment in result["segments"]:
                speaker = segment.get("speaker", "Unknown")
                if speaker != current_speaker:
                    print(f"\n{speaker}:")
                    current_speaker = speaker
                print(f"  {segment['text'].strip()}")
        else:
            # Without speakers
            print(result["text"])
        
        print("\n" + "=" * 60)
        
        # Save transcript
        save = input("\n💾 Save transcript? (y/n): ").strip().lower()
        if save == 'y':
            save_transcript(result, file_path)
        
        # Analyze
        analyze = input("\n🤖 Generate AI analysis? (y/n): ").strip().lower()
        if analyze == 'y':
            analyze_transcript(result["text"])
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")

def save_transcript(result: dict, original_file: str):
    """Save transcript to file"""
    # Create transcripts directory if it doesn't exist
    output_dir = Path("transcripts")
    output_dir.mkdir(exist_ok=True)
    
    base_name = Path(original_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as text
    txt_file = output_dir / f"{base_name}_transcript_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        # Add header
        f.write(f"TRANSCRIPTION\n")
        f.write(f"File: {original_file}\n")
        f.write(f"Generated: {datetime.now()}\n")
        if result.get("has_diarization"):
            f.write(f"Speaker Diarization: ENABLED\n")
        f.write("="*60 + "\n\n")
        
        if result.get("has_diarization"):
            current_speaker = None
            for segment in result.get("segments", []):
                speaker = segment.get("speaker", "Unknown")
                if speaker != current_speaker:
                    f.write(f"\n{speaker}:\n")
                    current_speaker = speaker
                f.write(f"{segment['text'].strip()}\n")
        else:
            f.write(result["text"])
    
    print(f"✅ Saved transcript: {txt_file}")
    print(f"   Location: {txt_file.absolute()}")
    
    # Save as SRT
    srt = input("   Also save as SRT subtitles? (y/n): ").strip().lower()
    if srt == 'y':
        srt_file = output_dir / f"{base_name}_subtitles_{timestamp}.srt"
        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result.get("segments", []), 1):
                start = format_timestamp(segment["start"])
                end = format_timestamp(segment["end"])
                text = segment["text"].strip()
                if segment.get("speaker"):
                    text = f"[{segment['speaker']}] {text}"
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        print(f"✅ Saved subtitles: {srt_file}")
        print(f"   Location: {srt_file.absolute()}")
    
    # Offer to open directory
    if input("\n📂 Open output folder? (y/n): ").strip().lower() == 'y':
        if platform.system() == "Windows":
            subprocess.run(["explorer", str(output_dir.absolute())])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(output_dir.absolute())])
        else:  # Linux
            subprocess.run(["xdg-open", str(output_dir.absolute())])

def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def analyze_transcript(text: str):
    """Analyze transcript with AI"""
    print("\n🔄 Generating analysis...")
    
    # Try OpenAI first
    analyzer = OpenAIAnalyzer()
    if not analyzer.client:
        print("   Using local models (no OpenAI API key found)")
        analyzer = TextAnalyzer()
    else:
        print("   Using OpenAI GPT-4 for analysis")
    
    # Summary
    print("\n📝 SUMMARY:")
    print("-" * 40)
    summary = analyzer.summarize(text)
    print(summary)
    
    # Themes
    print("\n🎯 KEY THEMES:")
    print("-" * 40)
    themes = analyzer.extract_themes(text, num_themes=5)
    for i, theme in enumerate(themes, 1):
        print(f"\n{i}. {theme['title']}")
        if theme.get('description'):
            print(f"   {theme['description'][:100]}...")
        if theme.get('keywords'):
            print(f"   Keywords: {', '.join(theme['keywords'][:5])}")
    
    # Sentiment
    print("\n😊 SENTIMENT:")
    print("-" * 40)
    sentiment = analyzer.analyze_sentiment(text)
    print(f"   Overall: {sentiment['label']}")
    print(f"   Confidence: {sentiment['confidence']:.1%}")
    if sentiment.get('emotion'):
        print(f"   Emotion: {sentiment['emotion'].title()}")
    
    # Key points (if using OpenAI)
    if isinstance(analyzer, OpenAIAnalyzer) and analyzer.client:
        print("\n💡 KEY POINTS:")
        print("-" * 40)
        points = analyzer.extract_key_points(text, num_points=5)
        for point in points:
            print(f"   • {point}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("🎬 SIMPLE TRANSCRIPTION TOOL")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # File or URL provided as argument
        input_path = sys.argv[1]
        
        if input_path.startswith(('http://', 'https://', 'www.')):
            transcribe_url(input_path)
        else:
            transcribe_file(input_path)
    else:
        # Interactive mode
        print("\nChoose input type:")
        print("1. YouTube/Video URL")
        print("2. Local audio/video file")
        
        choice = input("\nEnter choice (1-2): ").strip()
        
        if choice == "1":
            url = input("Enter URL: ").strip()
            if url:
                transcribe_url(url)
        elif choice == "2":
            file_path = input("Enter file path: ").strip()
            if file_path:
                transcribe_file(file_path)
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()