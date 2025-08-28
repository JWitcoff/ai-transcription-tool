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
    print("  1️⃣  🎯 Quick URL Transcription ⭐ RECOMMENDED")
    print("       • Enter any video URL → Get complete analysis")
    print("       • Custom analysis prompts + organized file saving")
    print("       • Dead simple: one URL, complete results")
    print()
    print("  2️⃣  📁 Advanced File/URL Options")
    print("       • Manual quality selection")
    print("       • Local files and batch processing")
    print("       • Advanced configuration")
    print()
    print("  3️⃣  🎙️  Live Transcription")
    print("       • Real-time transcription from microphone")
    print("       • See text as you speak")
    print()
    print("  4️⃣  🌐 Web Interface")
    print("       • Browser-based interface with Streamlit")
    print("       • Download transcripts in multiple formats")
    print()
    print("  5️⃣  📊 Batch Processing")
    print("       • Process multiple files at once")
    print("       • Automated workflow")
    print()
    print("  6️⃣  📋 Template Analysis")
    print("       • Use pre-made analysis templates")
    print("       • Interview, Tutorial, Meeting notes, etc.")
    print("       • Professional structured output")
    print()
    print("  7️⃣  🗂️  Session Management")
    print("       • View past transcriptions")
    print("       • Search and organize sessions")
    print("       • Export session lists")
    print()
    print("  8️⃣  ⚙️  Settings & Help")
    print("       • Configure API keys")
    print("       • View documentation")
    print("       • System diagnostics")
    print()
    print("  0️⃣  ❌ Exit")
    print()
    print("─" * 60)

def quick_url_transcription():
    """Option 1: Quick URL transcription"""
    clear_screen()
    print("🎯 QUICK URL TRANSCRIPTION")
    print("=" * 60)
    
    # Import and run quick URL transcribe
    try:
        from quick_url_transcribe import main as quick_main
        quick_main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to return to menu...")

def advanced_file_url():
    """Option 2: Advanced file/URL options"""
    clear_screen()
    print("📁 ADVANCED FILE/URL TRANSCRIPTION")
    print("=" * 60)
    
    # Import and run simple_transcribe (the old complex version)
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

def template_analysis():
    """Option 6: Template-based analysis"""
    clear_screen()
    print("📋 TEMPLATE ANALYSIS MODE")
    print("=" * 60)
    
    try:
        from analysis_templates import AnalysisTemplates
        templates = AnalysisTemplates()
        
        print("\nAvailable Analysis Templates:")
        template_list = templates.list_templates()
        
        for i, template in enumerate(template_list, 1):
            print(f"\n{i:2}. {template['name']}")
            print(f"    {template['description']}")
            print(f"    Tags: {', '.join(template['tags'])}")
        
        choice = input(f"\nChoose template (1-{len(template_list)}) or 0 to cancel: ").strip()
        
        if choice == "0":
            return
        
        try:
            template_idx = int(choice) - 1
            if 0 <= template_idx < len(template_list):
                selected_template = template_list[template_idx]
                template_data = templates.get_template(selected_template['id'])
                
                print(f"\n✅ Selected: {selected_template['name']}")
                print("\nTemplate Preview:")
                print("-" * 40)
                preview = template_data['prompt'][:200] + "..." if len(template_data['prompt']) > 200 else template_data['prompt']
                print(preview)
                print("-" * 40)
                
                url = input("\n📺 Enter video URL: ").strip()
                if url:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    
                    print(f"\n🚀 Processing with {selected_template['name']} template...")
                    
                    # Use the template prompt with quick_url_transcribe logic
                    try:
                        from quick_url_transcribe import download_audio, transcribe_audio, save_results
                        from custom_analyzer import CustomAnalyzer
                        
                        audio_file, metadata = download_audio(url)
                        if audio_file:
                            try:
                                result = transcribe_audio(audio_file)
                                if result:
                                    # Use template prompt for analysis
                                    custom_analyzer = CustomAnalyzer()
                                    analysis_result = custom_analyzer.analyze_custom(
                                        result.get("text", ""),
                                        template_data['prompt'],
                                        metadata.get('title', '')
                                    )
                                    
                                    if analysis_result.get('success'):
                                        print("\n" + "=" * 60)
                                        print(f"📋 {selected_template['name']} Analysis")
                                        print("=" * 60)
                                        print(analysis_result['analysis'])
                                        print("=" * 60)
                                    
                                    # Save with template info
                                    analysis_result['template'] = selected_template['name']
                                    save_results(result, metadata, analysis_result)
                                    
                                    print(f"\n🎉 Template analysis complete!")
                                    
                                # Clean up
                                if os.path.exists(audio_file):
                                    os.unlink(audio_file)
                            except Exception as e:
                                print(f"❌ Processing failed: {e}")
                    except Exception as e:
                        print(f"❌ Template analysis failed: {e}")
            else:
                print("❌ Invalid template choice")
        except ValueError:
            print("❌ Please enter a valid number")
    except ImportError:
        print("❌ Template system not available")
    
    input("\nPress Enter to return to menu...")

def session_management():
    """Option 7: Session management and search"""
    clear_screen()
    print("🗂️  SESSION MANAGEMENT")
    print("=" * 60)
    
    try:
        from file_manager import FileManager
        file_manager = FileManager()
        
        while True:
            print("\nSession Management Options:")
            print("1. 📊 View session statistics")
            print("2. 🔍 Search sessions")
            print("3. 📋 List recent sessions")
            print("4. 📤 Export session list")
            print("5. 🧹 Cleanup incomplete sessions")
            print("0. ⬅️  Return to main menu")
            
            choice = input("\nChoose option (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                # Show statistics
                stats = file_manager.get_session_stats()
                print("\n📊 SESSION STATISTICS")
                print("=" * 40)
                print(f"Total Sessions: {stats['total_sessions']}")
                print(f"Recent Sessions (7 days): {stats['recent_sessions']}")
                
                if stats['sources']:
                    print("\nSources:")
                    for source, count in stats['sources'].items():
                        print(f"  {source}: {count}")
                
                if stats['tags']:
                    print("\nPopular Tags:")
                    sorted_tags = sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True)
                    for tag, count in sorted_tags[:5]:
                        print(f"  {tag}: {count}")
                
                if stats['analysis_types']:
                    print("\nAnalysis Types:")
                    for atype, count in stats['analysis_types'].items():
                        print(f"  {atype}: {count}")
                        
            elif choice == "2":
                # Search sessions
                print("\n🔍 Search Sessions")
                query = input("Search term (in title/prompt): ").strip()
                source = input("Filter by source (youtube/twitch/etc, or press Enter): ").strip()
                tag = input("Filter by tag (or press Enter): ").strip()
                
                results = file_manager.search_sessions(query, source, tag, limit=20)
                
                print(f"\n📋 Found {len(results)} session(s):")
                print("=" * 60)
                
                for i, session in enumerate(results[:10], 1):
                    video = session.get('video', {})
                    analysis = session.get('analysis', {})
                    print(f"\n{i:2}. {video.get('title', 'Unknown')}")
                    print(f"    Date: {session.get('created', '')[:10]}")
                    print(f"    Source: {video.get('source', 'Unknown')}")
                    if analysis.get('prompt'):
                        print(f"    Analysis: {analysis['prompt'][:60]}...")
                    print(f"    Folder: {session.get('folder_path', '')}")
                
                if len(results) > 10:
                    print(f"\n... and {len(results) - 10} more results")
                    
            elif choice == "3":
                # List recent sessions
                recent = file_manager.search_sessions(limit=10)
                print(f"\n📋 Recent Sessions:")
                print("=" * 60)
                
                for i, session in enumerate(recent, 1):
                    video = session.get('video', {})
                    print(f"\n{i:2}. {video.get('title', 'Unknown')}")
                    print(f"    Date: {session.get('created', '')[:19].replace('T', ' ')}")
                    print(f"    Source: {video.get('source', 'Unknown')}")
                    print(f"    Folder: {session.get('folder_path', '')}")
                    
            elif choice == "4":
                # Export session list
                print("\n📤 Export Session List")
                print("1. Markdown format")
                print("2. JSON format") 
                print("3. CSV format")
                
                export_choice = input("Choose format (1-3): ").strip()
                formats = {"1": "markdown", "2": "json", "3": "csv"}
                
                if export_choice in formats:
                    format_name = formats[export_choice]
                    export_data = file_manager.export_session_list(format_name)
                    
                    # Save to file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"session_list_{timestamp}.{format_name.replace('markdown', 'md')}"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(export_data)
                    
                    print(f"✅ Exported to: {filename}")
                else:
                    print("❌ Invalid format choice")
                    
            elif choice == "5":
                # Cleanup incomplete sessions
                print("\n🧹 Cleaning up incomplete sessions...")
                cleaned = file_manager.cleanup_incomplete_sessions()
                print(f"✅ Cleaned up {cleaned} incomplete session(s)")
            else:
                print("❌ Invalid choice")
            
            if choice != "0":
                input("\nPress Enter to continue...")
                print()  # Add spacing
                
    except ImportError:
        print("❌ Session management not available")
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
        
        choice = input("Enter your choice (0-8): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!\n")
            sys.exit(0)
        elif choice == "1":
            quick_url_transcription()
        elif choice == "2":
            advanced_file_url()
        elif choice == "3":
            live_transcription()
        elif choice == "4":
            web_interface()
        elif choice == "5":
            batch_processing()
        elif choice == "6":
            template_analysis()
        elif choice == "7":
            session_management()
        elif choice == "8":
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