#!/usr/bin/env python3
"""
Quick URL Transcription - Dead Simple
Enter a URL, get complete transcription + analysis
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import yt_dlp
import tempfile
import json

# Import components
from audio_transcriber import AudioTranscriber
from openai_analyzer import OpenAIAnalyzer
from analyzer import TextAnalyzer
from captions import segments_to_srt, segments_to_vtt, Segment as CaptionSegment

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def download_audio(url: str) -> str:
    """Download audio from URL and return temp file path"""
    print(f"📥 Downloading audio from: {url}")
    
    # Create temp file
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_audio = os.path.join(temp_dir, f"transcribe_audio_{timestamp}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio + '.%(ext)s',
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
            print("   Extracting audio...")
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Find the output file
            for file in Path(temp_dir).glob(f"transcribe_audio_{timestamp}.*"):
                print(f"✅ Audio downloaded: {title}")
                if duration:
                    print(f"   Duration: {duration//60}:{duration%60:02d}")
                return str(file)
                
        raise Exception("Audio file not found after download")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def transcribe_audio(audio_file: str):
    """Transcribe audio with best available method"""
    print(f"\n🔄 Starting transcription...")
    
    # Check if we should use Scribe (env var or default)
    use_scribe = os.getenv("USE_SCRIBE", "true").lower() == "true"
    
    if use_scribe:
        try:
            print("🚀 Attempting ElevenLabs Scribe (premium accuracy + diarization)...")
            transcriber = AudioTranscriber(
                model_size='base',  # Used as fallback
                enable_diarization=True,
                diarization_provider='elevenlabs'
            )
            
            # Check if Scribe loaded successfully
            if transcriber.diarization_provider == 'elevenlabs':
                result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)
                
                if result and result.get('text'):
                    print("\n✅ Transcription complete with ElevenLabs Scribe!")
                    return result
                else:
                    print("⚠️  Scribe returned empty result, falling back...")
            else:
                print("⚠️  Scribe not available, using fallback...")
                
        except Exception as e:
            print(f"⚠️  Scribe failed: {e}")
            print("   Falling back to Whisper...")
    
    # Fallback to Whisper
    try:
        print("🔄 Using OpenAI Whisper for transcription...")
        print("   Model: base (74MB) - Good balance of speed and accuracy")
        
        transcriber = AudioTranscriber(
            model_size='base',
            enable_diarization=False
        )
        
        result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)
        
        if result and result.get('text'):
            print("\n✅ Transcription complete with Whisper!")
            return result
        else:
            raise Exception("Empty transcription result")
        
    except Exception as e:
        print(f"❌ All transcription methods failed: {e}")
        return None

def analyze_text(transcript: str):
    """Generate AI analysis of transcript"""
    if not transcript:
        return
    
    print("\n🧠 Generating AI Analysis...")
    
    # Try OpenAI first, fallback to local
    try:
        analyzer = OpenAIAnalyzer()
        if analyzer.client:
            print("   Using OpenAI GPT-4 for analysis")
        else:
            print("   Using local models (no OpenAI key)")
            analyzer = TextAnalyzer()
    except:
        print("   Using local models")
        analyzer = TextAnalyzer()
    
    # Generate summary
    print("\n📝 SUMMARY:")
    print("=" * 50)
    try:
        summary = analyzer.summarize(transcript)
        print(summary)
    except Exception as e:
        print(f"Summary generation failed: {e}")
    
    # Extract themes
    print("\n🎯 KEY THEMES:")
    print("=" * 50)
    try:
        themes = analyzer.extract_themes(transcript, num_themes=5)
        for i, theme in enumerate(themes, 1):
            print(f"\n{i}. {theme.get('title', 'Theme')}")
            if theme.get('description'):
                print(f"   {theme['description']}")
            if theme.get('keywords'):
                keywords = ', '.join(theme['keywords'][:5]) if isinstance(theme['keywords'], list) else theme['keywords']
                print(f"   Keywords: {keywords}")
    except Exception as e:
        print(f"Theme extraction failed: {e}")
    
    # Sentiment analysis
    print("\n😊 SENTIMENT ANALYSIS:")
    print("=" * 50)
    try:
        sentiment = analyzer.analyze_sentiment(transcript)
        print(f"Overall Sentiment: {sentiment.get('label', 'Unknown')}")
        if sentiment.get('confidence'):
            print(f"Confidence: {sentiment['confidence']:.1%}")
        if sentiment.get('emotion'):
            print(f"Dominant Emotion: {sentiment['emotion'].title()}")
    except Exception as e:
        print(f"Sentiment analysis failed: {e}")
    
    # Key points (OpenAI only)
    if hasattr(analyzer, 'client') and analyzer.client:
        print("\n💡 KEY POINTS:")
        print("=" * 50)
        try:
            points = analyzer.extract_key_points(transcript, num_points=5)
            for i, point in enumerate(points, 1):
                print(f"{i}. {point}")
        except Exception as e:
            print(f"Key points extraction failed: {e}")

def save_results(result: dict, url: str):
    """Save transcript and analysis with multiple caption formats"""
    # Create output directory
    output_dir = Path("transcripts")
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"transcript_{timestamp}"
    
    # Save transcript
    transcript_file = output_dir / f"{base_name}.txt"
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(f"Source: {url}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Provider: {result.get('provider', 'unknown')}\n")
        f.write("=" * 60 + "\n\n")
        
        if result.get("has_diarization") and result.get("segments"):
            # With speakers
            current_speaker = None
            for segment in result["segments"]:
                speaker = segment.get("speaker", "Unknown")
                if speaker != current_speaker:
                    f.write(f"\n{speaker}:\n")
                    current_speaker = speaker
                f.write(f"{segment['text'].strip()}\n")
        else:
            # Without speakers
            f.write(result.get("text", ""))
    
    # Save captions if we have segments
    if result.get("segments"):
        # Convert segments to caption format
        caption_segments = []
        for segment in result["segments"]:
            caption_segments.append(CaptionSegment(
                speaker_id=segment.get("speaker", "speaker_1"),
                start=segment.get("start", 0),
                end=segment.get("end", 0),
                text=segment.get("text", "").strip()
            ))
        
        # Save SRT format
        srt_file = output_dir / f"{base_name}.srt"
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(segments_to_srt(caption_segments))
        print(f"💾 Saved SRT: {srt_file.name}")
        
        # Save VTT format
        vtt_file = output_dir / f"{base_name}.vtt"
        with open(vtt_file, 'w', encoding='utf-8') as f:
            f.write(segments_to_vtt(caption_segments))
        print(f"💾 Saved VTT: {vtt_file.name}")
    
    # Save raw transcript JSON
    transcript_json = output_dir / f"{base_name}.json"
    with open(transcript_json, 'w', encoding='utf-8') as f:
        # Remove non-serializable items
        clean_result = result.copy()
        if 'words' in clean_result and clean_result['words']:
            # Convert Word objects to dicts if needed
            if hasattr(clean_result['words'][0], '__dict__'):
                clean_result['words'] = [w.__dict__ for w in clean_result['words']]
        
        json.dump(clean_result, f, indent=2, ensure_ascii=False, default=str)
    
    # Save segments in structured format
    if result.get("segments"):
        segments_json = output_dir / f"{base_name}_segments.json"
        with open(segments_json, 'w', encoding='utf-8') as f:
            segments_data = {
                "metadata": {
                    "source": url,
                    "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "provider": result.get('provider', 'unknown'),
                    "language": result.get('language', 'auto-detected'),
                    "total_segments": len(result["segments"])
                },
                "segments": result["segments"]
            }
            json.dump(segments_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved segments: {segments_json.name}")
    
    print(f"💾 Files saved:")
    print(f"   📄 Transcript: {transcript_file.name}")
    print(f"   📊 Raw data: {transcript_json.name}")
    print(f"   📂 Location: {output_dir.absolute()}")

def format_srt_time(seconds):
    """Format seconds to SRT timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    """Main function - simple URL transcription"""
    clear_screen()
    
    print("🎬 QUICK URL TRANSCRIPTION")
    print("=" * 60)
    print("Enter any video URL and get complete transcription + analysis!")
    print()
    
    # Get URL from user or command line
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("📺 Enter video URL (YouTube, etc.): ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\n🚀 Processing: {url}")
    
    # Step 1: Download audio
    audio_file = download_audio(url)
    if not audio_file:
        return
    
    try:
        # Step 2: Transcribe
        result = transcribe_audio(audio_file)
        if not result:
            return
        
        # Step 3: Display transcript
        print("\n📄 TRANSCRIPT:")
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
            print(result.get("text", ""))
        
        print("\n" + "=" * 60)
        
        # Step 4: Generate analysis
        transcript_text = result.get("text", "")
        if transcript_text:
            analyze_text(transcript_text)
        
        # Step 5: Save everything
        print("\n💾 SAVING RESULTS...")
        print("=" * 50)
        save_results(result, url)
        
        print(f"\n🎉 Complete! Transcription and analysis finished.")
        
        # Offer to open folder
        if input("\n📂 Open results folder? (y/n): ").strip().lower() == 'y':
            import subprocess
            import platform
            
            results_dir = Path("transcripts").absolute()
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(results_dir)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(results_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(results_dir)])
    
    finally:
        # Clean up temp file
        try:
            if os.path.exists(audio_file):
                os.unlink(audio_file)
        except:
            pass

if __name__ == "__main__":
    main()