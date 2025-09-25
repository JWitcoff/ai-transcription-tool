#!/usr/bin/env python3
"""
Simple CLI for YouTube video transcription and summarization
"""

import sys
from audio_capture import AudioCapture
from transcriber import Transcriber
from analyzer import TextAnalyzer
import json
from datetime import datetime

def main():
    print("\n🎬 YouTube Video Transcriber & Summarizer")
    print("-" * 50)
    
    # Get video URL
    url = input("\nEnter YouTube video URL: ").strip()
    if not url:
        print("❌ No URL provided. Exiting.")
        return
    
    # Ask for duration
    duration_input = input("Enter capture duration in seconds (or press Enter for full video): ").strip()
    duration = int(duration_input) if duration_input else None
    
    # Ask for model size
    print("\nWhisper model sizes:")
    print("1. tiny (fastest, least accurate)")
    print("2. base (good balance)")
    print("3. small (better accuracy)")
    print("4. medium (high accuracy)")
    print("5. large (best accuracy, slowest)")
    
    model_choice = input("\nChoose model (1-5, default is 2): ").strip() or "2"
    model_sizes = {"1": "tiny", "2": "base", "3": "small", "4": "medium", "5": "large"}
    model_size = model_sizes.get(model_choice, "base")
    
    # Ask what to do
    print("\nWhat would you like to do?")
    print("1. Transcribe only")
    print("2. Transcribe and summarize")
    print("3. Full analysis (transcribe, summarize, themes, sentiment)")
    
    action = input("\nChoose action (1-3, default is 2): ").strip() or "2"
    
    try:
        # Step 1: Capture audio
        print(f"\n📥 Capturing audio from: {url}")
        if duration:
            print(f"   Duration: {duration} seconds")
        
        capture = AudioCapture()
        audio_file, info = capture.capture_from_url(url, duration=duration)
        
        if audio_file:
            print(f"✅ Audio captured successfully: {audio_file}")
            print(f"   Title: {info.get('title', 'Unknown')}")
            print(f"   Duration: {info.get('duration', 'Unknown')} seconds")
        else:
            print("❌ Failed to capture audio")
            return
        
        # Step 2: Transcribe
        print(f"\n📝 Transcribing with Whisper {model_size} model...")
        print(f"   This may take several minutes depending on audio length...")
        
        # Estimate time based on model and audio duration
        audio_duration = info.get('duration', 0)
        if audio_duration > 0:
            # Rough estimates: tiny=0.1x, base=0.2x, small=0.4x, medium=0.8x, large=1.5x realtime
            time_multipliers = {"tiny": 0.1, "base": 0.2, "small": 0.4, "medium": 0.8, "large": 1.5}
            estimated_time = int(audio_duration * time_multipliers.get(model_size, 0.5))
            print(f"   Estimated time: ~{estimated_time//60}:{estimated_time%60:02d} minutes")
        
        transcriber = Transcriber()
        result = transcriber.transcribe(audio_file, model_size=model_size)
        
        if result and 'text' in result:
            transcript_text = result['text']
            print(f"✅ Transcription complete! ({len(transcript_text)} characters)")
            
            # Save transcript
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_file = f"transcript_{timestamp}.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"Video: {info.get('title', 'Unknown')}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                f.write(transcript_text)
            print(f"📄 Transcript saved to: {transcript_file}")
            
            # Additional analysis if requested
            if action in ["2", "3"]:
                analyzer = TextAnalyzer()
                
                # Summarize
                print("\n📊 Generating summary...")
                summary = analyzer.summarize(transcript_text)
                print(f"\n📌 Summary:\n{summary}")
                
                # Full analysis
                if action == "3":
                    # Extract themes
                    print("\n🎯 Extracting key themes...")
                    themes = analyzer.extract_themes(transcript_text)
                    print("\n🔑 Key Themes:")
                    for i, theme in enumerate(themes, 1):
                        print(f"   {i}. {theme}")
                    
                    # Sentiment analysis
                    print("\n😊 Analyzing sentiment...")
                    sentiment = analyzer.analyze_sentiment(transcript_text)
                    print(f"\n💭 Sentiment Analysis:")
                    print(f"   Overall: {sentiment.get('overall', 'Unknown')}")
                    if 'scores' in sentiment:
                        print(f"   Positive: {sentiment['scores'].get('positive', 0):.2%}")
                        print(f"   Neutral: {sentiment['scores'].get('neutral', 0):.2%}")
                        print(f"   Negative: {sentiment['scores'].get('negative', 0):.2%}")
                
                # Save analysis
                if action in ["2", "3"]:
                    analysis_file = f"analysis_{timestamp}.json"
                    analysis_data = {
                        "title": info.get('title', 'Unknown'),
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "transcript": transcript_text,
                        "summary": summary if action in ["2", "3"] else None,
                        "themes": themes if action == "3" else None,
                        "sentiment": sentiment if action == "3" else None
                    }
                    with open(analysis_file, 'w', encoding='utf-8') as f:
                        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Full analysis saved to: {analysis_file}")
            
            print("\n✨ Done!")
            
        else:
            print("❌ Transcription failed")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()