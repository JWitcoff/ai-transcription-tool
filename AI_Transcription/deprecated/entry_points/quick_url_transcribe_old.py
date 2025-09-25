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
from custom_analyzer import CustomAnalyzer
from output_formatter import OutputFormatter
from file_manager import FileManager
from clean_ui import start_transcription, update_status, show_model, complete_with_stats, format_duration, OutputSuppressor

def clear_screen():
    """Clear the terminal screen - deprecated, using clean UI instead"""
    pass  # No longer clearing screen aggressively

def process_local_file(file_path: str) -> tuple:
    """Process local audio/video file and return audio path with metadata"""
    import subprocess
    
    # Define supported extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
    audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma', '.opus']
    
    # Get file info
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
    
    # Silently process local file - info captured but not displayed
    
    audio_file = file_path
    temp_audio = None
    
    # Check if we need to extract audio from video
    if file_ext in video_extensions:
        # Video file detected - extracting audio silently
        
        # Create temp file for extracted audio
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_audio = os.path.join(temp_dir, f"extracted_audio_{timestamp}.wav")
        
        try:
            # Use ffmpeg to extract audio
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # WAV format
                '-ar', '16000',  # Sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output
                temp_audio
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg extraction failed: {result.stderr}")
            
            audio_file = temp_audio
            pass  # Audio extracted successfully
            
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Please install FFmpeg first.")
            
    elif file_ext not in audio_extensions:
        # Unknown format - attempting as audio
    
    # Create metadata similar to URL downloads
    metadata = {
        'title': os.path.splitext(file_name)[0],
        'duration': None,  # Could be extracted with ffprobe if needed
        'description': f'Local file: {file_name}',
        'source': 'local_file',
        'original_path': file_path
    }
    
    # CRITICAL: Track whether the audio_file is temporary (safe to delete)
    # Only video extractions create temp files. Audio files use the original!
    is_temp_file = (file_ext in video_extensions)
    
    return audio_file, metadata, is_temp_file

def download_audio(url: str) -> tuple:
    """Download audio from URL and return temp file path with metadata"""
    # Clean UI - no verbose download tracking

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
            # Suppress yt-dlp output
            with OutputSuppressor():
                info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            description = info.get('description', '')
            
            # Find the output file
            for file in Path(temp_dir).glob(f"transcribe_audio_{timestamp}.*"):
                metadata = {
                    'title': title,
                    'duration': duration,
                    'description': description,
                    'url': url
                }

                # Downloaded files are always temporary and safe to delete
                return str(file), metadata, True
                
        raise Exception("Audio file not found after download")
        
    except Exception as e:
        print(f"\n❌ Failed to download: {str(e)[:80]}")
        return None, None, False

def get_audio_file(input_path: str) -> tuple:
    """Get audio from URL or local file path
    
    Returns:
        tuple: (audio_file_path, metadata, is_temp_file)
        The is_temp_file flag indicates if the audio file can be safely deleted
    """
    
    # Remove quotes if present (from drag & drop)
    if input_path.startswith('"') and input_path.endswith('"'):
        input_path = input_path[1:-1]
    elif input_path.startswith("'") and input_path.endswith("'"):
        input_path = input_path[1:-1]
    
    # Check if it's a local file
    if os.path.exists(input_path):
        return process_local_file(input_path)
    else:
        # Assume it's a URL
        if not input_path.startswith(('http://', 'https://')):
            # Try as URL with https
            input_path = 'https://' + input_path
        return download_audio(input_path)

def transcribe_audio(audio_file: str):
    """Transcribe audio with best available method"""
    start_step("setup", "🛠️ Loading transcription models")

    # Check if we should use Scribe (env var or default)
    use_scribe = os.getenv("USE_SCRIBE", "true").lower() == "true"

    if use_scribe:
        try:
            update_progress("setup", 50, "🚀 Loading ElevenLabs Scribe")
            transcriber = AudioTranscriber(
                model_size='base',  # Used as fallback
                enable_diarization=True,
                diarization_provider='elevenlabs'
            )
            
            # Check if Scribe loaded successfully
            if transcriber.diarization_provider == 'elevenlabs':
                complete_step("setup")
                start_step("transcribe", "🎤 Transcribing with ElevenLabs Scribe")

                result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)

                if result and result.get('text'):
                    complete_step("transcribe")
                    skip_step("diarize", "included in ElevenLabs Scribe")
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
        update_progress("setup", 80, "🔄 Loading Whisper model")

        transcriber = AudioTranscriber(
            model_size='base',
            enable_diarization=False
        )

        complete_step("setup")
        start_step("transcribe", "🎤 Transcribing with Whisper")

        result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)

        if result and result.get('text'):
            complete_step("transcribe")
            skip_step("diarize", "not available with local Whisper")
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

def save_results(result: dict, metadata: dict, analysis_result: dict = None):
    """Save formatted transcript and analysis in organized structure"""
    formatter = OutputFormatter()
    file_manager = FileManager()
    
    # Create organized session folder
    video_dir = file_manager.create_session_folder(metadata)
    
    # Save formatted transcript
    transcript_file = video_dir / "transcript.txt"
    formatted_transcript = formatter.format_transcript(result, metadata.get('url', ''))
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(formatted_transcript)
    print(f"💾 Saved transcript: {transcript_file.name}")
    
    # Save analysis if provided
    if analysis_result and analysis_result.get('analysis'):
        analysis_file = video_dir / "analysis.txt"
        formatted_analysis = formatter.format_analysis(analysis_result)
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write(formatted_analysis)
        print(f"💾 Saved analysis: {analysis_file.name}")
        
        # Also save analysis as JSON
        analysis_json_file = video_dir / "analysis.json"
        with open(analysis_json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
    
    # Save markdown version
    markdown_file = video_dir / "transcript.md"
    markdown_content = formatter.create_markdown_output(result, analysis_result, metadata.get('url', ''))
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"💾 Saved markdown: {markdown_file.name}")
    
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
        srt_file = video_dir / "subtitles.srt"
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(segments_to_srt(caption_segments))
        print(f"💾 Saved SRT: {srt_file.name}")
        
        # Save VTT format
        vtt_file = video_dir / "subtitles.vtt"
        with open(vtt_file, 'w', encoding='utf-8') as f:
            f.write(segments_to_vtt(caption_segments))
        print(f"💾 Saved VTT: {vtt_file.name}")
    
    # Save raw transcript JSON
    transcript_json = video_dir / "transcript_raw.json"
    with open(transcript_json, 'w', encoding='utf-8') as f:
        # Remove non-serializable items
        clean_result = result.copy()
        if 'words' in clean_result and clean_result['words']:
            # Convert Word objects to dicts if needed
            if hasattr(clean_result['words'][0], '__dict__'):
                clean_result['words'] = [w.__dict__ for w in clean_result['words']]
        
        json.dump(clean_result, f, indent=2, ensure_ascii=False, default=str)
    
    # Save metadata
    metadata_file = video_dir / "metadata.json"
    metadata_dict = {
        "video_info": metadata,
        "transcription": {
            "provider": result.get('provider', 'unknown'),
            "language": result.get('language', 'auto-detected'),
            "has_diarization": result.get('has_diarization', False),
            "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        "analysis": {
            "prompt": analysis_result.get('prompt', '') if analysis_result else None,
            "provider": analysis_result.get('provider', '') if analysis_result else None
        }
    }
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n📂 All files saved to: {video_dir.absolute()}")
    print(f"   📄 Formatted transcript: transcript.txt")
    print(f"   📝 Markdown version: transcript.md")
    if analysis_result:
        print(f"   🧠 Analysis: analysis.txt")
    print(f"   📊 Raw data: transcript_raw.json")
    print(f"   ℹ️ Metadata: metadata.json")
    
    # Register session in index
    file_manager.register_session(
        video_dir,
        metadata,
        analysis_result
    )
    
    return video_dir

def format_srt_time(seconds):
    """Format seconds to SRT timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    """Main function - transcription with custom analysis for URLs and local files"""
    clear_screen()
    
    print("🎬 QUICK TRANSCRIPTION")
    print("=" * 60)
    print("Enter any video URL or local file path for transcription + analysis!")
    print("Supports: YouTube, MP4, MOV, MP3, WAV, and more!")
    print()
    
    # Get input from user or command line
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = input("📺 Enter URL or file path: ").strip()
    
    if not input_path:
        print("❌ No input provided")
        return
    
    print(f"\n🚀 Processing: {input_path}")

    # Initialize progress tracking
    audio_duration_minutes = None
    start_transcription_progress(audio_duration_minutes)
    print()  # Add space after progress bar initialization

    # Step 1: Get audio file (from URL or local file)
    audio_file, metadata, is_temp_file = get_audio_file(input_path)
    if not audio_file:
        print("\n⚠️  Unable to process the input. Please check the URL or file path.")
        input("\nPress Enter to continue...")
        return

    # Update progress tracker with actual audio duration if available
    if metadata and metadata.get('duration'):
        duration_minutes = metadata['duration'] / 60.0
        start_transcription_progress(duration_minutes)
    
    # Step 2: Ask for custom analysis preference
    print("\n" + "=" * 60)
    print("📝 ANALYSIS OPTIONS")
    print("=" * 60)
    
    # Create custom analyzer for prompt suggestions
    custom_analyzer = CustomAnalyzer()
    suggestions = custom_analyzer.suggest_prompts(
        metadata.get('title', ''),
        metadata.get('description', '')
    )
    
    print("\nWhat would you like to learn from this video?")
    print("\n1. Press Enter for standard analysis (summary, themes, sentiment)")
    print("2. Type your custom question/request")
    
    if suggestions:
        print("\n💡 Suggested prompts based on video content:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion}")
    
    print("\nExamples:")
    print("   • 'Extract all tips about YouTube growth'")
    print("   • 'List the main arguments and supporting evidence'")
    print("   • 'What are the action items mentioned?'")
    
    user_prompt = input("\n🎯 Your request (or press Enter for default): ").strip()
    
    try:
        # Step 3: Transcribe
        result = transcribe_audio(audio_file)
        if not result:
            return
        
        # Step 4: Display formatted transcript
        print("\n📄 TRANSCRIPT:")
        print("=" * 60)
        
        # Use formatter for display
        formatter = OutputFormatter()
        if result.get("has_diarization") and result.get("segments"):
            # With speakers - show formatted version
            formatted_display = formatter._format_diarized_transcript(result["segments"])
            # Limit display to first 2000 characters
            if len(formatted_display) > 2000:
                print(formatted_display[:2000])
                print("\n... [Transcript continues - see saved file for full text] ...\n")
            else:
                print(formatted_display)
        else:
            # Without speakers - show formatted paragraphs
            formatted_display = formatter._smart_paragraph_split(result.get("text", ""))
            # Limit display to first 2000 characters
            if len(formatted_display) > 2000:
                print(formatted_display[:2000])
                print("\n... [Transcript continues - see saved file for full text] ...\n")
            else:
                print(formatted_display)
        
        print("\n" + "=" * 60)
        
        # Step 5: Generate analysis (custom or standard)
        transcript_text = result.get("text", "")
        analysis_result = None
        
        if transcript_text:
            if user_prompt:
                # Custom analysis
                start_step("analyze", "🧠 Generating custom analysis")
                analysis_result = custom_analyzer.analyze_custom(
                    transcript_text,
                    user_prompt,
                    metadata.get('title', '')
                )
                complete_step("analyze")
                
                if analysis_result.get('success') and analysis_result.get('analysis'):
                    print(f"\nYour request: {user_prompt}")
                    print("\n" + "-" * 50 + "\n")
                    print(analysis_result['analysis'])
                else:
                    print("Analysis generation failed. See saved files for transcript.")
            else:
                # Standard analysis (backward compatible)
                start_step("analyze", "🧠 Generating standard analysis")
                analyze_text(transcript_text)
                complete_step("analyze")
                # Create a pseudo analysis_result for saving
                analysis_result = {
                    'prompt': 'Standard analysis (summary, themes, sentiment)',
                    'analysis': 'Standard analysis was performed (see terminal output)',
                    'provider': 'Standard'
                }

        # Step 6: Save everything with proper formatting
        start_step("save", "💾 Saving transcription files")
        video_dir = save_results(result, metadata, analysis_result)
        complete_step("save")
        
        # Complete progress tracking
        finish_progress()

        print(f"📁 Results saved to: {video_dir.name}")

        # Offer to open folder
        if input("\n📂 Open results folder? (y/n): ").strip().lower() == 'y':
            import subprocess
            import platform
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(video_dir)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(video_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(video_dir)])

        # Give user time to review results before returning to main menu
        input("\nPress Enter to return to main menu...")
    
    finally:
        # CRITICAL: Only clean up TEMPORARY files, never user's original files!
        try:
            if is_temp_file and audio_file and os.path.exists(audio_file):
                print(f"\n🧹 Cleaning up temporary file: {os.path.basename(audio_file)}")
                os.unlink(audio_file)
            elif not is_temp_file:
                print(f"\n✅ Preserving original file: {os.path.basename(audio_file)}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

if __name__ == "__main__":
    main()