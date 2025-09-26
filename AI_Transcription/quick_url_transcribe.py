#!/usr/bin/env python3
"""
Quick URL Transcription - Clean UI Version
Enter a URL, get complete transcription + analysis with minimal terminal output
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import yt_dlp
import tempfile
import json
import time

# Import components
from audio_transcriber import AudioTranscriber
from openai_analyzer import OpenAIAnalyzer
from analyzer import TextAnalyzer
from captions import segments_to_srt, segments_to_vtt, Segment as CaptionSegment
from custom_analyzer import CustomAnalyzer
from output_formatter import OutputFormatter
from file_manager import FileManager
from clean_ui import (
    start_transcription, update_status, show_model, complete_with_stats,
    format_duration, OutputSuppressor
)

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

    audio_file = file_path
    temp_audio = None

    # Check if we need to extract audio from video
    if file_ext in video_extensions:
        # Video file - extract audio silently
        temp_audio = tempfile.mktemp(suffix='.wav')
        try:
            with OutputSuppressor():
                subprocess.run([
                    'ffmpeg', '-i', file_path,
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    temp_audio
                ], check=True, capture_output=True)
            audio_file = temp_audio
        except subprocess.CalledProcessError:
            if temp_audio and os.path.exists(temp_audio):
                os.unlink(temp_audio)
            raise

    # Try to get duration using ffprobe
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file
        ], capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0
    except:
        duration = 0

    metadata = {
        'title': file_name,
        'duration': duration,
        'description': f'Local file: {file_name}',
        'url': file_path
    }

    # Local files are not temporary - user owns them
    is_temp_file = (temp_audio is not None)

    return audio_file, metadata, is_temp_file

def download_audio(url: str) -> tuple:
    """Download audio from URL and return temp file path with metadata"""
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
        with OutputSuppressor():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
    """Get audio from URL or local file path"""
    # Check if it's a URL or local file
    if input_path.startswith(('http://', 'https://', 'www.')):
        # It's a URL - download it
        if not input_path.startswith(('http://', 'https://')):
            input_path = 'https://' + input_path
        return download_audio(input_path)
    else:
        # It's a local file - check if exists
        if os.path.exists(input_path):
            return process_local_file(input_path)
        else:
            # Maybe it's a URL without protocol?
            if '.' in input_path and not os.path.exists(input_path):
                return download_audio('https://' + input_path)
    return None, None, False

def transcribe_audio(audio_file: str) -> dict:
    """Transcribe audio with best available method"""
    # Start transcription stage
    update_status('transcribe')

    # Check if we should use Scribe (env var or default)
    use_scribe = os.getenv("USE_SCRIBE", "true").lower() == "true"
    model_used = None

    if use_scribe:
        try:
            # Try ElevenLabs Scribe silently
            with OutputSuppressor():
                transcriber = AudioTranscriber(
                    model_size='base',  # Used as fallback
                    enable_diarization=True,
                    diarization_provider='elevenlabs'
                )

            # Check if Scribe loaded successfully
            if transcriber.diarization_provider == 'elevenlabs':
                model_used = 'ElevenLabs Scribe'
                show_model(model_used, success=True)

                # Transcribe silently
                with OutputSuppressor():
                    result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)

                if result and result.get('text'):
                    return result
                # Else fall through to Whisper
        except Exception:
            # Silently fall back to Whisper
            pass

    # Fallback to Whisper
    if not model_used:
        try:
            model_used = 'Whisper'
            show_model(model_used, success=False)  # False because it's fallback

            # Load and transcribe with Whisper silently
            with OutputSuppressor():
                transcriber = AudioTranscriber(
                    model_size='base',
                    enable_diarization=False
                )
                result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)

            if result and result.get('text'):
                return result
            else:
                raise Exception("No transcript generated")

        except Exception as e:
            print(f"\n❌ Transcription failed: {str(e)[:80]}")
            sys.exit(1)

def analyze_transcript(transcript: str, custom_prompt: str = None) -> dict:
    """Analyze transcript with AI"""
    # Update status to analysis stage
    update_status('analyze')

    # Use OpenAI if available, otherwise local
    openai_analyzer = OpenAIAnalyzer()

    if openai_analyzer.client:
        # Using OpenAI for analysis
        if custom_prompt:
            custom_analyzer = CustomAnalyzer()
            result = custom_analyzer.analyze_custom(transcript, custom_prompt, "")
            return result.get('analysis', "Analysis failed")
        else:
            summary = openai_analyzer.summarize(transcript)
            themes = openai_analyzer.extract_themes(transcript, num_themes=3)
            sentiment = openai_analyzer.analyze_sentiment(transcript)

            return {
                'summary': summary,
                'themes': themes,
                'sentiment': sentiment
            }
    else:
        # Using local models
        analyzer = TextAnalyzer()

        if custom_prompt:
            # Basic local custom analysis
            return f"Local analysis: {custom_prompt}\n\nSummary: {analyzer.summarize(transcript, max_length=150)}"
        else:
            summary = analyzer.summarize(transcript, max_length=150)
            themes = analyzer.extract_themes(transcript, num_themes=3)
            sentiment = analyzer.analyze_sentiment(transcript)

            return {
                'summary': summary,
                'themes': themes,
                'sentiment': sentiment
            }

def save_results(transcript_data: dict, metadata: dict, custom_analysis: str = None) -> Path:
    """Save all results to organized folder structure"""
    # Create output directory based on timestamp and title
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in metadata.get('title', 'transcript')[:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_')

    video_dir = Path("transcripts") / f"{timestamp}_{safe_title}"
    video_dir.mkdir(parents=True, exist_ok=True)

    # Count files saved
    file_count = 0

    # Save transcript
    transcript_file = video_dir / "transcript.txt"
    formatter = OutputFormatter()
    formatted_transcript = formatter.format_diarized_transcript(transcript_data)
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(formatted_transcript)
    file_count += 1

    # Save analysis if provided
    if custom_analysis:
        analysis_file = video_dir / "analysis.txt"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("ANALYSIS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            if isinstance(custom_analysis, dict):
                # Standard analysis
                f.write(f"SUMMARY:\n{custom_analysis.get('summary', 'N/A')}\n\n")
                f.write("THEMES:\n")
                for theme in custom_analysis.get('themes', []):
                    f.write(f"- {theme.get('title', 'Theme')}: {theme.get('description', '')}\n")
                f.write(f"\nSENTIMENT: {custom_analysis.get('sentiment', {}).get('label', 'Unknown')}\n")
            else:
                # Custom analysis
                f.write(str(custom_analysis))
        file_count += 1

    # Save markdown
    markdown_file = video_dir / "transcript.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(f"# {metadata.get('title', 'Transcript')}\n\n")
        f.write(f"**URL:** {metadata.get('url', 'N/A')}\n")
        f.write(f"**Duration:** {format_duration(metadata.get('duration', 0))}\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Transcript\n\n")
        f.write(formatted_transcript)
    file_count += 1

    # Save raw JSON
    json_file = video_dir / "transcript_raw.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)
    file_count += 1

    # Save SRT if segments available
    if 'segments' in transcript_data and transcript_data['segments']:
        try:
            segments = [CaptionSegment(
                start=seg.get('start', 0),
                end=seg.get('end', 0),
                text=seg.get('text', ''),
                speaker=seg.get('speaker')
            ) for seg in transcript_data['segments']]

            srt_content = segments_to_srt(segments)
            srt_file = video_dir / "captions.srt"
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            file_count += 1

            vtt_content = segments_to_vtt(segments)
            vtt_file = video_dir / "captions.vtt"
            with open(vtt_file, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            file_count += 1
        except:
            pass  # Silently skip if caption generation fails

    # Save metadata
    metadata_file = video_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    file_count += 1

    return video_dir, file_count

def main():
    """Main execution function with clean UI"""
    # Get input from user or command line
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        # Simple prompt without clearing screen
        print("🎬 QUICK TRANSCRIPTION")
        print("Enter any video URL or local file path for transcription + analysis!")
        input_path = input("📺 Enter URL or file path: ").strip()

    if not input_path:
        print("❌ No input provided")
        return

    # Initialize clean UI
    start_transcription(input_path)

    # Track start time for duration
    start_time = time.time()

    try:
        # Step 1: Get audio file (from URL or local file)
        audio_file, metadata, is_temp_file = get_audio_file(input_path)
        if not audio_file:
            print("\n❌ Unable to process the input. Please check the URL or file path.")
            return

        # Step 2: Get analysis preference BEFORE transcription (improved user flow)
        print("\n" + "=" * 60)
        print("📝 ANALYSIS OPTIONS")
        print("=" * 60)
        print("\n1. Press Enter for standard analysis")
        print("2. Type a custom question about the content")

        user_prompt = input("\nYour choice (or Enter to skip): ").strip()

        # Step 3: Transcribe audio
        transcript_data = transcribe_audio(audio_file)

        # Step 4: Analyze if requested
        analysis_result = None
        if user_prompt:
            analysis_result = analyze_transcript(
                transcript_data.get('text', ''),
                user_prompt if user_prompt else None
            )

        # Step 5: Save results
        output_dir, file_count = save_results(transcript_data, metadata, analysis_result)

        # Calculate duration and stats
        total_time = time.time() - start_time
        duration = metadata.get('duration', 0)
        duration_str = format_duration(duration) if duration else "Unknown"

        # Count speakers
        speaker_count = 0
        if 'segments' in transcript_data:
            unique_speakers = set(seg.get('speaker') for seg in transcript_data['segments']
                                if seg.get('speaker'))
            speaker_count = len(unique_speakers) if unique_speakers else 1

        # Estimate confidence (simplified)
        confidence = 0.95 if 'elevenlabs' in str(transcript_data.get('provider', '')).lower() else 0.85

        # Complete with stats
        complete_with_stats(
            duration=duration_str,
            speakers=speaker_count,
            confidence=confidence,
            output_dir=str(output_dir),
            file_count=file_count
        )

    except KeyboardInterrupt:
        print("\n\n❌ Transcription cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

    finally:
        # Clean up temp files if needed
        if 'audio_file' in locals() and is_temp_file and os.path.exists(audio_file):
            try:
                os.unlink(audio_file)
            except:
                pass

if __name__ == "__main__":
    main()