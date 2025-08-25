#!/usr/bin/env python3
"""
Runner script for the Video Transcription Tool
Handles setup and launches the Streamlit app
"""

import os
import sys
import subprocess
from pathlib import Path

def check_and_install_dependencies():
    """Check if dependencies are installed and offer to install them"""
    try:
        import streamlit
        print("✅ Dependencies already installed")
        return True
    except ImportError:
        print("📦 Installing dependencies...")
        
        # Get the directory of this script
        script_dir = Path(__file__).parent
        requirements_file = script_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
        
        try:
            # Install requirements
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

def setup_environment():
    """Setup environment variables and configuration"""
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env file created")
            print("   Edit .env file to configure your settings")
        except Exception as e:
            print(f"⚠️  Could not create .env file: {e}")

def run_streamlit_app():
    """Launch the Streamlit application"""
    app_file = Path(__file__).parent / "app.py"
    
    if not app_file.exists():
        print("❌ app.py not found")
        return False
    
    print("🚀 Starting Video Transcription Tool...")
    print("   Opening in your default browser at http://localhost:8501")
    print("   Press Ctrl+C to stop the server")
    
    try:
        # Change to the app directory
        os.chdir(Path(__file__).parent)
        
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
        return True
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        return True
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False

def main():
    """Main entry point"""
    print("🎬 Video Transcription & Analysis Tool")
    print("=" * 50)
    
    # Step 1: Check and install dependencies
    if not check_and_install_dependencies():
        print("❌ Could not install dependencies")
        print("   Please run: pip install -r requirements.txt")
        return False
    
    # Step 2: Setup environment
    setup_environment()
    
    # Step 3: Run the app
    return run_streamlit_app()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)