#!/usr/bin/env python3
"""
Hybrid Transcriber - Real-time display with post-processing diarization
"""

import os
import tempfile
import subprocess
import threading
import time
from pathlib import Path

def run_hybrid_mode(stream_url: str, enable_diarization: bool = True):
    """
    Run hybrid mode: real-time transcription + saved file for diarization
    
    This mode:
    1. Shows real-time transcription as the stream plays
    2. Saves the full audio for post-processing with diarization
    3. Generates final transcript with speaker labels after stream ends
    """
    
    print("🎬 Hybrid Mode: Real-time + Diarization")
    print("=" * 50)
    
    # Step 1: Start real-time transcription
    print("▶️  Starting real-time transcription...")
    print(f"   Stream URL: {stream_url}")
    
    # Create temp file for saving audio
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_audio_path = temp_audio.name
    temp_audio.close()
    
    # Start downloading audio in background while transcribing
    download_thread = threading.Thread(
        target=download_audio_background,
        args=(stream_url, temp_audio_path),
        daemon=True
    )
    download_thread.start()
    
    # Run live transcription app
    print("\n🔴 Live transcription interface starting...")
    print("   Open browser at: http://localhost:8501")
    print("   Press Ctrl+C when done to process with diarization\n")
    
    try:
        subprocess.run([
            'streamlit', 'run', 'live_transcription_app.py',
            '--', '--url', stream_url
        ])
    except KeyboardInterrupt:
        print("\n⏹️  Stopping live transcription...")
    
    # Step 2: Process saved audio with diarization
    if enable_diarization and os.path.exists(temp_audio_path):
        print("\n🎯 Processing with speaker diarization...")
        print("   This may take a few minutes...")
        
        # Use the original audio_transcriber with diarization
        from audio_transcriber import AudioTranscriber
        
        transcriber = AudioTranscriber(
            model_size="base",
            enable_diarization=True
        )
        
        result = transcriber.transcribe_from_file(
            temp_audio_path,
            include_timestamps=True
        )
        
        # Save diarized transcript
        output_file = f"diarized_transcript_{int(time.time())}.txt"
        transcriber.export_transcription(result, output_file, format="txt")
        
        print(f"\n✅ Diarized transcript saved to: {output_file}")
        
        # Display speaker statistics
        if result.get("has_diarization"):
            speakers = {}
            for segment in result.get("segments", []):
                speaker = segment.get("speaker", "Unknown")
                speakers[speaker] = speakers.get(speaker, 0) + 1
            
            print("\n📊 Speaker Statistics:")
            for speaker, count in speakers.items():
                print(f"   {speaker}: {count} segments")
    
    # Cleanup
    try:
        os.unlink(temp_audio_path)
    except:
        pass
    
    print("\n✅ Hybrid processing complete!")

def download_audio_background(url: str, output_path: str):
    """Download audio in background for post-processing"""
    try:
        import yt_dlp
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
    except Exception as e:
        print(f"Background download error: {e}")

def main():
    print("🎥 Hybrid Transcription Mode")
    print("=" * 50)
    print("\nThis mode provides:")
    print("✅ Real-time transcription display")
    print("✅ Full speaker diarization (post-processing)")
    print("✅ Best of both worlds!\n")
    
    stream_url = input("Enter stream URL: ").strip()
    
    if not stream_url:
        print("❌ No URL provided")
        return
    
    enable_diarization = input("Enable speaker diarization? (y/N): ").strip().lower() == 'y'
    
    run_hybrid_mode(stream_url, enable_diarization)

if __name__ == "__main__":
    main()