import streamlit as st
import tempfile
import os
from datetime import datetime
import json

from audio_capture import AudioCapture
from transcriber import Transcriber
from analyzer import TextAnalyzer

class VideoTranscriptionApp:
    def __init__(self):
        self.audio_capture = AudioCapture()
        self.transcriber = Transcriber()
        self.analyzer = TextAnalyzer()
        
    def run(self):
        st.set_page_config(
            page_title="Video Transcription & Analysis Tool",
            page_icon="🎬",
            layout="wide"
        )
        
        st.title("🎬 Video Transcription & Analysis Tool")
        st.markdown("Extract audio from live video streams, transcribe to text, and analyze key themes")
        
        # Sidebar for configuration
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # API Keys
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                     help="For transcription and analysis")
            
            # Audio quality settings
            st.subheader("Audio Settings")
            audio_quality = st.selectbox("Audio Quality", ["best", "medium", "low"])
            
            # Analysis settings
            st.subheader("Analysis Settings")
            enable_summary = st.checkbox("Generate Summary", value=True)
            enable_themes = st.checkbox("Extract Key Themes", value=True)
            enable_sentiment = st.checkbox("Sentiment Analysis", value=True)
            
        # Main interface
        tab1, tab2, tab3 = st.tabs(["🎥 Live Capture", "📝 Transcription", "📊 Analysis"])
        
        with tab1:
            self._render_capture_tab()
            
        with tab2:
            self._render_transcription_tab()
            
        with tab3:
            self._render_analysis_tab()
    
    def _render_capture_tab(self):
        st.header("Audio/Video Input")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Stream URL", "Upload File"],
            help="Select how you want to provide the audio/video"
        )
        
        if input_method == "Stream URL":
            # URL input
            video_url = st.text_input(
                "Enter video URL:", 
                placeholder="https://youtube.com/watch?v=...",
                help="Supports YouTube, Twitch, Vimeo, and other major platforms"
            )
            
            # Show supported platforms
            with st.expander("📋 Supported Platforms"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Fully Supported:**")
                    st.markdown("• YouTube\n• Twitch\n• Vimeo\n• Facebook\n• Instagram")
                with col2:
                    st.markdown("**Also Supported:**")
                    st.markdown("• TikTok\n• Twitter\n• Reddit\n• And 1000+ more")
                
                st.warning("**Not Supported:** Livestorm, proprietary platforms, password-protected content")
            
            # Capture options
            col1, col2 = st.columns(2)
            
            with col1:
                duration = st.number_input("Capture Duration (seconds)", 
                                         min_value=10, max_value=3600, value=300)
                
            with col2:
                start_time = st.number_input("Start Time (seconds)", 
                                           min_value=0, value=0)
            
            # Capture button
            if st.button("🎬 Start Capture", type="primary"):
                if video_url:
                    self._start_capture(video_url, duration, start_time)
                else:
                    st.error("Please enter a video URL")
        
        else:  # Upload File
            st.subheader("Upload Audio/Video File")
            
            uploaded_file = st.file_uploader(
                "Choose an audio or video file",
                type=['mp4', 'avi', 'mov', 'mkv', 'webm', 'mp3', 'wav', 'm4a', 'flac', 'ogg']
            )
            
            if uploaded_file is not None:
                # Save uploaded file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_file_path = tmp_file.name
                
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                
                # File processing options
                col1, col2 = st.columns(2)
                
                with col1:
                    duration = st.number_input("Duration to process (seconds)", 
                                             min_value=10, max_value=3600, value=300,
                                             help="Leave as default to process entire file")
                    
                with col2:
                    start_time = st.number_input("Start time (seconds)", 
                                               min_value=0, value=0)
                
                # Process button
                if st.button("🎵 Process File", type="primary"):
                    self._process_uploaded_file(temp_file_path, duration, start_time)
                
        # Display capture status
        if "capture_status" in st.session_state:
            if st.session_state.capture_status == "running":
                st.info("🔴 Processing in progress...")
                st.progress(st.session_state.get("capture_progress", 0))
            elif st.session_state.capture_status == "completed":
                st.success("✅ Audio processing completed!")
                
                # Display audio info
                if "audio_info" in st.session_state:
                    info = st.session_state.audio_info
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Title", info.get('title', 'Unknown'))
                    with col2:
                        st.metric("Duration", f"{info.get('duration', 0)}s")
                    with col3:
                        file_size = info.get('file_size', 0)
                        st.metric("File Size", f"{file_size / 1024 / 1024:.1f} MB")
            elif st.session_state.capture_status == "error":
                st.error(f"❌ Processing failed: {st.session_state.get('error_message', 'Unknown error')}")
    
    def _render_transcription_tab(self):
        st.header("Audio Transcription")
        
        if "audio_file" not in st.session_state:
            st.info("👆 Capture audio from the Live Capture tab first")
            return
            
        # Transcription options
        col1, col2 = st.columns(2)
        
        with col1:
            model_size = st.selectbox("Whisper Model Size", 
                                    ["tiny", "base", "small", "medium", "large"])
            
        with col2:
            language = st.selectbox("Language", 
                                  ["auto-detect", "en", "es", "fr", "de", "it", "pt"])
        
        # Enhanced features for uploaded files
        if "audio_info" in st.session_state and st.session_state.audio_info.get("from_file", False):
            st.subheader("🎯 Enhanced Features (Uploaded Files)")
            
            col1, col2 = st.columns(2)
            with col1:
                enable_diarization = st.checkbox(
                    "Speaker Diarization", 
                    help="Identify different speakers in the audio (slower but more detailed)"
                )
            with col2:
                use_enhanced = st.checkbox(
                    "Enhanced Transcription", 
                    value=True,
                    help="Use advanced transcription features for better accuracy"
                )
        else:
            enable_diarization = False
            use_enhanced = False
        
        # Transcribe button
        if st.button("🎙️ Start Transcription", type="primary"):
            self._start_transcription(model_size, language, use_enhanced, enable_diarization)
        
        # Display transcription results
        if "transcription" in st.session_state:
            st.subheader("Transcription Results")
            
            # Show transcript with timestamps and speaker info
            transcript = st.session_state.transcription
            
            # Check if we have speaker diarization
            has_speakers = transcript.get("has_diarization", False)
            
            if has_speakers:
                st.info("🎯 Transcript includes speaker identification")
            
            for segment in transcript.get("segments", []):
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                text = segment.get("text", "")
                speaker = segment.get("speaker", "")
                
                # Format with speaker info if available
                if speaker and has_speakers:
                    st.markdown(f"**[{start_time:.1f}s - {end_time:.1f}s] 🗣️ {speaker}:** {text}")
                else:
                    st.markdown(f"**[{start_time:.1f}s - {end_time:.1f}s]** {text}")
            
            # Download options
            st.subheader("📥 Download Transcript")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Generate formatted text with speaker info
                txt_content = self._generate_formatted_txt(transcript)
                st.download_button(
                    "📄 Download TXT",
                    data=txt_content,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    help="Download transcript with speaker labels"
                )
            
            with col2:
                st.download_button(
                    "📊 Download JSON",
                    data=json.dumps(transcript, indent=2),
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help="Download full transcript data including timestamps"
                )
            
            with col3:
                # Generate SRT file
                srt_content = self._generate_srt(transcript)
                st.download_button(
                    "🎬 Download SRT",
                    data=srt_content,
                    file_name=f"subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                    mime="text/plain",
                    help="Download subtitle file for video editors"
                )
            
            # Show diarization status
            if has_speakers:
                st.success("✅ Speaker diarization is ENABLED - Different speakers are identified in the transcript")
                # Count speakers
                speakers = set()
                for segment in transcript.get("segments", []):
                    if segment.get("speaker"):
                        speakers.add(segment.get("speaker"))
                st.info(f"Found {len(speakers)} unique speaker(s): {', '.join(sorted(speakers))}")
            else:
                st.info("ℹ️ Speaker diarization is DISABLED - Enable it for speaker identification")
    
    def _render_analysis_tab(self):
        st.header("Text Analysis & Theme Extraction")
        
        if "transcription" not in st.session_state:
            st.info("👆 Complete transcription first")
            return
        
        transcript_text = st.session_state.transcription.get("text", "")
        
        if not transcript_text.strip():
            st.warning("No text found in transcription")
            return
        
        # Analysis buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Generate Summary"):
                self._generate_summary(transcript_text)
        
        with col2:
            if st.button("🎯 Extract Themes"):
                self._extract_themes(transcript_text)
        
        with col3:
            if st.button("😊 Analyze Sentiment"):
                self._analyze_sentiment(transcript_text)
        
        # Display analysis results
        if "summary" in st.session_state:
            st.subheader("📝 Summary")
            st.write(st.session_state.summary)
        
        if "themes" in st.session_state:
            st.subheader("🎯 Key Themes")
            themes = st.session_state.themes
            
            for i, theme in enumerate(themes, 1):
                st.markdown(f"**{i}. {theme['title']}**")
                st.markdown(f"   {theme['description']}")
                st.markdown(f"   *Keywords: {', '.join(theme['keywords'])}*")
                st.markdown("---")
        
        if "sentiment" in st.session_state:
            st.subheader("😊 Sentiment Analysis")
            sentiment = st.session_state.sentiment
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Overall Sentiment", sentiment['label'], 
                         f"{sentiment['score']:.2f}")
            
            with col2:
                st.metric("Confidence", f"{sentiment['confidence']:.1%}")
            
            with col3:
                st.metric("Emotional Tone", sentiment.get('emotion', 'Neutral'))
    
    def _start_capture(self, url, duration, start_time):
        """Start audio capture from video stream"""
        st.session_state.capture_status = "running"
        st.session_state.capture_progress = 0
        
        try:
            # Use AudioCapture class to extract audio
            audio_file, info = self.audio_capture.capture_from_url(
                url, 
                duration=duration, 
                start_time=start_time
            )
            
            st.session_state.audio_file = audio_file
            st.session_state.audio_info = info
            st.session_state.capture_status = "completed"
            st.session_state.capture_progress = 100
            
        except Exception as e:
            st.session_state.capture_status = "error"
            st.session_state.error_message = str(e)
    
    def _process_uploaded_file(self, file_path, duration, start_time):
        """Process uploaded audio/video file"""
        st.session_state.capture_status = "running"
        st.session_state.capture_progress = 0
        
        try:
            # Use AudioCapture class to extract audio from local file
            audio_file, info = self.audio_capture.capture_from_file(
                file_path,
                start_time=start_time,
                duration=duration if duration < 3600 else None
            )
            
            # Mark as uploaded file for enhanced features
            info['from_file'] = True
            
            st.session_state.audio_file = audio_file
            st.session_state.audio_info = info
            st.session_state.capture_status = "completed"
            st.session_state.capture_progress = 100
            
        except Exception as e:
            st.session_state.capture_status = "error"
            st.session_state.error_message = str(e)
    
    def _start_transcription(self, model_size, language, use_enhanced=False, enable_diarization=False):
        """Start audio transcription with optional enhanced features"""
        if "audio_file" not in st.session_state:
            st.error("No audio file available")
            return
        
        try:
            # Determine spinner message based on features
            spinner_msg = "Transcribing audio..."
            if use_enhanced and enable_diarization:
                spinner_msg = "Transcribing with speaker identification... This may take several minutes."
            elif use_enhanced:
                spinner_msg = "Enhanced transcribing... This may take a few minutes."
            
            with st.spinner(spinner_msg):
                transcript = self.transcriber.transcribe(
                    st.session_state.audio_file,
                    model_size=model_size,
                    language=language if language != "auto-detect" else None,
                    use_enhanced=use_enhanced,
                    enable_diarization=enable_diarization
                )
                
                st.session_state.transcription = transcript
                
                # Show success message with feature info
                success_msg = "Transcription completed!"
                if transcript.get("enhanced"):
                    success_msg += " ✨ Enhanced features enabled."
                if transcript.get("has_diarization"):
                    success_msg += " 🎯 Speaker identification included."
                
                st.success(success_msg)
                
        except Exception as e:
            st.error(f"Transcription failed: {str(e)}")
    
    def _generate_summary(self, text):
        """Generate text summary"""
        try:
            with st.spinner("Generating summary..."):
                summary = self.analyzer.summarize(text)
                st.session_state.summary = summary
                
        except Exception as e:
            st.error(f"Summary generation failed: {str(e)}")
    
    def _extract_themes(self, text):
        """Extract key themes from text"""
        try:
            with st.spinner("Extracting themes..."):
                themes = self.analyzer.extract_themes(text)
                st.session_state.themes = themes
                
        except Exception as e:
            st.error(f"Theme extraction failed: {str(e)}")
    
    def _analyze_sentiment(self, text):
        """Analyze text sentiment"""
        try:
            with st.spinner("Analyzing sentiment..."):
                sentiment = self.analyzer.analyze_sentiment(text)
                st.session_state.sentiment = sentiment
                
        except Exception as e:
            st.error(f"Sentiment analysis failed: {str(e)}")
    
    def _generate_formatted_txt(self, transcript):
        """Generate formatted text with speaker information"""
        lines = []
        
        # Add header
        lines.append("TRANSCRIPTION")
        lines.append(f"Generated: {datetime.now()}")
        if transcript.get("has_diarization"):
            lines.append("Speaker Diarization: ENABLED")
        lines.append("=" * 60)
        lines.append("")
        
        # Add transcript with speaker info
        if transcript.get("has_diarization") and transcript.get("segments"):
            current_speaker = None
            for segment in transcript.get("segments", []):
                speaker = segment.get("speaker", "Unknown")
                text = segment.get("text", "").strip()
                
                if speaker != current_speaker:
                    lines.append("")
                    lines.append(f"{speaker}:")
                    current_speaker = speaker
                
                lines.append(text)
        else:
            # No diarization - just return plain text
            lines.append(transcript.get("text", ""))
        
        return "\n".join(lines)
    
    def _generate_srt(self, transcript):
        """Generate SRT subtitle file"""
        srt_content = ""
        
        for i, segment in enumerate(transcript.get("segments", []), 1):
            start = self._seconds_to_srt_time(segment.get("start", 0))
            end = self._seconds_to_srt_time(segment.get("end", 0))
            text = segment.get("text", "").strip()
            
            # Add speaker info if available
            if transcript.get("has_diarization") and segment.get("speaker"):
                text = f"[{segment.get('speaker')}] {text}"
            
            srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
        
        return srt_content
    
    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

if __name__ == "__main__":
    app = VideoTranscriptionApp()
    app.run()