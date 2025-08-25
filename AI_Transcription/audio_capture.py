import yt_dlp
import ffmpeg
import tempfile
import os
from pathlib import Path
import subprocess
from typing import Tuple, Dict, Optional

class AudioCapture:
    """Handles audio extraction from live video streams"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.download_progress = 0
        
    def capture_from_url(self, url: str, duration: Optional[int] = None, start_time: int = 0) -> Tuple[str, Dict]:
        """
        Capture audio from a video URL
        
        Args:
            url: Video URL (YouTube, Twitch, etc.)
            duration: Duration to capture in seconds
            start_time: Start time offset in seconds
            
        Returns:
            Tuple of (audio_file_path, info_dict)
        """
        # Check if this is a Livestorm URL
        if 'livestorm.co' in url:
            raise Exception(
                "Livestorm platform is not directly supported for audio extraction. "
                "Please try one of these alternatives:\n"
                "1. Use a screen recording tool to record the audio\n"
                "2. If there's a replay available, check if it's posted on YouTube\n"
                "3. Contact the organizer for an audio recording\n"
                "4. Use a different video platform URL if available"
            )
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
            'extractaudio': True,
            'audioformat': 'wav',
            'audioquality': '192K',
            'no_warnings': False,
            'quiet': False,  # Enable output for progress
            'progress_hooks': [self._progress_hook],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(url, download=False)
                
                # Get the best audio stream URL
                if 'entries' in info:
                    # Playlist - get first video
                    video_info = info['entries'][0]
                else:
                    video_info = info
                
                # Find audio stream
                audio_url = self._get_audio_stream_url(video_info)
                
                if not audio_url:
                    raise ValueError("No audio stream found")
                
                # Create output filename
                safe_title = self._sanitize_filename(video_info.get('title', 'audio'))
                duration_str = str(duration) if duration else "full"
                output_file = os.path.join(self.temp_dir, f"{safe_title}_{start_time}_{duration_str}.wav")
                
                # Download and process audio segment
                print(f"   Downloading audio... (this may take a moment)")
                self._download_audio_segment(audio_url, output_file, start_time, duration)
                print(f"✅ Audio downloaded successfully")
                
                # Prepare info dict
                audio_info = {
                    'title': video_info.get('title', 'Unknown'),
                    'duration': duration,
                    'start_time': start_time,
                    'original_duration': video_info.get('duration', 0),
                    'uploader': video_info.get('uploader', 'Unknown'),
                    'upload_date': video_info.get('upload_date', 'Unknown'),
                    'file_path': output_file,
                    'file_size': os.path.getsize(output_file) if os.path.exists(output_file) else 0
                }
                
                return output_file, audio_info
                
        except Exception as e:
            # Provide more helpful error messages
            error_msg = str(e)
            if "Unsupported URL" in error_msg:
                domain = url.split("//")[1].split("/")[0] if "//" in url else url
                raise Exception(
                    f"The platform '{domain}' is not supported for direct audio extraction. "
                    f"This tool works best with YouTube, Twitch, Vimeo, and other major platforms. "
                    f"Please try:\n"
                    f"1. A YouTube or Vimeo version of the video\n"
                    f"2. A direct video file URL\n"
                    f"3. Upload a local video/audio file instead"
                )
            raise Exception(f"Failed to capture audio: {error_msg}")
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp downloads"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                if percent - self.download_progress >= 10:  # Update every 10%
                    self.download_progress = percent
                    print(f"   Download progress: {percent:.0f}%")
        elif d['status'] == 'finished':
            print(f"   Processing audio file...")
    
    def _get_audio_stream_url(self, video_info: Dict) -> Optional[str]:
        """Extract the best audio stream URL from video info"""
        formats = video_info.get('formats', [])
        
        # Look for audio-only streams first
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        
        if audio_formats:
            # Sort by quality (abr = audio bitrate)
            audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
            return audio_formats[0]['url']
        
        # Fallback to video with audio
        video_with_audio = [f for f in formats if f.get('acodec') != 'none']
        
        if video_with_audio:
            video_with_audio.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
            return video_with_audio[0]['url']
        
        return None
    
    def _download_audio_segment(self, audio_url: str, output_file: str, start_time: int, duration: int):
        """Download and extract audio segment using ffmpeg"""
        try:
            # Use ffmpeg to download and extract segment
            if duration:
                stream = ffmpeg.input(audio_url, ss=start_time, t=duration)
            else:
                stream = ffmpeg.input(audio_url, ss=start_time)
            stream = ffmpeg.output(stream, output_file, 
                                 acodec='pcm_s16le',  # WAV format
                                 ar=16000,  # 16kHz sample rate (good for speech)
                                 ac=1)  # Mono audio
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
        except ffmpeg.Error as e:
            # Fallback to subprocess if ffmpeg-python fails
            self._download_with_subprocess(audio_url, output_file, start_time, duration)
    
    def _download_with_subprocess(self, audio_url: str, output_file: str, start_time: int, duration: int):
        """Fallback method using subprocess to call ffmpeg directly"""
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', audio_url,
        ]
        
        # Only add duration if specified
        if duration:
            cmd.extend(['-t', str(duration)])
        
        cmd.extend([
            '-vn',  # No video
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',  # Overwrite output
            output_file
        ])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg failed: {e.stderr.decode()}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove unsafe characters from filename"""
        # Keep only alphanumeric characters, spaces, hyphens, and underscores
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ' -_':
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        return ''.join(safe_chars).strip()[:50]  # Limit length
    
    def capture_from_file(self, file_path: str, start_time: int = 0, duration: Optional[int] = None) -> Tuple[str, Dict]:
        """
        Extract audio from a local video file
        
        Args:
            file_path: Path to local video file
            start_time: Start time offset in seconds
            duration: Duration to extract (None for entire file)
            
        Returns:
            Tuple of (audio_file_path, info_dict)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file info
        try:
            probe = ffmpeg.probe(file_path)
            file_duration = float(probe['format']['duration'])
            
            if duration is None:
                duration = int(file_duration - start_time)
            
        except Exception as e:
            raise Exception(f"Failed to probe file: {str(e)}")
        
        # Create output filename
        input_path = Path(file_path)
        output_file = os.path.join(self.temp_dir, f"{input_path.stem}_{start_time}_{duration}.wav")
        
        try:
            # Extract audio segment
            stream = ffmpeg.input(file_path, ss=start_time, t=duration)
            stream = ffmpeg.output(stream, output_file,
                                 acodec='pcm_s16le',
                                 ar=16000,
                                 ac=1)
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Prepare info dict
            audio_info = {
                'title': input_path.stem,
                'duration': duration,
                'start_time': start_time,
                'original_duration': file_duration,
                'file_path': output_file,
                'file_size': os.path.getsize(output_file)
            }
            
            return output_file, audio_info
            
        except ffmpeg.Error as e:
            raise Exception(f"Failed to extract audio: {str(e)}")
    
    def get_supported_sites(self) -> list:
        """Get list of supported video sites"""
        try:
            with yt_dlp.YoutubeDL() as ydl:
                extractors = ydl._get_available_extractors()
                return [extractor.IE_NAME for extractor in extractors if hasattr(extractor, 'IE_NAME')]
        except:
            # Return common supported sites if extraction fails
            return [
                'youtube', 'twitch', 'vimeo', 'dailymotion', 'facebook',
                'instagram', 'tiktok', 'twitter', 'reddit', 'streamable'
            ]
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        temp_files = Path(self.temp_dir).glob("*.wav")
        for file in temp_files:
            try:
                file.unlink()
            except:
                pass  # Ignore errors when cleaning up