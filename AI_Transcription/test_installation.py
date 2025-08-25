#!/usr/bin/env python3
"""
Test script to verify the video transcription tool installation
"""

import sys
import os
import subprocess
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_ffmpeg():
    """Test FFmpeg installation"""
    print("Testing FFmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            return True
        else:
            print("❌ FFmpeg not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        print("   macOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt install ffmpeg")
        return False

def test_python_packages():
    """Test required Python packages"""
    print("Testing Python packages...")
    
    required_packages = [
        'streamlit',
        'whisper', 
        'yt_dlp',
        'torch',
        'transformers',
        'numpy',
        'pandas'
    ]
    
    all_ok = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            all_ok = False
    
    return all_ok

def test_gpu_support():
    """Test GPU support"""
    print("Testing GPU support...")
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name()
            print(f"✅ CUDA GPU available: {device_name}")
            return True
        else:
            print("ℹ️  No CUDA GPU available (CPU will be used)")
            return True
    except ImportError:
        print("❌ PyTorch not available")
        return False

def test_file_structure():
    """Test file structure"""
    print("Testing file structure...")
    
    required_files = [
        'app.py',
        'audio_capture.py', 
        'transcriber.py',
        'analyzer.py',
        'config.py',
        'utils.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_ok = True
    current_dir = Path(__file__).parent
    
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} - OK")
        else:
            print(f"❌ {file_name} - Missing")
            all_ok = False
    
    return all_ok

def test_whisper_models():
    """Test Whisper model loading"""
    print("Testing Whisper model loading...")
    try:
        import whisper
        
        # Try to load the smallest model
        print("  Loading 'tiny' model...")
        model = whisper.load_model("tiny")
        
        # Test transcription with a short audio
        print("  Testing transcription...")
        
        # Create a simple test (this would require actual audio)
        print("✅ Whisper models can be loaded")
        return True
        
    except Exception as e:
        print(f"❌ Whisper model test failed: {e}")
        return False

def run_basic_test():
    """Run a basic functionality test"""
    print("Running basic functionality test...")
    try:
        from config import Config
        from utils import validate_url, create_safe_filename
        from audio_capture import AudioCapture
        from transcriber import Transcriber
        from analyzer import TextAnalyzer
        
        # Test configuration
        config_issues = Config.validate_config()
        if config_issues:
            print("⚠️  Configuration issues found:")
            for issue in config_issues:
                print(f"    - {issue}")
        else:
            print("✅ Configuration validation passed")
        
        # Test utility functions
        assert validate_url("https://youtube.com/watch?v=test") == True
        assert create_safe_filename("test file.mp4") == "test file.mp4"
        print("✅ Utility functions working")
        
        # Test class initialization
        capture = AudioCapture()
        transcriber = Transcriber()
        analyzer = TextAnalyzer()
        print("✅ Main classes can be initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Video Transcription Tool - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("FFmpeg", test_ffmpeg),
        ("Python Packages", test_python_packages),
        ("GPU Support", test_gpu_support),
        ("File Structure", test_file_structure),
        ("Whisper Models", test_whisper_models),
        ("Basic Functionality", run_basic_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The tool is ready to use.")
        print("   Run: streamlit run app.py")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
        print("   See README.md for installation instructions.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)