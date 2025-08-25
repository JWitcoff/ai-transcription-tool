import streamlit as st
import asyncio
import time
import json
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional

# Import our optimized components
from live_stream_capture import LiveStreamCapture
from fast_transcriber import FastTranscriber, TranscriptionSegment, TranscriptBuffer
from live_analyzer import LiveAnalyzer

class LiveTranscriptionApp:
    """Main application for real-time video stream transcription and analysis"""
    
    def __init__(self):
        self.stream_capture = None
        self.transcriber = None
        self.analyzer = None
        self.transcript_buffer = None
        
        # Session state initialization
        if 'is_live' not in st.session_state:
            st.session_state.is_live = False
        if 'transcript_segments' not in st.session_state:
            st.session_state.transcript_segments = []
        if 'current_themes' not in st.session_state:
            st.session_state.current_themes = []
        if 'key_insights' not in st.session_state:
            st.session_state.key_insights = []
        if 'performance_stats' not in st.session_state:
            st.session_state.performance_stats = {}
    
    def run(self):
        """Main Streamlit app"""
        st.set_page_config(
            page_title="Live Video Transcription & Analysis",
            page_icon="🎥",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🎥 Live Video Stream Transcription & Analysis")
        st.markdown("*Real-time audio capture, transcription, and intelligent theme extraction*")
        
        # Sidebar configuration
        self._render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔴 Live Stream", "📝 Transcript", "🎯 Analysis", "⚡ Performance"])
        
        with tab1:
            self._render_live_stream_tab()
        
        with tab2:
            self._render_transcript_tab()
        
        with tab3:
            self._render_analysis_tab()
        
        with tab4:
            self._render_performance_tab()
    
    def _render_sidebar(self):
        """Render sidebar configuration"""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # Model settings
            st.subheader("Transcription Model")
            model_size = st.selectbox(
                "Whisper Model",
                ["tiny", "base", "small"],
                index=1,
                help="Larger models are more accurate but slower"
            )
            
            use_faster_whisper = st.checkbox(
                "Use Faster-Whisper",
                value=True,
                help="Optimized Whisper implementation for better performance"
            )
            
            # Processing settings
            st.subheader("Processing Settings")
            chunk_duration = st.slider(
                "Chunk Duration (seconds)",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5,
                help="Duration of each audio processing chunk"
            )
            
            analysis_window = st.slider(
                "Analysis Window (seconds)",
                min_value=30.0,
                max_value=300.0,
                value=60.0,
                step=30.0,
                help="Time window for theme analysis"
            )
            
            # Store in session state
            st.session_state.model_size = model_size
            st.session_state.use_faster_whisper = use_faster_whisper
            st.session_state.chunk_duration = chunk_duration
            st.session_state.analysis_window = analysis_window
            
            # System info
            st.subheader("System Info")
            import torch
            if torch.cuda.is_available():
                st.success("✅ CUDA Available")
                st.info(f"GPU: {torch.cuda.get_device_name()}")
            else:
                st.info("💻 Using CPU")
    
    def _render_live_stream_tab(self):
        """Render live streaming interface"""
        st.header("Live Stream Input")
        
        # Stream URL input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            stream_url = st.text_input(
                "Live Stream URL",
                placeholder="https://youtube.com/watch?v=... or https://twitch.tv/...",
                help="Enter the URL of a live video stream"
            )
        
        with col2:
            if st.button("🔍 Check Stream", disabled=not stream_url):
                self._check_stream_info(stream_url)
        
        # Stream info display
        if 'stream_info' in st.session_state:
            info = st.session_state.stream_info
            
            if 'error' in info:
                st.error(f"❌ {info['error']}")
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Title", info.get('title', 'Unknown')[:30] + "...")\n                with col2:
                    st.metric("Uploader", info.get('uploader', 'Unknown'))\n                with col3:
                    is_live = info.get('is_live', False)
                    st.metric("Status", "🔴 Live" if is_live else "📹 VOD")
                
                if info.get('description'):
                    with st.expander("📄 Description"):
                        st.text(info['description'])
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(
                "🎬 Start Live Transcription",
                type="primary",
                disabled=not stream_url or st.session_state.is_live
            ):
                self._start_live_transcription(stream_url)
        
        with col2:
            if st.button(
                "⏸️ Pause",
                disabled=not st.session_state.is_live
            ):
                self._pause_transcription()
        
        with col3:
            if st.button(
                "🛑 Stop",
                disabled=not st.session_state.is_live
            ):
                self._stop_transcription()
        
        # Status display
        if st.session_state.is_live:
            st.success("🔴 **Live transcription active**")
            
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            stats = st.session_state.get('performance_stats', {})
            
            with col1:
                st.metric("Queue Size", stats.get('queue_size', 0))
            with col2:
                st.metric("Segments", len(st.session_state.transcript_segments))
            with col3:
                st.metric("Themes", len(st.session_state.current_themes))
            with col4:
                processing_time = stats.get('processing_time', 0)
                st.metric("Avg Process Time", f"{processing_time:.2f}s")
        
        # Live transcript preview
        if st.session_state.transcript_segments:
            st.subheader("📺 Live Transcript (Last 30 seconds)")
            
            current_time = time.time()
            recent_segments = [
                seg for seg in st.session_state.transcript_segments[-10:]
                if current_time - seg['timestamp'] <= 30
            ]
            
            for segment in recent_segments[-5:]:  # Show last 5 segments
                time_str = datetime.fromtimestamp(segment['timestamp']).strftime("%H:%M:%S")
                st.markdown(f"**[{time_str}]** {segment['text']}")
    
    def _render_transcript_tab(self):
        """Render full transcript view"""
        st.header("📝 Full Transcript")
        
        if not st.session_state.transcript_segments:
            st.info("👈 Start live transcription to see results here")
            return
        
        # Transcript controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_timestamps = st.checkbox("Show Timestamps", value=True)
        
        with col2:
            confidence_filter = st.slider("Min Confidence", 0.0, 1.0, 0.3, 0.1)
        
        with col3:
            max_segments = st.number_input("Max Segments", 10, 1000, 100)
        
        # Filter segments
        filtered_segments = [
            seg for seg in st.session_state.transcript_segments
            if seg.get('confidence', 1.0) >= confidence_filter
        ][-max_segments:]
        
        # Display transcript
        if filtered_segments:
            # Generate downloadable transcript
            transcript_text = self._generate_transcript_text(filtered_segments, show_timestamps)
            
            # Download button
            st.download_button(
                "📥 Download Transcript",
                data=transcript_text,
                file_name=f"live_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
            # Display segments
            st.subheader(f"Showing {len(filtered_segments)} segments")
            
            for i, segment in enumerate(filtered_segments):
                timestamp = segment['timestamp']
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                confidence = segment.get('confidence', 1.0)
                
                # Color code by confidence
                if confidence >= 0.8:
                    color = "green"
                elif confidence >= 0.6:
                    color = "orange"
                else:
                    color = "red"
                
                if show_timestamps:
                    st.markdown(f"**[{time_str}]** <span style='color:{color}'>{segment['text']}</span>", 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:{color}'>{segment['text']}</span>", 
                              unsafe_allow_html=True)
        
        else:
            st.warning("No transcript segments match the current filters")
    
    def _render_analysis_tab(self):
        """Render analysis results"""
        st.header("🎯 Content Analysis")
        
        if not st.session_state.current_themes and not st.session_state.key_insights:
            st.info("👈 Start live transcription to see analysis here")
            return
        
        # Analysis summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Key Themes")
            
            themes = st.session_state.current_themes
            if themes:
                for theme in sorted(themes, key=lambda x: x.get('confidence', 0), reverse=True)[:5]:
                    confidence = theme.get('confidence', 0)
                    
                    # Progress bar for confidence
                    st.markdown(f"**{theme['title']}**")
                    st.progress(confidence)
                    st.markdown(f"*Keywords: {', '.join(theme.get('keywords', []))}*")
                    st.markdown(f"*Frequency: {theme.get('frequency', 0)}*")
                    st.markdown("---")
            else:
                st.info("No themes detected yet")
        
        with col2:
            st.subheader("💡 Key Insights")
            
            insights = st.session_state.key_insights
            if insights:
                # Categorize insights
                categories = {'decision': '🎯', 'question': '❓', 'action_item': '✅', 'key_point': '💡'}
                
                for insight in insights[-10:]:  # Show last 10
                    category = insight.get('category', 'key_point')
                    icon = categories.get(category, '💬')
                    importance = insight.get('importance', 0.5)
                    timestamp = insight.get('timestamp', time.time())
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                    
                    st.markdown(f"{icon} **[{time_str}]** {insight['text']}")
                    st.caption(f"Category: {category.title()}, Importance: {importance:.2f}")
                    st.markdown("---")
            else:
                st.info("No key insights detected yet")
        
        # AI-powered Summary and Analysis
        st.subheader("🤖 AI Analysis")
        
        # Import the existing analyzer
        from analyzer import TextAnalyzer
        
        if st.button("🧠 Generate AI Summary & Analysis"):
            if st.session_state.transcript_segments:
                # Combine recent transcript text
                full_text = ' '.join([seg['text'] for seg in st.session_state.transcript_segments[-50:]])
                
                with st.spinner("Generating AI-powered analysis..."):
                    analyzer = TextAnalyzer()
                    
                    # Generate summary
                    summary = analyzer.summarize(full_text)
                    st.subheader("📝 AI Summary")
                    st.write(summary)
                    
                    # Extract themes
                    themes = analyzer.extract_themes(full_text)
                    st.subheader("🎯 AI-Extracted Themes")
                    for theme in themes:
                        st.markdown(f"**{theme['title']}**")
                        st.markdown(f"*{theme['description']}*")
                        st.caption(f"Keywords: {', '.join(theme['keywords'])}")
                    
                    # Sentiment analysis
                    sentiment = analyzer.analyze_sentiment(full_text)
                    st.subheader("😊 Sentiment Analysis")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Sentiment", sentiment['label'])
                    
                    with col2:
                        st.metric("Confidence", f"{sentiment['confidence']:.1%}")
                    
                    with col3:
                        st.metric("Emotion", sentiment.get('emotion', 'neutral').title())
                    
                    # Text statistics
                    stats = analyzer.get_text_statistics(full_text)
                    with st.expander("📊 Text Statistics"):
                        st.json(stats)
    
    def _render_performance_tab(self):
        """Render performance monitoring"""
        st.header("⚡ Performance Monitoring")
        
        stats = st.session_state.get('performance_stats', {})
        
        # System performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 System Performance")
            
            if stats:
                st.metric("Transcription Queue", stats.get('queue_size', 0))
                st.metric("Result Queue", stats.get('result_queue_size', 0))
                st.metric("Recent Segments", stats.get('recent_segments', 0))
                st.metric("Model Device", stats.get('device', 'Unknown'))
                
                # Processing speed
                processing_speed = stats.get('real_time_factor', 1.0)
                if processing_speed >= 1.0:
                    st.success(f"✅ Real-time processing: {processing_speed:.2f}x")
                else:
                    st.warning(f"⚠️ Slower than real-time: {processing_speed:.2f}x")
            else:
                st.info("No performance data available")
        
        with col2:
            st.subheader("📊 Processing Statistics")
            
            # Processing time chart placeholder
            st.info("Performance charts will appear here during live transcription")
        
        # Optimization recommendations
        st.subheader("💡 Optimization Recommendations")
        
        import torch
        if torch.cuda.is_available():
            st.success("✅ CUDA is available and recommended for best performance")
        else:
            st.warning("⚠️ Consider using a GPU for better real-time performance")
        
        model_size = st.session_state.get('model_size', 'base')
        if model_size in ['medium', 'large']:
            st.warning(f"⚠️ {model_size.title()} model may be too slow for real-time processing")
        else:
            st.success(f"✅ {model_size.title()} model is suitable for real-time processing")
    
    def _check_stream_info(self, stream_url: str):
        """Check stream information"""
        try:
            capture = LiveStreamCapture()
            stream_info = capture.get_stream_info(stream_url)
            st.session_state.stream_info = stream_info
            
            if 'error' not in stream_info:
                st.success("✅ Stream information retrieved successfully")
            
        except Exception as e:
            st.session_state.stream_info = {'error': str(e)}
    
    def _start_live_transcription(self, stream_url: str):
        """Start live transcription process"""
        try:
            # Initialize components
            self.stream_capture = LiveStreamCapture(
                chunk_duration=st.session_state.chunk_duration
            )
            
            self.transcriber = FastTranscriber(
                model_size=st.session_state.model_size,
                use_faster_whisper=st.session_state.use_faster_whisper
            )
            
            self.analyzer = LiveAnalyzer(
                analysis_window=st.session_state.analysis_window
            )
            
            self.transcript_buffer = TranscriptBuffer()
            
            # Start processing
            self.transcriber.start_processing(callback=self._on_transcription_result)
            self.analyzer.start_analysis()
            
            # Start capture in a separate thread
            def capture_audio():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.stream_capture.start_live_capture(stream_url, self._on_audio_chunk)
                )
            
            capture_thread = threading.Thread(target=capture_audio, daemon=True)
            capture_thread.start()
            
            st.session_state.is_live = True
            st.success("🚀 Live transcription started!")
            
        except Exception as e:
            st.error(f"❌ Failed to start transcription: {e}")
    
    def _on_audio_chunk(self, audio_data, timestamp):
        """Handle new audio chunk"""
        if self.transcriber:
            # Process audio chunk
            segment = self.transcriber.transcribe_chunk(audio_data, timestamp)
            
            # Update performance stats
            if hasattr(self.transcriber, 'get_processing_stats'):
                st.session_state.performance_stats = self.transcriber.get_processing_stats()
    
    def _on_transcription_result(self, segment):
        """Handle transcription result"""
        if segment and segment.text.strip():
            # Add to transcript buffer
            if self.transcript_buffer:
                self.transcript_buffer.add_segment(segment)
            
            # Add to session state
            segment_dict = {
                'text': segment.text,
                'timestamp': segment.start_time,
                'confidence': segment.confidence
            }
            st.session_state.transcript_segments.append(segment_dict)
            
            # Analyze content
            if self.analyzer:
                self.analyzer.add_text(segment.text, segment.start_time)
                
                # Update analysis results
                analysis = self.analyzer.get_analysis_summary()
                st.session_state.current_themes = analysis.get('themes', [])
                st.session_state.key_insights = analysis.get('key_insights', {}).get('recent', [])
    
    def _pause_transcription(self):
        """Pause transcription"""
        # Implementation for pause functionality
        st.info("⏸️ Transcription paused")
    
    def _stop_transcription(self):
        """Stop transcription"""
        try:
            if self.stream_capture:
                self.stream_capture.stop_capture()
            
            if self.transcriber:
                self.transcriber.stop_processing()
            
            if self.analyzer:
                self.analyzer.stop_analysis()
            
            st.session_state.is_live = False
            st.success("🛑 Live transcription stopped")
            
        except Exception as e:
            st.error(f"Error stopping transcription: {e}")
    
    def _generate_transcript_text(self, segments: List[Dict], include_timestamps: bool = True) -> str:
        """Generate downloadable transcript text"""
        lines = []
        
        if include_timestamps:
            for segment in segments:
                timestamp = datetime.fromtimestamp(segment['timestamp']).strftime("%H:%M:%S")
                lines.append(f"[{timestamp}] {segment['text']}")
        else:
            for segment in segments:
                lines.append(segment['text'])
        
        return '\n'.join(lines)


def main():
    """Main application entry point"""
    app = LiveTranscriptionApp()
    app.run()


if __name__ == "__main__":
    main()