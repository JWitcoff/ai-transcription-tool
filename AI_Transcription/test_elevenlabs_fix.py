#!/usr/bin/env python3
"""
Test script to verify the ElevenLabs file upload fix
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def create_test_audio():
    """Create a small test audio file"""
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "test_audio.wav")
    
    # Create a 3-second test audio file using ffmpeg
    cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3',
        '-ar', '16000', '-ac', '1', test_file, '-y'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"✅ Created test audio file: {test_file}")
        return test_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create test audio: {e}")
        return None
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        return None

def test_elevenlabs_upload():
    """Test the ElevenLabs file upload with the fix"""
    
    # Check for API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('ELEVENLABS_API_KEY') or os.getenv('ELEVENLABS_SCRIBE_KEY')
    if not api_key:
        print("❌ No ElevenLabs API key found in .env file")
        print("   Please set ELEVENLABS_API_KEY or ELEVENLABS_SCRIBE_KEY")
        return False
    
    print("🔧 Testing ElevenLabs file upload fix...")
    print("=" * 60)
    
    # Create test audio
    test_file = create_test_audio()
    if not test_file:
        return False
    
    try:
        # Import the fixed ScribeClient
        from elevenlabs_scribe import ScribeClient
        
        # Initialize client
        client = ScribeClient()
        print("\n📤 Uploading test file to ElevenLabs...")
        
        # Test the upload with minimal settings
        result = client.transcribe_file(
            test_file,
            diarize=False,  # Simple test without diarization
            num_speakers=None,
            diarization_threshold=None,
            use_multi_channel=False
        )
        
        if result and 'text' in result:
            print("\n✅ SUCCESS! File upload is working correctly!")
            print(f"   Transcribed text: {result['text'][:100]}...")
            return True
        else:
            print("\n❌ Upload succeeded but unexpected response format")
            print(f"   Response keys: {list(result.keys()) if result else 'None'}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    finally:
        # Clean up test file
        if test_file and os.path.exists(test_file):
            os.unlink(test_file)
            test_dir = os.path.dirname(test_file)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
            print("\n🧹 Cleaned up test file")

def test_with_real_file():
    """Test with a real audio file if provided"""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"\n📁 Testing with real file: {file_path}")
        print("=" * 60)
        
        try:
            from elevenlabs_scribe import ScribeClient
            
            client = ScribeClient()
            print("📤 Uploading to ElevenLabs...")
            
            result = client.transcribe_file(
                file_path,
                diarize=True,  # Test with diarization
                num_speakers=None,
                diarization_threshold=None,
                use_multi_channel=False
            )
            
            if result and 'text' in result:
                print("\n✅ SUCCESS! File processed correctly!")
                print(f"   Text length: {len(result['text'])} characters")
                if 'words' in result:
                    print(f"   Words: {len(result['words'])}")
                return True
            else:
                print("\n❌ Unexpected response format")
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False

if __name__ == "__main__":
    print("🧪 ElevenLabs File Upload Fix Test")
    print("=" * 60)
    
    # Test with synthetic audio first
    success = test_elevenlabs_upload()
    
    # If a file path was provided, test with that too
    if len(sys.argv) > 1:
        success = test_with_real_file() and success
    
    if success:
        print("\n🎉 All tests passed! The fix is working correctly.")
        print("\nYou can now use AI_Transcription with local files without errors!")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)