#!/usr/bin/env python3
"""
Test script for new transcription architecture.
Tests the clean interface design and provider system.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all new architecture components can be imported."""
    print("🧪 Testing new architecture imports...")

    try:
        from transcription import TranscriptionService, TranscriptionProvider
        from transcription.providers import ElevenLabsProvider, WhisperProvider
        from transcription.config import TranscriptionConfig
        from transcription.errors import TranscriptionError
        from transcription.ui import CleanUI
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration system."""
    print("\n🧪 Testing configuration system...")

    try:
        from transcription.config import TranscriptionConfig

        # Test environment-based config
        config = TranscriptionConfig.from_env()
        print(f"✅ Environment config loaded: {config.whisper.model_size}")

        # Test dictionary config
        config_dict = {
            'whisper': {'model_size': 'small'},
            'prefer_elevenlabs': True
        }
        config = TranscriptionConfig.from_dict(config_dict)
        print(f"✅ Dictionary config loaded: {config.whisper.model_size}")

        # Test config conversion
        config_dict = config.to_dict()
        print(f"✅ Config serialization works")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_providers():
    """Test provider system."""
    print("\n🧪 Testing provider system...")

    try:
        from transcription.providers import ElevenLabsProvider, WhisperProvider

        # Test ElevenLabs provider
        elevenlabs = ElevenLabsProvider()
        print(f"✅ ElevenLabs provider created: {elevenlabs.name}")
        print(f"   Available: {elevenlabs.is_available()}")
        print(f"   Supported formats: {len(elevenlabs.get_supported_formats())} formats")

        # Test Whisper provider
        whisper = WhisperProvider()
        print(f"✅ Whisper provider created: {whisper.name}")
        print(f"   Available: {whisper.is_available()}")
        print(f"   Supported formats: {len(whisper.get_supported_formats())} formats")

        return True
    except Exception as e:
        print(f"❌ Provider test failed: {e}")
        return False

def test_service():
    """Test main transcription service."""
    print("\n🧪 Testing transcription service...")

    try:
        from transcription import TranscriptionService

        # Test service creation
        service = TranscriptionService()
        print(f"✅ Service created")

        # Test provider info
        providers = service.get_available_providers()
        print(f"✅ Available providers: {providers}")

        provider_info = service.get_provider_info()
        print(f"✅ Provider info retrieved: {list(provider_info.keys())}")

        return True
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

def test_ui():
    """Test UI components."""
    print("\n🧪 Testing UI components...")

    try:
        from transcription.ui import CleanUI, OutputSuppressor

        # Test CleanUI
        ui = CleanUI()
        print(f"✅ CleanUI created")

        # Test OutputSuppressor
        with OutputSuppressor():
            pass
        print(f"✅ OutputSuppressor works")

        return True
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        return False

def test_error_hierarchy():
    """Test error handling system."""
    print("\n🧪 Testing error system...")

    try:
        from transcription.errors import (
            TranscriptionError, ProviderError, APIError,
            ConfigurationError, ValidationError
        )

        # Test error creation
        error = TranscriptionError("Test error", provider="TestProvider")
        print(f"✅ TranscriptionError created: {error}")

        # Test inheritance
        api_error = APIError("API failed", provider="TestAPI", status_code=400)
        print(f"✅ APIError created: {api_error}")
        print(f"✅ Is TranscriptionError: {isinstance(api_error, TranscriptionError)}")

        return True
    except Exception as e:
        print(f"❌ Error test failed: {e}")
        return False

def main():
    """Run all architecture tests."""
    print("🏗️  TESTING NEW TRANSCRIPTION ARCHITECTURE")
    print("=" * 60)

    tests = [
        test_imports,
        test_configuration,
        test_providers,
        test_service,
        test_ui,
        test_error_hierarchy
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Architecture is working!")
        return 0
    else:
        print("⚠️  Some tests failed - check implementation")
        return 1

if __name__ == "__main__":
    sys.exit(main())