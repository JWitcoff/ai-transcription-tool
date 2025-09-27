#!/usr/bin/env python3
"""
Quick URL Transcription - Clean UI Version
Enter a URL, get complete transcription + analysis with minimal terminal output
"""

import warnings
# Suppress torchaudio deprecation warnings early, before any imports
warnings.filterwarnings("ignore", message=".*torchaudio._backend.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*list_audio_backends.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*TorchAudio.*maintenance phase.*", category=UserWarning)

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

    # Simple working yt-dlp configuration (restored from commit c816422)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,  # Suppress output for clean UI
        'no_warnings': True,  # Suppress warnings
        'noplaylist': True,  # Only download single video, ignore playlist parameters
    }

    try:
        print("\n⏬ Downloading audio...")
        with OutputSuppressor():  # Suppress yt-dlp output for clean UI
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

                    print(f"✅ Audio downloaded: {title[:50]}...")
                    # Downloaded files are always temporary and safe to delete
                    return str(file), metadata, True

        raise Exception("Audio file not found after download")

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'live event will begin' in error_msg.lower():
            print("\n❌ This live stream hasn't started yet or has ended")
        elif 'private' in error_msg.lower():
            print("\n❌ This video is private or restricted")
        elif 'members-only' in error_msg.lower():
            print("\n❌ This content is members-only")
        elif 'sign in to confirm' in error_msg.lower() or 'bot' in error_msg.lower():
            print("\n❌ YouTube authentication required")
            print("💡 This video requires sign-in to confirm you're not a bot.")
            print("   Solutions:")
            print("   1. Make sure you're logged into Chrome browser")
            print("   2. Try accessing the video in Chrome first")
            print("   3. If the issue persists, try a different browser (Firefox/Safari)")
        elif '403' in error_msg or 'forbidden' in error_msg.lower():
            print("\n❌ Access forbidden (403 error)")
            print("💡 YouTube is blocking access. Try:")
            print("   1. Make sure you're logged into your browser")
            print("   2. Access the video in Chrome browser first")
            print("   3. Wait a few minutes and try again")
            print("   4. Check if the video is region-restricted")
        elif 'playlist' in error_msg.lower():
            print("\n❌ Playlist handling issue")
            print("💡 Try using the direct video URL without playlist parameters")
        else:
            print(f"\n❌ Download failed: {error_msg[:100]}")
            print("💡 Common solutions:")
            print("   - Check if the URL is valid and accessible")
            print("   - Try a different video if this one is restricted")
        return None, None, False

    except Exception as e:
        print(f"\n❌ Failed to download: {str(e)[:100]}")
        print("💡 Tip: Make sure the URL is valid and the content is accessible")
        return None, None, False

def _merge_phantom_speakers(transcript_data: dict, min_duration: float = 5.0, min_confidence: float = 0.7) -> dict:
    """
    Fix phantom speakers by merging short segments and enforcing realistic speaker counts

    Args:
        transcript_data: Transcript dictionary with segments
        min_duration: Minimum duration (seconds) for a speaker to be considered real
        min_confidence: Minimum confidence threshold (not used yet, for future)

    Returns:
        Cleaned transcript_data with phantom speakers merged
    """
    if not isinstance(transcript_data, dict) or 'segments' not in transcript_data:
        return transcript_data

    segments = transcript_data['segments']
    if not segments:
        return transcript_data

    # Step 1: Analyze speaker patterns
    speaker_stats = {}
    for segment in segments:
        if not isinstance(segment, dict):
            continue

        speaker = segment.get('speaker', 'Speaker 1')
        duration = segment.get('end', 0) - segment.get('start', 0)

        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                'total_duration': 0,
                'segment_count': 0,
                'first_appearance': segment.get('start', 0)
            }

        speaker_stats[speaker]['total_duration'] += duration
        speaker_stats[speaker]['segment_count'] += 1

    # Step 2: Identify phantom speakers (very short total duration)
    real_speakers = []
    phantom_speakers = []

    for speaker, stats in speaker_stats.items():
        if stats['total_duration'] >= min_duration and stats['segment_count'] >= 2:
            real_speakers.append(speaker)
        else:
            phantom_speakers.append(speaker)

    # Step 3: If we have too many speakers for a short content, limit to 2
    total_duration = max(seg.get('end', 0) for seg in segments) if segments else 0

    if total_duration < 300 and len(real_speakers) > 2:  # Less than 5 minutes, max 2 speakers
        # Keep only the two speakers with most speaking time
        speaker_durations = [(speaker, speaker_stats[speaker]['total_duration']) for speaker in real_speakers]
        speaker_durations.sort(key=lambda x: x[1], reverse=True)
        real_speakers = [speaker_durations[0][0], speaker_durations[1][0]]
        phantom_speakers.extend([s[0] for s in speaker_durations[2:]])

    # Step 4: Create speaker mapping (phantom -> real)
    speaker_mapping = {}

    # Map phantom speakers to nearest real speaker
    for phantom in phantom_speakers:
        phantom_first_time = speaker_stats[phantom]['first_appearance']

        # Find the closest real speaker by timing
        closest_speaker = real_speakers[0] if real_speakers else 'Speaker 1'
        min_time_diff = float('inf')

        for real_speaker in real_speakers:
            real_first_time = speaker_stats[real_speaker]['first_appearance']
            time_diff = abs(phantom_first_time - real_first_time)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_speaker = real_speaker

        speaker_mapping[phantom] = closest_speaker

    # Step 5: Apply mapping to segments
    cleaned_segments = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue

        segment_copy = segment.copy()
        original_speaker = segment_copy.get('speaker', 'Speaker 1')

        if original_speaker in speaker_mapping:
            segment_copy['speaker'] = speaker_mapping[original_speaker]

        cleaned_segments.append(segment_copy)

    # Step 6: Merge adjacent segments with same speaker
    merged_segments = []
    current_segment = None

    for segment in cleaned_segments:
        if current_segment is None:
            current_segment = segment.copy()
        else:
            # Check if we can merge with current segment
            current_speaker = current_segment.get('speaker', 'Speaker 1')
            segment_speaker = segment.get('speaker', 'Speaker 1')
            current_end = current_segment.get('end', 0)
            segment_start = segment.get('start', 0)

            # Merge if same speaker and segments are close (within 2 seconds)
            if current_speaker == segment_speaker and (segment_start - current_end) <= 2.0:
                # Merge text with space
                current_text = current_segment.get('text', '').strip()
                segment_text = segment.get('text', '').strip()
                current_segment['text'] = f"{current_text} {segment_text}".strip()
                current_segment['end'] = segment.get('end', current_end)
            else:
                # Different speaker or too far apart, save current and start new
                merged_segments.append(current_segment)
                current_segment = segment.copy()

    # Add the last segment
    if current_segment is not None:
        merged_segments.append(current_segment)

    # Update transcript data
    transcript_data_copy = transcript_data.copy()
    transcript_data_copy['segments'] = merged_segments

    # Update speaker count metadata if it exists
    if 'speaker_count' in transcript_data_copy:
        actual_speakers = set(seg.get('speaker', 'Speaker 1') for seg in merged_segments)
        transcript_data_copy['speaker_count'] = len(actual_speakers)

    return transcript_data_copy

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
            # Try ElevenLabs Scribe with minimal output
            transcriber = AudioTranscriber(
                model_size='base',  # Used as fallback
                enable_diarization=True,
                diarization_provider='elevenlabs'
            )

            # Check if Scribe loaded successfully
            if transcriber.diarization_provider == 'elevenlabs':
                model_used = 'ElevenLabs Scribe'
                show_model(model_used, success=True)

                # Transcribe with progress indication
                print("\n🎙️ Transcribing with ElevenLabs Scribe...")
                result = transcriber.transcribe_from_file(audio_file, include_timestamps=True)

                # Handle both string and dict responses
                if result:
                    if isinstance(result, str):
                        # ElevenLabs returned raw text, convert to dict format
                        result = {
                            'text': result,
                            'provider': 'elevenlabs',
                            'has_diarization': False,
                            'segments': []
                        }

                    if isinstance(result, dict) and result.get('text'):
                        return result

                print("⚠️ ElevenLabs returned no text, falling back to Whisper...")
        except Exception as e:
            # Show error and fall back to Whisper
            print(f"⚠️ ElevenLabs unavailable: {str(e)[:50]}, using Whisper...")
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

def save_results(transcript_data, metadata: dict, custom_analysis = None) -> Path:
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

    # Handle both string and dict transcript formats
    if isinstance(transcript_data, str):
        # Raw text - save directly
        formatted_transcript = f"# {metadata.get('title', 'Transcript')}\n\n{transcript_data}"
    else:
        # Dict format - use formatter
        formatted_transcript = formatter.format_transcript(transcript_data, metadata.get('url', ''))

    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(formatted_transcript)
    file_count += 1

    # Save analysis if provided (now in two-part format)
    if custom_analysis:
        analysis_file = video_dir / "analysis.txt"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("ANALYSIS\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Handle new two-part format or legacy formats
            if isinstance(custom_analysis, str):
                # New two-part format: **SUMMARY**\n...\n\n**ANALYSIS**\n...
                f.write(custom_analysis)
            elif isinstance(custom_analysis, dict):
                # Legacy format - convert to new format
                summary = custom_analysis.get('summary', 'No summary available')
                themes = custom_analysis.get('themes', '')
                sentiment = custom_analysis.get('sentiment', '')

                f.write(f"**SUMMARY**\n{summary}\n\n")
                if themes or sentiment:
                    f.write("**ANALYSIS**\n")
                    if themes:
                        f.write(f"- Themes: {themes}\n")
                    if sentiment:
                        f.write(f"- Sentiment: {sentiment}\n")
            else:
                # Fallback for any other format
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

    # Save SRT if segments available (with type safety)
    if isinstance(transcript_data, dict) and 'segments' in transcript_data and transcript_data['segments']:
        try:
            segments = [CaptionSegment(
                start=seg.get('start', 0),
                end=seg.get('end', 0),
                text=seg.get('text', ''),
                speaker=seg.get('speaker')
            ) for seg in transcript_data['segments'] if isinstance(seg, dict)]

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

def main(input_path=None):
    """Main execution function with clean UI

    Args:
        input_path: Optional URL or file path. If not provided, will prompt user.
    """
    # Get input from user, parameter, or command line
    if input_path is None:
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
            print("💡 Common issues:")
            print("  - URL might be invalid or restricted")
            print("  - Live stream might not be available")
            print("  - File path might not exist")
            return

        # Step 2: Get analysis preference BEFORE transcription (improved user flow)
        print("\n" + "=" * 60)
        print("📝 ANALYSIS OPTIONS")
        print("=" * 60)
        print("\n1. Press Enter for standard analysis")
        print("2. Type a custom question about the content")

        user_prompt = input("\nYour choice (or Enter for standard): ").strip()

        # Step 3: Transcribe audio
        transcript_data = transcribe_audio(audio_file)

        # Check if transcription failed and returned a string error
        if isinstance(transcript_data, str):
            print(f"❌ Transcription failed: {transcript_data}")
            return

        # Ensure we have a valid dictionary result
        if not isinstance(transcript_data, dict) or not transcript_data.get('text'):
            print("❌ Error: Invalid transcription result")
            return

        # Step 3.5: Fix phantom speakers (Critical for accuracy)
        transcript_data = _merge_phantom_speakers(transcript_data)

        # Step 4: Always analyze using new two-part format
        analysis_result = None
        # Extract text from validated dict
        transcript_text = transcript_data.get('text', '')

        if user_prompt:
            # Custom analysis with user's prompt
            custom_analyzer = CustomAnalyzer()
            result = custom_analyzer.analyze_custom(transcript_text, user_prompt, "")
            if isinstance(result, dict):
                analysis_result = result.get('analysis', "Analysis failed")
            else:
                analysis_result = str(result)
        else:
            # Standard analysis using new unified format
            analyzer = TextAnalyzer()
            analysis_result = analyzer.summarize(transcript_text)  # Now returns two-part format

        # Step 5: Save results
        output_dir, file_count = save_results(transcript_data, metadata, analysis_result)

        # Calculate duration and stats
        total_time = time.time() - start_time
        duration = metadata.get('duration', 0)
        duration_str = format_duration(duration) if duration else "Unknown"

        # Count speakers (with type safety)
        speaker_count = 0
        if isinstance(transcript_data, dict) and 'segments' in transcript_data:
            unique_speakers = set(seg.get('speaker') for seg in transcript_data['segments']
                                if isinstance(seg, dict) and seg.get('speaker'))
            speaker_count = len(unique_speakers) if unique_speakers else 1

        # Estimate confidence (with type safety)
        confidence = 0.85  # Default
        if isinstance(transcript_data, dict):
            provider = transcript_data.get('provider', '')
            confidence = 0.95 if 'elevenlabs' in str(provider).lower() else 0.85

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