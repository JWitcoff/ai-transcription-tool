#!/usr/bin/env python3
"""
WORKING CLI - Combines the proven audio_transcriber with simplified live mode
This version actually works by using the tested components properly
"""

import sys
import os
from pathlib import Path

# Add path to find audio_transcriber module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'audio_transcriber'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
from datetime import datetime
import yt_dlp
import tempfile

# Import the WORKING transcriber from audio_transcriber folder
try:
    from audio_transcriber.audio_transcriber import AudioTranscriber
except ImportError:
    from audio_transcriber import AudioTranscriber

# Import our analyzers
from openai_analyzer import OpenAIAnalyzer
from analyzer import TextAnalyzer

class WorkingCLI:
    """Simple, working CLI that uses proven components"""
    
    def __init__(self):
        self.transcriber = None
        self.analyzer = None
        
    def run(self):
        """Main menu"""
        print("=" * 60)
        print("🎬 VIDEO TRANSCRIPTION TOOL - WORKING VERSION")
        print("=" * 60)
        print()
        
        # Check for OpenAI
        self.analyzer = OpenAIAnalyzer()
        if self.analyzer.client:
            print("✅ OpenAI API detected for enhanced analysis")
        else:
            print("ℹ️  No OpenAI API - using local models")
            self.analyzer = TextAnalyzer()
        
        print("\nOptions:")
        print("1. Transcribe YouTube/Online Video")
        print("2. Transcribe Local File")
        print("3. Live Stream Transcription (simplified)")
        print("4. Batch Process Multiple Files")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == "1":
            self.transcribe_url()
        elif choice == "2":
            self.transcribe_file()
        elif choice == "3":
            self.live_transcribe()
        elif choice == "4":
            self.batch_transcribe()
        else:
            print("Invalid choice")
    
    def transcribe_url(self):
        """Transcribe from URL"""
        url = input("\nEnter video URL: ").strip()
        if not url:
            print("No URL provided")
            return
        
        print("\n⚙️  Options:")
        print("1. Fast (tiny model, no speakers)")
        print("2. Balanced (base model, no speakers)")
        print("3. Accurate (base + speaker identification)")
        print("4. Best (large + speakers) [slow]")
        
        choice = input("Choose (1-4) [2]: ").strip() or "2"
        
        options = {
            "1": ("tiny", False),
            "2": ("base", False),
            "3": ("base", True),
            "4": ("large", True)
        }
        
        model_size, enable_diarization = options.get(choice, ("base", False))
        
        # Download audio
        print("\n📥 Downloading audio...")
        audio_file = self._download_audio(url)
        
        if not audio_file:
            print("❌ Download failed")
            return
        
        # Process
        self._process_file(audio_file, model_size, enable_diarization, is_temp=True)
    
    def transcribe_file(self):
        """Transcribe local file"""
        file_path = input("\nEnter file path: ").strip()
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        print("\n⚙️  Options:")
        print("1. Fast (tiny model, no speakers)")
        print("2. Balanced (base model, no speakers)")
        print("3. Accurate (base + speaker identification)")
        print("4. Best (large + speakers) [slow]")
        
        choice = input("Choose (1-4) [2]: ").strip() or "2"
        
        options = {
            "1": ("tiny", False),
            "2": ("base", False),
            "3": ("base", True),
            "4": ("large", True)
        }
        
        model_size, enable_diarization = options.get(choice, ("base", False))
        
        self._process_file(file_path, model_size, enable_diarization, is_temp=False)
    
    def _process_file(self, file_path: str, model_size: str, enable_diarization: bool, is_temp: bool = False):
        """Process audio file with transcription"""
        print(f"\n🔄 Processing with {model_size} model...")
        if enable_diarization:
            print("   Including speaker identification...")
        
        # Initialize transcriber
        self.transcriber = AudioTranscriber(
            model_size=model_size,
            enable_diarization=enable_diarization
        )
        
        try:
            # Transcribe
            result = self.transcriber.transcribe_from_file(
                file_path,
                include_timestamps=True
            )
            
            print("\n✅ Transcription complete!")
            
            # Display results
            self._display_results(result)
            
            # Save options
            self._save_results(result, file_path)
            
            # Analyze
            if input("\n🤖 Generate AI analysis? (y/n): ").strip().lower() == 'y':
                self._analyze_results(result)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            # Clean up temp file
            if is_temp:
                try:
                    os.unlink(file_path)
                except:
                    pass
    
    def _display_results(self, result: dict):
        """Display transcription results"""
        print("\n" + "=" * 60)
        print("TRANSCRIPT")
        print("=" * 60)
        
        if result.get("has_diarization") and result.get("segments"):
            # With speakers
            current_speaker = None
            for segment in result["segments"][:20]:  # Show first 20 segments
                speaker = segment.get("speaker", "Unknown")
                if speaker != current_speaker:
                    print(f"\n{speaker}:")
                    current_speaker = speaker
                print(f"  {segment['text'].strip()}")
            
            if len(result["segments"]) > 20:
                print(f"\n... and {len(result['segments']) - 20} more segments")
        else:
            # Without speakers - show first 500 chars
            text = result["text"]
            if len(text) > 500:
                print(text[:500] + "...")
                print(f"\n[Full transcript: {len(text)} characters]")
            else:
                print(text)
        
        print("\n" + "=" * 60)
    
    def _save_results(self, result: dict, original_file: str):
        """Save transcription results"""
        if input("\n💾 Save transcript? (y/n): ").strip().lower() != 'y':
            return
        
        base_name = Path(original_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Text format
        txt_file = f"{base_name}_transcript_{timestamp}.txt"
        self.transcriber.export_transcription(result, txt_file, "txt")
        print(f"✅ Saved: {txt_file}")
        
        # SRT format
        if input("   Also save as SRT subtitles? (y/n): ").strip().lower() == 'y':
            srt_file = f"{base_name}_subtitles_{timestamp}.srt"
            self.transcriber.export_transcription(result, srt_file, "srt")
            print(f"✅ Saved: {srt_file}")
    
    def _analyze_results(self, result: dict):
        """Analyze transcription with AI"""
        print("\n🔄 Generating analysis...")
        
        text = result["text"]
        
        # Summary
        print("\n📝 SUMMARY:")
        print("-" * 40)
        summary = self.analyzer.summarize(text)
        print(summary)
        
        # Themes
        print("\n🎯 KEY THEMES:")
        print("-" * 40)
        themes = self.analyzer.extract_themes(text, num_themes=5)
        for i, theme in enumerate(themes, 1):
            print(f"\n{i}. {theme['title']}")
            if theme.get('description'):
                print(f"   {theme['description'][:100]}...")
            if theme.get('keywords'):
                print(f"   Keywords: {', '.join(theme['keywords'][:5])}")
        
        # Sentiment
        print("\n😊 SENTIMENT:")
        print("-" * 40)
        sentiment = self.analyzer.analyze_sentiment(text)
        print(f"   Overall: {sentiment['label']}")
        print(f"   Confidence: {sentiment['confidence']:.1%}")
        if sentiment.get('emotion'):
            print(f"   Emotion: {sentiment['emotion'].title()}")
        
        # Key points (if using OpenAI)
        if isinstance(self.analyzer, OpenAIAnalyzer) and self.analyzer.client:
            print("\n💡 KEY POINTS:")
            print("-" * 40)
            points = self.analyzer.extract_key_points(text, num_points=5)
            for point in points:
                print(f"   • {point}")
    
    def live_transcribe(self):
        """Simplified live transcription"""
        print("\n🔴 LIVE TRANSCRIPTION (Simplified)")
        print("-" * 40)
        
        url = input("Enter live stream URL: ").strip()
        if not url:
            print("No URL provided")
            return
        
        print("\n⚠️  Note: Live mode is simplified")
        print("   - No speaker identification")
        print("   - Basic transcription only")
        print("   - Press Ctrl+C to stop")
        
        # Try to use the simpler live mode
        try:
            from live_stream_capture import LiveStreamCapture
            from fast_transcriber import FastTranscriber
            
            print("\n🚀 Starting live capture...")
            
            # Use tiny model for speed
            transcriber = FastTranscriber(model_size="tiny", use_faster_whisper=False)
            capture = LiveStreamCapture(chunk_duration=5.0)
            
            # Simple callback to print text
            def on_transcription(segment):
                if segment and segment.text.strip():
                    time_str = datetime.fromtimestamp(segment.start_time).strftime("%H:%M:%S")
                    print(f"[{time_str}] {segment.text}")
            
            transcriber.start_processing(callback=on_transcription)
            
            # Start capture
            import asyncio
            
            async def capture_stream():
                await capture.start_live_capture(
                    url,
                    lambda audio, ts: transcriber.transcribe_chunk(audio, ts)
                )
            
            # Run until interrupted
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(capture_stream())
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping...")
                capture.stop_capture()
                transcriber.stop_processing()
                
        except Exception as e:
            print(f"❌ Live mode error: {e}")
            print("\nTry downloading the video instead (Option 1)")
    
    def batch_transcribe(self):
        """Batch process multiple files"""
        print("\n📦 BATCH TRANSCRIPTION")
        print("-" * 40)
        
        files = []
        print("Enter file paths (one per line, empty to finish):")
        
        while True:
            path = input().strip()
            if not path:
                break
            if os.path.exists(path):
                files.append(path)
            else:
                print(f"   ⚠️  Not found: {path}")
        
        if not files:
            print("No valid files")
            return
        
        print(f"\n📋 Found {len(files)} files")
        
        # Choose settings
        print("\n⚙️  Options:")
        print("1. Fast (tiny, no speakers)")
        print("2. Balanced (base, no speakers)")
        print("3. Accurate (base + speakers)")
        
        choice = input("Choose (1-3) [2]: ").strip() or "2"
        
        options = {
            "1": ("tiny", False),
            "2": ("base", False),
            "3": ("base", True)
        }
        
        model_size, enable_diarization = options.get(choice, ("base", False))
        
        # Output directory
        output_dir = input("Output directory [./transcriptions]: ").strip() or "./transcriptions"
        
        # Initialize transcriber
        self.transcriber = AudioTranscriber(
            model_size=model_size,
            enable_diarization=enable_diarization
        )
        
        # Process files
        print(f"\n🔄 Processing {len(files)} files...")
        results = self.transcriber.transcribe_batch(files, output_dir, "txt")
        
        successful = sum(1 for r in results if "error" not in r)
        print(f"\n✅ Complete: {successful}/{len(files)} successful")
    
    def _download_audio(self, url: str) -> str:
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
                ydl.download([url])
                
                # Find output file
                for file in Path('.').glob('temp_audio.*'):
                    return str(file)
            return None
            
        except Exception as e:
            print(f"Download error: {e}")
            return None


def main():
    """Run the working CLI"""
    cli = WorkingCLI()
    cli.run()


if __name__ == "__main__":
    main()