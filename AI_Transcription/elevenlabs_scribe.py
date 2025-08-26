"""
ElevenLabs Scribe API client with proper diarization and multi-channel support
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()

@dataclass
class Word:
    """Represents a single word from transcription"""
    text: str
    start: float
    end: float
    type: Optional[str] = None
    speaker_id: Optional[str] = None
    channel_index: Optional[int] = None

@dataclass
class Segment:
    """Represents a continuous segment of speech from one speaker"""
    speaker_id: str
    start: float
    end: float
    text: str
    channel_index: Optional[int] = None

class ScribeParseError(Exception):
    """Raised when response parsing fails"""
    pass

class ScribeClient:
    """ElevenLabs Scribe API client with proper request/response handling"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.elevenlabs.io"):
        """
        Initialize Scribe client
        
        Args:
            api_key: ElevenLabs API key (if not provided, loads from env)
            base_url: API base URL
        """
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY') or os.getenv('ELEVENLABS_SCRIBE_KEY')
        if not self.api_key:
            raise ValueError("ElevenLabs API key not found. Set ELEVENLABS_API_KEY in .env file")
        
        self.base_url = base_url
        self.headers = {
            "xi-api-key": self.api_key,
        }
    
    def _build_payload(self, 
                      diarize: bool,
                      num_speakers: Optional[int],
                      diarization_threshold: Optional[float],
                      use_multi_channel: bool,
                      timestamps_granularity: str = "word") -> Dict[str, Any]:
        """
        Build API payload with proper validation.
        
        CRITICAL: diarization_threshold ONLY when diarize=True AND num_speakers=None
        Otherwise API returns 422 error.
        """
        payload = {
            "model_id": "scribe_v1",
            "timestamps_granularity": timestamps_granularity,
            "diarize": diarize
        }
        
        # Multi-channel handling
        if use_multi_channel:
            payload["use_multi_channel"] = True
            # NOTE: When using multi-channel, typically set diarize=False
            # as speakers are separated by channel_index
            if diarize:
                print("⚠️  Warning: diarize=True with multi-channel is usually unnecessary")
        
        # Set num_speakers if provided
        if num_speakers is not None:
            payload["num_speakers"] = num_speakers
        
        # CRITICAL: Only set threshold when diarize=True AND num_speakers=None
        if diarize and num_speakers is None and diarization_threshold is not None:
            payload["diarization_threshold"] = diarization_threshold
        elif diarization_threshold is not None:
            print(f"⚠️  Ignoring diarization_threshold (requires diarize=True and num_speakers=None)")
        
        return payload
    
    def validate_audio_size(self, audio_url: Optional[str] = None, file_path: Optional[str] = None) -> bool:
        """
        Check audio size against API limits.
        - cloud_storage_url: max 2 GB
        - file upload: max 3 GB
        
        Returns True if within limits, raises ValueError if too large.
        """
        MAX_CLOUD_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
        MAX_UPLOAD_SIZE = 3 * 1024 * 1024 * 1024  # 3 GB
        
        if audio_url:
            # For cloud URLs, attempt HEAD request to check Content-Length
            try:
                response = requests.head(audio_url, timeout=10)
                size = int(response.headers.get('Content-Length', 0))
                if size > MAX_CLOUD_SIZE:
                    raise ValueError(f"Audio file too large: {size/1e9:.1f}GB > 2GB limit for cloud_storage_url")
                elif size > 1.5 * 1024 * 1024 * 1024:  # Warn at 1.5GB
                    print(f"⚠️  Large file: {size/1e9:.1f}GB (limit is 2GB)")
            except requests.RequestException:
                print("⚠️  Could not verify file size for cloud URL")
        
        if file_path and os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size > MAX_UPLOAD_SIZE:
                raise ValueError(f"Audio file too large: {size/1e9:.1f}GB > 3GB limit for file upload")
            elif size > 2 * 1024 * 1024 * 1024:  # Warn at 2GB
                print(f"⚠️  Large file: {size/1e9:.1f}GB (limit is 3GB)")
        
        return True
    
    def _make_request_with_retry(self, endpoint: str, json_payload: Optional[Dict] = None,
                                 data_payload: Optional[Dict] = None, files: Optional[Dict] = None,
                                 max_retries: int = 3) -> requests.Response:
        """
        Make API request with exponential backoff retry logic.
        
        Args:
            endpoint: API endpoint URL
            json_payload: JSON body for cloud_storage_url
            data_payload: Form data for file upload
            files: Files dict for multipart upload
            max_retries: Maximum retry attempts
        
        Returns:
            Response object
        """
        for attempt in range(max_retries):
            try:
                if json_payload:
                    # JSON request (cloud_storage_url)
                    response = requests.post(
                        endpoint,
                        headers={**self.headers, "Content-Type": "application/json"},
                        json=json_payload,
                        timeout=300  # 5 minutes
                    )
                else:
                    # Multipart form request (file upload)
                    response = requests.post(
                        endpoint,
                        headers=self.headers,
                        data=data_payload,
                        files=files,
                        timeout=300
                    )
                
                # Check for rate limit or server errors
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0.2, 0.5)
                        print(f"⚠️  Got {response.status_code}, retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                
                return response
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0.2, 0.5)
                    print(f"⚠️  Request failed: {e}, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise
        
        return response
    
    def transcribe_url(self, audio_url: str, *,
                      diarize: bool = True,
                      num_speakers: Optional[int] = None,
                      diarization_threshold: Optional[float] = None,
                      use_multi_channel: bool = False) -> Dict:
        """
        Call Scribe with a public HTTPS audio URL and return parsed JSON.
        
        Args:
            audio_url: Public HTTPS URL to audio file
            diarize: Enable speaker diarization
            num_speakers: Maximum number of speakers (1-32)
            diarization_threshold: Speaker separation threshold (0.18-0.32)
            use_multi_channel: Process multi-channel audio separately
        
        Returns:
            Raw API response as dict
        """
        # Validate size
        self.validate_audio_size(audio_url=audio_url)
        
        endpoint = f"{self.base_url}/v1/speech-to-text"
        
        # Build payload
        payload = self._build_payload(diarize, num_speakers, diarization_threshold, 
                                     use_multi_channel)
        payload["cloud_storage_url"] = audio_url
        
        print(f"🚀 Sending to ElevenLabs Scribe (cloud URL)...")
        print(f"   • Diarization: {'ON' if diarize else 'OFF'}")
        if use_multi_channel:
            print(f"   • Multi-channel: ON (speaker by channel)")
        print(f"   • URL: {audio_url[:50]}...")
        
        try:
            response = self._make_request_with_retry(endpoint, json_payload=payload)
            
            if response.status_code == 422:
                error_detail = response.json().get('detail', 'Unknown validation error')
                raise ValueError(f"API validation error (422): {error_detail}")
            
            response.raise_for_status()
            result = response.json()
            
            # Log response structure for debugging
            if not result:
                raise ScribeParseError("Empty response from API")
            
            print(f"✅ Transcription received")
            if "words" in result:
                print(f"   • Words: {len(result['words'])}")
            elif "transcripts" in result:
                print(f"   • Channels: {len(result['transcripts'])}")
            
            return result
            
        except requests.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if hasattr(e.response, 'text'):
                preview = e.response.text[:1000]
                error_msg += f" - {preview}"
            raise Exception(f"ElevenLabs API error: {error_msg}")
    
    def transcribe_file(self, path: str, **kwargs) -> Dict:
        """
        Multipart upload version; same options as transcribe_url.
        
        Args:
            path: Path to local audio file
            **kwargs: Same as transcribe_url
        
        Returns:
            Raw API response as dict
        """
        # Validate size
        self.validate_audio_size(file_path=path)
        
        endpoint = f"{self.base_url}/v1/speech-to-text"
        
        # Build payload - note: multipart uses strings for booleans
        payload = self._build_payload(
            kwargs.get('diarize', True),
            kwargs.get('num_speakers'),
            kwargs.get('diarization_threshold'),
            kwargs.get('use_multi_channel', False)
        )
        
        # Convert booleans to strings for multipart
        data_payload = {
            "model_id": payload["model_id"],
            "timestamps_granularity": payload["timestamps_granularity"],
            "diarize": str(payload["diarize"]).lower()
        }
        
        if "use_multi_channel" in payload:
            data_payload["use_multi_channel"] = str(payload["use_multi_channel"]).lower()
        
        if "num_speakers" in payload:
            data_payload["num_speakers"] = str(payload["num_speakers"])
        
        if "diarization_threshold" in payload:
            data_payload["diarization_threshold"] = str(payload["diarization_threshold"])
        
        print(f"🚀 Uploading to ElevenLabs Scribe (file upload)...")
        print(f"   • File: {os.path.basename(path)}")
        print(f"   • Size: {os.path.getsize(path)/1e6:.1f}MB")
        
        try:
            with open(path, 'rb') as audio_file:
                files = {"file": audio_file}
                response = self._make_request_with_retry(endpoint, data_payload=data_payload, 
                                                        files=files)
            
            if response.status_code == 422:
                error_detail = response.json().get('detail', 'Unknown validation error')
                raise ValueError(f"API validation error (422): {error_detail}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if hasattr(e.response, 'text'):
                preview = e.response.text[:1000]
                error_msg += f" - {preview}"
            raise Exception(f"ElevenLabs API error: {error_msg}")

def parse_words_from_response(resp: Dict) -> List[Word]:
    """
    Parse words from ElevenLabs response.
    
    Two response structures:
    1. Single-channel/diarized: words at top level with speaker_id
    2. Multi-channel: transcripts array with channel_index per word
    
    Multi-channel note: When use_multi_channel=True, speakers are 
    typically identified by channel_index, not speaker_id.
    
    Example input (single-channel):
    {
        "words": [
            {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "speaker_1"}
        ]
    }
    
    Example input (multi-channel):
    {
        "transcripts": [
            {
                "channel_index": 0,
                "words": [{"text": "Hello", "start": 0.0, "end": 0.5}]
            }
        ]
    }
    
    Returns:
        List of Word objects with all metadata preserved
    """
    words = []
    
    # Multi-channel response
    if "transcripts" in resp:
        for transcript in resp["transcripts"]:
            channel_idx = transcript.get("channel_index", 0)
            for word_data in transcript.get("words", []):
                # Only include actual words, not audio events
                if word_data.get("type") in [None, "word"]:
                    words.append(Word(
                        text=word_data.get("text", ""),
                        start=word_data.get("start", 0.0),
                        end=word_data.get("end", 0.0),
                        type=word_data.get("type"),
                        speaker_id=word_data.get("speaker_id"),  # Usually None in multi-channel
                        channel_index=channel_idx  # This identifies the "speaker"
                    ))
    
    # Single-channel or diarized response
    elif "words" in resp:
        for word_data in resp.get("words", []):
            # Only include actual words, not audio events
            if word_data.get("type") in [None, "word"]:
                words.append(Word(
                    text=word_data.get("text", ""),
                    start=word_data.get("start", 0.0),
                    end=word_data.get("end", 0.0),
                    type=word_data.get("type"),
                    speaker_id=word_data.get("speaker_id"),
                    channel_index=None
                ))
    else:
        raise ScribeParseError(f"No 'words' or 'transcripts' in response. Keys: {list(resp.keys())}")
    
    return words

def group_words_into_segments(words: List[Word], 
                             max_gap: float = 0.75,
                             min_merge_ms: int = 300) -> List[Segment]:
    """
    Walk words in time order. Start a new segment when speaker_id changes or
    gap > max_gap. Merge adjacent same-speaker segments shorter than min_merge_ms.
    Default speaker fallback: 'speaker_1' if diarization absent.
    
    Example:
    words = [
        Word("Hello", 0.0, 0.5, speaker_id="speaker_1"),
        Word("world", 0.6, 1.0, speaker_id="speaker_1"),
        Word("Hi", 2.0, 2.3, speaker_id="speaker_2")
    ]
    Result: [
        Segment("speaker_1", 0.0, 1.0, "Hello world"),
        Segment("speaker_2", 2.0, 2.3, "Hi")
    ]
    
    Args:
        words: List of Word objects to group
        max_gap: Maximum gap between words in same segment (seconds)
        min_merge_ms: Minimum segment duration to keep separate (milliseconds)
    
    Returns:
        List of Segment objects
    """
    if not words:
        return []
    
    segments: List[Segment] = []
    current_segment: Optional[Segment] = None
    
    # Sort words by start time
    sorted_words = sorted(words, key=lambda w: w.start)
    
    for word in sorted_words:
        # Skip non-word types
        if word.type and word.type != "word":
            continue
        
        # Determine speaker identity
        # Priority: speaker_id (diarization) > channel_index (multi-channel) > default
        if word.speaker_id:
            speaker = word.speaker_id
        elif word.channel_index is not None:
            speaker = f"channel_{word.channel_index}"
        else:
            speaker = "speaker_1"
        
        # Check if we need a new segment
        need_new_segment = (
            not current_segment or
            current_segment.speaker_id != speaker or
            current_segment.channel_index != word.channel_index or
            (word.start - current_segment.end) > max_gap
        )
        
        if need_new_segment:
            # Save current segment if exists
            if current_segment:
                segments.append(current_segment)
            
            # Start new segment
            current_segment = Segment(
                speaker_id=speaker,
                start=word.start,
                end=word.end,
                text=word.text,
                channel_index=word.channel_index
            )
        else:
            # Extend current segment
            current_segment.text += " " + word.text
            current_segment.end = word.end
    
    # Add final segment
    if current_segment:
        segments.append(current_segment)
    
    # Optional: Merge very short segments of the same speaker
    if min_merge_ms > 0:
        merged_segments = []
        for segment in segments:
            duration_ms = (segment.end - segment.start) * 1000
            
            # Try to merge with previous if same speaker and both are short
            if (merged_segments and 
                merged_segments[-1].speaker_id == segment.speaker_id and
                merged_segments[-1].channel_index == segment.channel_index and
                duration_ms < min_merge_ms):
                
                # Merge with previous
                merged_segments[-1].text += " " + segment.text
                merged_segments[-1].end = segment.end
            else:
                merged_segments.append(segment)
        
        segments = merged_segments
    
    return segments

def transcribe_and_group_from_url(audio_url: str, **kwargs) -> Dict:
    """
    Convenience function to transcribe and group segments.
    
    Returns dict with:
    - language_code: Detected language
    - text: Full transcript text
    - words: List of Word objects
    - segments: List of Segment objects
    """
    client = ScribeClient()
    
    # Get raw transcription
    raw_response = client.transcribe_url(audio_url, **kwargs)
    
    # Parse words
    words = parse_words_from_response(raw_response)
    
    # Group into segments
    segments = group_words_into_segments(words)
    
    return {
        "language_code": raw_response.get("language_code"),
        "language_probability": raw_response.get("language_probability"),
        "text": raw_response.get("text", ""),
        "words": words,
        "segments": segments,
        "raw_response": raw_response
    }

def test_client():
    """Quick test of the client"""
    try:
        client = ScribeClient()
        print("✅ ElevenLabs Scribe client initialized")
        print(f"   • API key: {client.api_key[:10]}...")
        return True
    except Exception as e:
        print(f"❌ ElevenLabs Scribe test failed: {e}")
        return False

if __name__ == "__main__":
    test_client()