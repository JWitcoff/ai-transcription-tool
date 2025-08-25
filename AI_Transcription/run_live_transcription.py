#!/usr/bin/env python3
"""
Live Video Stream Transcription Tool
====================================

A powerful tool that captures audio from live video streams, transcribes speech to text in real-time,
and extracts key themes and insights from the content.

Key Features:
- Real-time audio capture from live streams (YouTube, Twitch, etc.)
- Chunked transcription processing for low latency
- Live theme extraction and sentiment analysis
- Web-based interface with real-time updates
- Export functionality for transcripts and analysis

Performance Optimizations:
- Uses faster-whisper for improved transcription speed
- Chunked audio processing (3-second chunks with 1-second overlap)
- Background threading for non-blocking operations
- GPU acceleration when available
- Smart buffering to prevent memory issues

Usage:
    python run_live_transcription.py

Requirements:
    See requirements_optimized.txt for dependencies
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'whisper',
        'torch',
        'numpy',
        'yt_dlp',
        'ffmpeg'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'ffmpeg':
                # Check if ffmpeg is available in system PATH
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, check=True)
            else:
                __import__(package.replace('-', '_'))
        except (ImportError, subprocess.CalledProcessError, FileNotFoundError):
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("📦 Installing optimized dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements_optimized.txt"
    
    if requirements_file.exists():
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    else:
        print("❌ requirements_optimized.txt not found!")
        return False
    
    return True

def check_system_requirements():
    """Check system-level requirements"""
    print("\n🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Extract ffmpeg version
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
        else:
            print("❌ ffmpeg not working properly")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg not found in system PATH")
        print("   Please install ffmpeg:")
        print("   - macOS: brew install ffmpeg")
        print("   - Ubuntu: sudo apt install ffmpeg")
        print("   - Windows: Download from https://ffmpeg.org/")
        return False
    
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name()
            print(f"✅ CUDA GPU detected: {gpu_name}")
            print("   This will significantly improve transcription speed!")
        else:
            print("ℹ️  No CUDA GPU detected, using CPU")
            print("   Consider using a GPU for better real-time performance")
    except ImportError:
        print("ℹ️  PyTorch not installed yet")
    
    return True

def run_application():
    """Run the live transcription application"""
    app_file = Path(__file__).parent / "live_transcription_app.py"
    
    if not app_file.exists():
        print("❌ live_transcription_app.py not found!")
        return False
    
    try:
        print("\n🚀 Starting Live Video Transcription Tool...")
        print("   Open your browser to the URL shown below")
        print("   Press Ctrl+C to stop the application")
        
        # Run streamlit app
        subprocess.run([
            'streamlit', 'run', str(app_file),
            '--server.address', '0.0.0.0',
            '--server.port', '8501',
            '--browser.gatherUsageStats', 'false'
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install dependencies first.")
        return False
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("=" * 60)
    print("🎥 Live Video Stream Transcription & Analysis Tool")
    print("=" * 60)
    
    # Check system requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met. Please fix the issues above.")
        sys.exit(1)
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"\n📋 Missing dependencies: {', '.join(missing)}")
        
        response = input("Would you like to install them now? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            if not install_dependencies():
                print("❌ Failed to install dependencies. Please install manually.")
                sys.exit(1)
        else:
            print("Please install the missing dependencies and try again.")
            print(f"Run: pip install -r requirements_optimized.txt")
            sys.exit(1)
    else:
        print("✅ All dependencies are installed")
    
    # Run the application
    if not run_application():
        sys.exit(1)

if __name__ == "__main__":
    main()