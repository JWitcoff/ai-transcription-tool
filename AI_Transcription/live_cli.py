#!/usr/bin/env python3
"""
Direct CLI version - No Streamlit, just pure Python
Run live transcription directly in your terminal
"""

import asyncio
import time
import sys
from datetime import datetime
import threading
from collections import deque

# Import our components
from live_stream_capture import LiveStreamCapture
from fast_transcriber import FastTranscriber, TranscriptionSegment, TranscriptBuffer
from live_analyzer import LiveAnalyzer
from openai_analyzer import OpenAIAnalyzer

class LiveCLI:
    """Command-line interface for live transcription"""
    
    def __init__(self):
        self.stream_capture = None
        self.transcriber = None
        self.analyzer = None
        self.openai_analyzer = None
        self.transcript_buffer = TranscriptBuffer()
        
        self.is_running = False
        self.transcript_segments = deque(maxlen=100)
        
    def run(self):
        """Main CLI interface"""
        print("=" * 60)
        print("🎥 LIVE VIDEO TRANSCRIPTION - CLI VERSION")
        print("=" * 60)
        print()
        
        # Get stream URL
        stream_url = input("Enter stream URL (YouTube/Twitch/etc): ").strip()
        if not stream_url:
            print("❌ No URL provided")
            return
        
        # Choose model
        print("\nChoose Whisper model size:")
        print("1. tiny (fastest, least accurate)")
        print("2. base (balanced) [recommended]")
        print("3. small (slower, more accurate)")
        
        model_choice = input("Enter choice (1-3) [2]: ").strip() or "2"
        model_map = {"1": "tiny", "2": "base", "3": "small"}
        model_size = model_map.get(model_choice, "base")
        
        # Check for OpenAI
        self.openai_analyzer = OpenAIAnalyzer()
        if self.openai_analyzer.client:
            print("✅ OpenAI API detected - will use for enhanced analysis")
        else:
            print("ℹ️  No OpenAI API key - using local models")
        
        print(f"\n📊 Configuration:")
        print(f"   Model: {model_size}")
        print(f"   URL: {stream_url}")
        print()
        
        # Start transcription
        try:
            print("🚀 Starting live transcription...")
            print("   Press Ctrl+C to stop")
            print("=" * 60)
            print()
            
            self.start_live_transcription(stream_url, model_size)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping transcription...")
            self.stop_transcription()
            
            # Offer to save and analyze
            self.post_processing()
    
    def start_live_transcription(self, stream_url: str, model_size: str):
        """Start the live transcription process"""
        
        # Initialize components
        self.stream_capture = LiveStreamCapture(chunk_duration=3.0)
        self.transcriber = FastTranscriber(
            model_size=model_size,
            use_faster_whisper=True
        )
        self.analyzer = LiveAnalyzer(analysis_window=60.0)
        
        # Start processing
        self.transcriber.start_processing(callback=self.on_transcription)
        self.analyzer.start_analysis()
        
        self.is_running = True
        
        # Start capture in async thread
        def capture_audio():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.stream_capture.start_live_capture(stream_url, self.on_audio_chunk)
            )
        
        capture_thread = threading.Thread(target=capture_audio, daemon=True)
        capture_thread.start()
        
        # Keep main thread alive and show status
        self.show_live_status()
    
    def on_audio_chunk(self, audio_data, timestamp):
        """Handle new audio chunk"""
        if self.transcriber:
            segment = self.transcriber.transcribe_chunk(audio_data, timestamp)
    
    def on_transcription(self, segment: TranscriptionSegment):
        """Handle transcription result"""
        if segment and segment.text.strip():
            # Add to buffer
            self.transcript_buffer.add_segment(segment)
            
            # Store segment
            self.transcript_segments.append({
                'text': segment.text,
                'timestamp': segment.start_time,
                'confidence': segment.confidence
            })
            
            # Display in terminal
            time_str = datetime.fromtimestamp(segment.start_time).strftime("%H:%M:%S")
            
            # Color code by confidence
            if segment.confidence > 0.8:
                color = '\033[92m'  # Green
            elif segment.confidence > 0.6:
                color = '\033[93m'  # Yellow
            else:
                color = '\033[91m'  # Red
            
            print(f"{color}[{time_str}]{'\033[0m'} {segment.text}")
            
            # Add to analyzer
            if self.analyzer:
                self.analyzer.add_text(segment.text, segment.start_time)
    
    def show_live_status(self):
        """Show live status updates"""
        last_analysis_time = time.time()
        
        while self.is_running:
            time.sleep(1)
            
            # Show periodic analysis (every 30 seconds)
            if time.time() - last_analysis_time > 30:
                self.show_quick_analysis()
                last_analysis_time = time.time()
    
    def show_quick_analysis(self):
        """Show quick analysis summary"""
        if not self.analyzer:
            return
        
        print("\n" + "=" * 60)
        print("📊 QUICK ANALYSIS UPDATE")
        
        # Get current themes
        themes = self.analyzer.get_current_themes(min_confidence=0.3)
        if themes:
            print("\n🎯 Top Themes:")
            for theme in themes[:3]:
                print(f"   • {theme.title}: {', '.join(theme.keywords[:3])}")
        
        # Get sentiment
        sentiment = self.analyzer.get_sentiment_summary(duration=60.0)
        print(f"\n😊 Sentiment: {sentiment['trend']} (avg: {sentiment['average']:.2f})")
        
        print("=" * 60 + "\n")
    
    def stop_transcription(self):
        """Stop all transcription processes"""
        self.is_running = False
        
        if self.stream_capture:
            self.stream_capture.stop_capture()
        
        if self.transcriber:
            self.transcriber.stop_processing()
        
        if self.analyzer:
            self.analyzer.stop_analysis()
    
    def post_processing(self):
        """Post-processing after transcription stops"""
        print("\n" + "=" * 60)
        print("📋 TRANSCRIPTION COMPLETE")
        print(f"   Total segments: {len(self.transcript_segments)}")
        print("=" * 60)
        
        if not self.transcript_segments:
            print("No transcription data collected.")
            return
        
        # Save transcript?
        save = input("\n💾 Save transcript? (y/n): ").strip().lower()
        if save == 'y':
            self.save_transcript()
        
        # Generate analysis?
        analyze = input("\n🤖 Generate AI analysis? (y/n): ").strip().lower()
        if analyze == 'y':
            self.generate_analysis()
    
    def save_transcript(self):
        """Save transcript to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"LIVE TRANSCRIPTION\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            
            for segment in self.transcript_segments:
                time_str = datetime.fromtimestamp(segment['timestamp']).strftime("%H:%M:%S")
                f.write(f"[{time_str}] {segment['text']}\n")
        
        print(f"✅ Transcript saved to: {filename}")
    
    def generate_analysis(self):
        """Generate comprehensive analysis"""
        print("\n🔄 Generating analysis...")
        
        # Combine all text
        full_text = ' '.join([seg['text'] for seg in self.transcript_segments])
        
        if self.openai_analyzer and self.openai_analyzer.client:
            print("   Using OpenAI for enhanced analysis...")
            
            # Summary
            print("\n📝 SUMMARY:")
            print("-" * 40)
            summary = self.openai_analyzer.summarize(full_text)
            print(summary)
            
            # Themes
            print("\n🎯 KEY THEMES:")
            print("-" * 40)
            themes = self.openai_analyzer.extract_themes(full_text, num_themes=5)
            for i, theme in enumerate(themes, 1):
                print(f"\n{i}. {theme['title']}")
                print(f"   {theme['description']}")
                print(f"   Keywords: {', '.join(theme['keywords'])}")
            
            # Key Points
            print("\n💡 KEY POINTS:")
            print("-" * 40)
            points = self.openai_analyzer.extract_key_points(full_text)
            for point in points:
                print(f"   • {point}")
            
            # Action Items
            action_items = self.openai_analyzer.generate_action_items(full_text)
            if action_items:
                print("\n✅ ACTION ITEMS:")
                print("-" * 40)
                for item in action_items:
                    print(f"   • {item['task']}")
            
            # Sentiment
            print("\n😊 SENTIMENT ANALYSIS:")
            print("-" * 40)
            sentiment = self.openai_analyzer.analyze_sentiment(full_text)
            print(f"   Overall: {sentiment['label']}")
            print(f"   Confidence: {sentiment['confidence']:.1%}")
            print(f"   Emotion: {sentiment.get('emotion', 'neutral').title()}")
            
        else:
            # Use local analyzer
            print("   Using local models for analysis...")
            
            from analyzer import TextAnalyzer
            local_analyzer = TextAnalyzer()
            
            # Summary
            print("\n📝 SUMMARY:")
            print("-" * 40)
            summary = local_analyzer.summarize(full_text)
            print(summary)
            
            # Themes
            print("\n🎯 KEY THEMES:")
            print("-" * 40)
            themes = local_analyzer.extract_themes(full_text)
            for theme in themes:
                print(f"\n• {theme['title']}")
                print(f"  {theme['description']}")
            
            # Sentiment
            print("\n😊 SENTIMENT:")
            print("-" * 40)
            sentiment = local_analyzer.analyze_sentiment(full_text)
            print(f"   {sentiment['label']} ({sentiment['confidence']:.1%})")
        
        # Save analysis?
        save = input("\n💾 Save analysis? (y/n): ").strip().lower()
        if save == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("TRANSCRIPTION ANALYSIS\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("SUMMARY:\n")
                f.write(summary + "\n\n")
                
                f.write("KEY THEMES:\n")
                for theme in themes[:5]:
                    f.write(f"• {theme.get('title', 'Theme')}\n")
                
                if self.openai_analyzer and self.openai_analyzer.client:
                    f.write("\nKEY POINTS:\n")
                    for point in points:
                        f.write(f"• {point}\n")
            
            print(f"✅ Analysis saved to: {filename}")


def main():
    """Main entry point"""
    cli = LiveCLI()
    cli.run()


if __name__ == "__main__":
    main()