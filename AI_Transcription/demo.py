#!/usr/bin/env python3
"""
Demo script to test the video transcription tool with a sample YouTube video
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from audio_capture import AudioCapture
from transcriber import Transcriber
from analyzer import TextAnalyzer

def demo_youtube_transcription():
    """Demo with a short YouTube video"""
    
    # Use a short, public YouTube video for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (short version)
    
    print("🎬 Video Transcription Tool Demo")
    print("=" * 50)
    print(f"Testing with URL: {test_url}")
    
    try:
        # Step 1: Audio Capture
        print("\n📡 Step 1: Capturing Audio...")
        capture = AudioCapture()
        audio_file, info = capture.capture_from_url(test_url, duration=30, start_time=0)
        
        print(f"✅ Audio captured: {info['title']}")
        print(f"   Duration: {info['duration']}s")
        print(f"   File: {audio_file}")
        
        # Step 2: Transcription
        print("\n🎙️ Step 2: Transcribing Audio...")
        transcriber = Transcriber()
        transcript = transcriber.transcribe(audio_file, model_size="tiny")  # Use tiny for speed
        
        print(f"✅ Transcription completed!")
        print(f"   Text: {transcript['text'][:100]}...")
        
        # Step 3: Analysis
        print("\n📊 Step 3: Analyzing Text...")
        analyzer = TextAnalyzer()
        
        # Generate summary
        summary = analyzer.summarize(transcript['text'])
        print(f"📝 Summary: {summary}")
        
        # Extract themes
        themes = analyzer.extract_themes(transcript['text'])
        print(f"🎯 Themes found: {len(themes)}")
        for i, theme in enumerate(themes[:2], 1):
            print(f"   {i}. {theme['title']}: {theme['description'][:50]}...")
        
        # Sentiment analysis
        sentiment = analyzer.analyze_sentiment(transcript['text'])
        print(f"😊 Sentiment: {sentiment['label']} (confidence: {sentiment['confidence']:.2f})")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True

def test_livestorm_handling():
    """Test how the tool handles Livestorm URLs"""
    print("\n🧪 Testing Livestorm URL Handling")
    print("-" * 30)
    
    livestorm_url = "https://app.livestorm.co/elevenlabs/how-to-create-personalised-shopping-experiences-with-conversational-ai/live"
    
    try:
        capture = AudioCapture()
        capture.capture_from_url(livestorm_url)
    except Exception as e:
        print(f"✅ Livestorm URL properly handled with error message:")
        print(f"   {str(e)}")
        return True
    
    print("❌ Expected error for Livestorm URL")
    return False

if __name__ == "__main__":
    print("Choose a demo:")
    print("1. YouTube transcription demo (requires internet)")
    print("2. Test Livestorm URL handling")
    print("3. Both")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice in ["1", "3"]:
        demo_youtube_transcription()
    
    if choice in ["2", "3"]:
        test_livestorm_handling()
    
    print("\n" + "=" * 50)
    print("To use the full web interface, run:")
    print("  streamlit run app.py")
    print("Then open http://localhost:8501 in your browser")