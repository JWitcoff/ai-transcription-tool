#!/usr/bin/env python3
"""
AI Transcription Tool - Unified Entry Point
A comprehensive tool for audio/video transcription with multiple modes
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# ASCII Art Banner
BANNER = """
╔═══════════════════════════════════════════════════════════╗
║                 🎬 AI TRANSCRIPTION TOOL 🎬               ║
║           Powered by Whisper & Speaker Diarization        ║
╚═══════════════════════════════════════════════════════════╝
"""

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    """Display the main menu"""
    print(BANNER)
    print("Choose transcription mode:\n")
    print("  1️⃣  📁 Transcribe File/URL")
    print("       • YouTube videos, local audio/video files")
    print("       • Speaker identification available")
    print()
    print("  2️⃣  🎙️  Live Transcription")
    print("       • Real-time transcription from microphone")
    print("       • See text as you speak")
    print()
    print("  3️⃣  🌐 Web Interface")
    print("       • Browser-based interface with Streamlit")
    print("       • Download transcripts in multiple formats")
    print()
    print("  4️⃣  🚀 Quick Transcribe")
    print("       • Fastest mode for quick results")
    print("       • Minimal configuration")
    print()
    print("  5️⃣  📊 Batch Processing")
    print("       • Process multiple files at once")
    print("       • Automated workflow")
    print()
    print("  6️⃣  ⚙️  Settings & Help")
    print("       • Configure API keys")
    print("       • View documentation")
    print()
    print("  0️⃣  ❌ Exit")
    print()
    print("─" * 60)

def transcribe_file_or_url():
    """Option 1: Transcribe a file or URL"""
    clear_screen()
    print("📁 FILE/URL TRANSCRIPTION MODE")
    print("=" * 60)
    
    # Import and run simple_transcribe
    try:
        from simple_transcribe import main as simple_main
        simple_main()
    except Exception as e:
        print(f"❌ Error: {e}")
        input("\nPress Enter to return to menu...")

def live_transcription():
    """Option 2: Live transcription from microphone"""
    clear_screen()
    print("🎙️ LIVE TRANSCRIPTION MODE")
    print("=" * 60)
    print("\nStarting live transcription...")
    print("Speak into your microphone. Press Ctrl+C to stop.\n")
    
    try:
        from live_cli import main as live_main
        live_main()
    except KeyboardInterrupt:
        print("\n\n✅ Live transcription stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPress Enter to return to menu...")

def web_interface():
    """Option 3: Launch Streamlit web interface"""
    clear_screen()
    print("🌐 WEB INTERFACE MODE")
    print("=" * 60)
    print("\n🚀 Launching web interface...")
    print("   • Opening in your browser at http://localhost:8501")
    print("   • Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n✅ Web server stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPress Enter to return to menu...")

def quick_transcribe():
    """Option 4: Quick transcribe with minimal config"""
    clear_screen()
    print("🚀 QUICK TRANSCRIBE MODE")
    print("=" * 60)
    
    print("\nInput type:")
    print("1. YouTube URL")
    print("2. Local file")
    
    choice = input("\nChoice (1-2): ").strip()
    
    if choice == "1":
        url = input("Enter YouTube URL: ").strip()
        if url:
            print("\n⏳ Processing... (using fast mode)")
            try:
                from simple_transcribe import transcribe_url
                transcribe_url(url)
            except Exception as e:
                print(f"❌ Error: {e}")
    elif choice == "2":
        file_path = input("Enter file path: ").strip()
        if file_path and os.path.exists(file_path):
            print("\n⏳ Processing... (using fast mode)")
            try:
                from simple_transcribe import transcribe_file
                transcribe_file(file_path)
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("❌ File not found")
    
    input("\nPress Enter to return to menu...")

def batch_processing():
    """Option 5: Batch process multiple files"""
    clear_screen()
    print("📊 BATCH PROCESSING MODE")
    print("=" * 60)
    
    print("\nEnter directory path containing audio/video files")
    print("(or press Enter to use current directory)")
    
    dir_path = input("\nDirectory path: ").strip() or "."
    
    if not os.path.isdir(dir_path):
        print(f"❌ Directory not found: {dir_path}")
        input("\nPress Enter to return to menu...")
        return
    
    # Find audio/video files
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.avi', '.mov', '.mkv', '.webm'}
    files = []
    
    for file in Path(dir_path).iterdir():
        if file.suffix.lower() in audio_extensions:
            files.append(file)
    
    if not files:
        print(f"❌ No audio/video files found in {dir_path}")
        input("\nPress Enter to return to menu...")
        return
    
    print(f"\n✅ Found {len(files)} file(s):")
    for i, file in enumerate(files[:10], 1):  # Show first 10
        print(f"   {i}. {file.name}")
    if len(files) > 10:
        print(f"   ... and {len(files) - 10} more")
    
    if input("\nProcess all files? (y/n): ").strip().lower() == 'y':
        print("\nChoose quality:")
        print("1. Fast (tiny model)")
        print("2. Balanced (base model)")
        print("3. Accurate (with speaker identification)")
        
        quality = input("\nChoice (1-3): ").strip()
        model_options = {"1": ("tiny", False), "2": ("base", False), "3": ("base", True)}
        model_size, enable_diarization = model_options.get(quality, ("base", False))
        
        print(f"\n⏳ Processing {len(files)} files...")
        
        try:
            from audio_transcriber import AudioTranscriber
            transcriber = AudioTranscriber(model_size=model_size, enable_diarization=enable_diarization)
            
            for i, file in enumerate(files, 1):
                print(f"\n[{i}/{len(files)}] Processing: {file.name}")
                try:
                    result = transcriber.transcribe_from_file(str(file))
                    
                    # Save to transcripts folder
                    output_dir = Path("transcripts")
                    output_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = output_dir / f"{file.stem}_transcript_{timestamp}.txt"
                    
                    transcriber.export_transcription(result, str(output_file), "txt")
                    print(f"   ✅ Saved: {output_file.name}")
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
            
            print(f"\n✅ Batch processing complete!")
            print(f"   Transcripts saved in: transcripts/")
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
    
    input("\nPress Enter to return to menu...")

def settings_and_help():
    """Option 6: Settings and help"""
    clear_screen()
    print("⚙️ SETTINGS & HELP")
    print("=" * 60)
    
    print("\n1. Configure API Keys")
    print("2. Test Installation")
    print("3. View Documentation")
    print("4. About")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "1":
        print("\n🔑 API Key Configuration")
        print("-" * 40)
        print("\nCreate a .env file with your API keys:")
        print("  OPENAI_API_KEY=your_key_here")
        print("\nCurrent status:")
        
        env_file = Path(".env")
        if env_file.exists():
            print("  ✅ .env file exists")
        else:
            print("  ❌ .env file not found")
            if input("\nCreate .env file now? (y/n): ").strip().lower() == 'y':
                api_key = input("Enter OpenAI API key (or press Enter to skip): ").strip()
                with open(".env", "w") as f:
                    f.write(f"OPENAI_API_KEY={api_key}\n")
                print("✅ .env file created")
    
    elif choice == "2":
        print("\n🧪 Testing Installation")
        print("-" * 40)
        try:
            import whisper
            print("✅ Whisper: Installed")
        except ImportError:
            print("❌ Whisper: Not installed")
        
        try:
            from pyannote.audio import Pipeline
            print("✅ Pyannote (Diarization): Installed")
        except ImportError:
            print("❌ Pyannote (Diarization): Not installed")
        
        try:
            import streamlit
            print("✅ Streamlit: Installed")
        except ImportError:
            print("❌ Streamlit: Not installed")
        
        try:
            import openai
            print("✅ OpenAI: Installed")
        except ImportError:
            print("❌ OpenAI: Not installed")
    
    elif choice == "3":
        print("\n📚 Documentation")
        print("-" * 40)
        print("\n🎯 Quick Start:")
        print("  1. Choose option 1 for file/URL transcription")
        print("  2. Select quality (3 or 4 for speaker identification)")
        print("  3. Transcripts save to 'transcripts/' folder")
        print("\n💡 Tips:")
        print("  • First run downloads AI models (~1-2GB)")
        print("  • Speaker diarization requires pyannote.audio")
        print("  • Use option 4 for quick transcriptions")
        print("\n🔗 More info: https://github.com/JWitcoff/ai-transcription-tool")
    
    elif choice == "4":
        print("\n📌 About")
        print("-" * 40)
        print("AI Transcription Tool v1.0")
        print("Powered by:")
        print("  • OpenAI Whisper - Speech recognition")
        print("  • Pyannote - Speaker diarization")
        print("  • Streamlit - Web interface")
        print("\n© 2024 - Built with Claude Code")
    
    input("\nPress Enter to return to menu...")

def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    
    try:
        import streamlit
    except ImportError:
        missing.append("streamlit")
    
    if missing:
        print("⚠️  Missing dependencies detected!")
        print(f"   Required: {', '.join(missing)}")
        if input("\nInstall now? (y/n): ").strip().lower() == 'y':
            print("\n📦 Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed. Please restart the program.")
            sys.exit(0)
        return False
    return True

def main():
    """Main entry point"""
    # Initial setup
    clear_screen()
    
    # Check dependencies on first run
    if not check_dependencies():
        print("\n⚠️  Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    while True:
        clear_screen()
        print_menu()
        
        choice = input("Enter your choice (0-6): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!\n")
            sys.exit(0)
        elif choice == "1":
            transcribe_file_or_url()
        elif choice == "2":
            live_transcription()
        elif choice == "3":
            web_interface()
        elif choice == "4":
            quick_transcribe()
        elif choice == "5":
            batch_processing()
        elif choice == "6":
            settings_and_help()
        else:
            print("❌ Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)