import asyncio
import time
from typing import Dict, List, Optional, Callable
from collections import deque
from dataclasses import dataclass
import threading
import queue
import re

@dataclass
class Theme:
    """Represents an extracted theme with keywords and context"""
    title: str
    keywords: List[str]
    description: str
    confidence: float
    first_mentioned: float
    last_mentioned: float
    frequency: int

@dataclass
class KeyInsight:
    """Represents a key insight or important statement"""
    text: str
    timestamp: float
    importance_score: float
    category: str  # 'decision', 'question', 'action_item', 'key_point'

class LiveAnalyzer:
    """Real-time analysis of transcribed content for themes and insights"""
    
    def __init__(self, analysis_window: float = 60.0):
        """
        Initialize live analyzer
        
        Args:
            analysis_window: Time window for analysis in seconds
        """
        self.analysis_window = analysis_window
        
        # Text buffers
        self.text_buffer = deque(maxlen=1000)  # Store text chunks with timestamps
        self.full_text = ""
        
        # Analysis results
        self.current_themes = {}  # theme_id -> Theme
        self.key_insights = deque(maxlen=50)
        self.sentiment_history = deque(maxlen=100)
        
        # Threading for background analysis
        self.analysis_queue = queue.Queue()
        self.is_analyzing = False
        self.analysis_thread = None
        
        # Keywords for different categories
        self.decision_keywords = [
            'decide', 'decision', 'choose', 'selected', 'agreed', 'concluded',
            'determined', 'resolved', 'final', 'commit', 'go with'
        ]
        
        self.question_keywords = [
            'question', 'ask', 'wonder', 'curious', 'what if', 'how about',
            'should we', 'could we', 'would it', 'why', 'how', 'what', 'when', 'where'
        ]
        
        self.action_keywords = [
            'action', 'do', 'implement', 'execute', 'complete', 'finish',
            'start', 'begin', 'create', 'build', 'develop', 'work on'
        ]
        
        # Common theme categories
        self.theme_patterns = {
            'business': ['revenue', 'profit', 'sales', 'market', 'customer', 'strategy', 'growth'],
            'technology': ['software', 'system', 'platform', 'api', 'database', 'code', 'development'],
            'project': ['timeline', 'deadline', 'milestone', 'deliverable', 'requirement', 'scope'],
            'team': ['team', 'collaboration', 'meeting', 'discussion', 'feedback', 'communication'],
            'process': ['workflow', 'procedure', 'process', 'method', 'approach', 'framework'],
            'quality': ['quality', 'testing', 'bug', 'issue', 'improvement', 'optimization'],
            'planning': ['plan', 'schedule', 'roadmap', 'goals', 'objectives', 'priorities']
        }
    
    def start_analysis(self):
        """Start background analysis processing"""
        if self.is_analyzing:
            return
        
        self.is_analyzing = True
        self.analysis_thread = threading.Thread(
            target=self._analysis_worker,
            daemon=True
        )
        self.analysis_thread.start()
        print("🔍 Started real-time content analysis")
    
    def stop_analysis(self):
        """Stop background analysis"""
        self.is_analyzing = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=2)
        print("🛑 Stopped content analysis")
    
    def add_text(self, text: str, timestamp: float):
        """Add new transcribed text for analysis"""
        if not text.strip():
            return
        
        # Add to buffer
        self.text_buffer.append((text, timestamp))
        
        # Update full text
        self._update_full_text()
        
        # Queue for analysis if not already processing
        try:
            self.analysis_queue.put_nowait((text, timestamp))
        except queue.Full:
            pass  # Skip if queue is full
    
    def _update_full_text(self):
        """Update full text from buffer"""
        current_time = time.time()
        
        # Remove old text outside analysis window
        while (self.text_buffer and 
               current_time - self.text_buffer[0][1] > self.analysis_window):
            self.text_buffer.popleft()
        
        # Rebuild full text
        self.full_text = ' '.join([text for text, _ in self.text_buffer])
    
    def _analysis_worker(self):
        """Background worker for content analysis"""
        while self.is_analyzing:
            try:
                # Get text with timeout
                text, timestamp = self.analysis_queue.get(timeout=1.0)
                
                # Perform quick analysis on new text
                self._analyze_new_text(text, timestamp)
                
                # Periodically perform comprehensive analysis
                if len(self.text_buffer) % 10 == 0:  # Every 10 new texts
                    self._perform_comprehensive_analysis()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Analysis worker error: {e}")
                continue
    
    def _analyze_new_text(self, text: str, timestamp: float):
        """Quick analysis of new text"""
        text_lower = text.lower()
        
        # Check for key insights
        insight = self._extract_insight(text, timestamp)
        if insight:
            self.key_insights.append(insight)
        
        # Update theme frequencies
        self._update_theme_frequencies(text_lower, timestamp)
        
        # Basic sentiment
        sentiment = self._quick_sentiment_analysis(text)
        self.sentiment_history.append((sentiment, timestamp))
    
    def _extract_insight(self, text: str, timestamp: float) -> Optional[KeyInsight]:
        """Extract key insights from text"""
        text_lower = text.lower()
        
        # Check for decisions
        for keyword in self.decision_keywords:
            if keyword in text_lower:
                return KeyInsight(
                    text=text,
                    timestamp=timestamp,
                    importance_score=0.8,
                    category='decision'
                )
        
        # Check for questions
        if '?' in text or any(kw in text_lower for kw in self.question_keywords):
            return KeyInsight(
                text=text,
                timestamp=timestamp,
                importance_score=0.6,
                category='question'
            )
        
        # Check for action items
        for keyword in self.action_keywords:
            if keyword in text_lower:
                return KeyInsight(
                    text=text,
                    timestamp=timestamp,
                    importance_score=0.7,
                    category='action_item'
                )
        
        # Check for emphasis (caps, exclamation)
        if text.isupper() or '!' in text:
            return KeyInsight(
                text=text,
                timestamp=timestamp,
                importance_score=0.5,
                category='key_point'
            )
        
        return None
    
    def _update_theme_frequencies(self, text_lower: str, timestamp: float):
        """Update theme keyword frequencies"""
        for theme_name, keywords in self.theme_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            
            if matches > 0:
                if theme_name in self.current_themes:
                    theme = self.current_themes[theme_name]
                    theme.frequency += matches
                    theme.last_mentioned = timestamp
                else:
                    # Create new theme
                    matched_keywords = [kw for kw in keywords if kw in text_lower]
                    self.current_themes[theme_name] = Theme(
                        title=theme_name.title(),
                        keywords=matched_keywords,
                        description=f"Discussion about {theme_name}",
                        confidence=min(1.0, matches * 0.2),
                        first_mentioned=timestamp,
                        last_mentioned=timestamp,
                        frequency=matches
                    )
    
    def _perform_comprehensive_analysis(self):
        """Perform comprehensive analysis of all text"""
        if not self.full_text:
            return
        
        # Extract more sophisticated themes
        self._extract_advanced_themes()
        
        # Update theme descriptions
        self._update_theme_descriptions()
        
        # Prune old or low-confidence themes
        self._prune_themes()
    
    def _extract_advanced_themes(self):
        """Extract themes using more advanced techniques"""
        # Simple keyword co-occurrence analysis
        words = re.findall(r'\w+', self.full_text.lower())
        
        if len(words) < 50:  # Not enough content yet
            return
        
        # Find frequent word combinations
        bigrams = [(words[i], words[i+1]) for i in range(len(words)-1)]
        trigrams = [(words[i], words[i+1], words[i+2]) for i in range(len(words)-2)]
        
        # Count frequencies
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Create themes from frequent words
        for word, freq in word_freq.items():
            if freq >= 3 and word not in ['that', 'this', 'with', 'have', 'will', 'they']:
                theme_id = f"topic_{word}"
                
                if theme_id not in self.current_themes:
                    self.current_themes[theme_id] = Theme(
                        title=word.title(),
                        keywords=[word],
                        description=f"Frequent discussion of '{word}'",
                        confidence=min(1.0, freq * 0.1),
                        first_mentioned=time.time() - self.analysis_window,
                        last_mentioned=time.time(),
                        frequency=freq
                    )
    
    def _update_theme_descriptions(self):
        """Update theme descriptions based on context"""
        for theme_name, theme in self.current_themes.items():
            # Find context around theme keywords
            context_sentences = []
            sentences = re.split(r'[.!?]+', self.full_text)
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in theme.keywords):
                    context_sentences.append(sentence.strip())
            
            if context_sentences:
                # Use most recent context
                theme.description = context_sentences[-1][:100] + "..."
    
    def _prune_themes(self):
        """Remove old or low-confidence themes"""
        current_time = time.time()
        to_remove = []
        
        for theme_name, theme in self.current_themes.items():
            # Remove if not mentioned recently and low frequency
            if (current_time - theme.last_mentioned > self.analysis_window * 2 and 
                theme.frequency < 3):
                to_remove.append(theme_name)
        
        for theme_name in to_remove:
            del self.current_themes[theme_name]
    
    def _quick_sentiment_analysis(self, text: str) -> float:
        """Quick sentiment analysis (-1 to 1)"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 
                         'love', 'like', 'happy', 'pleased', 'satisfied', 'success']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 
                         'angry', 'frustrated', 'disappointed', 'problem', 'issue', 'error']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def get_current_themes(self, min_confidence: float = 0.3) -> List[Theme]:
        """Get current themes above confidence threshold"""
        return [theme for theme in self.current_themes.values() 
                if theme.confidence >= min_confidence]
    
    def get_key_insights(self, last_n: int = 10) -> List[KeyInsight]:
        """Get most recent key insights"""
        return list(self.key_insights)[-last_n:]
    
    def get_sentiment_summary(self, duration: float = 300.0) -> Dict:
        """Get sentiment summary for recent duration"""
        current_time = time.time()
        recent_sentiments = [
            sentiment for sentiment, timestamp in self.sentiment_history
            if current_time - timestamp <= duration
        ]
        
        if not recent_sentiments:
            return {'average': 0.0, 'trend': 'neutral', 'count': 0}
        
        avg_sentiment = sum(recent_sentiments) / len(recent_sentiments)
        
        # Determine trend (compare first half vs second half)
        mid_point = len(recent_sentiments) // 2
        if mid_point > 0:
            first_half = sum(recent_sentiments[:mid_point]) / mid_point
            second_half = sum(recent_sentiments[mid_point:]) / (len(recent_sentiments) - mid_point)
            
            if second_half > first_half + 0.1:
                trend = 'improving'
            elif second_half < first_half - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'neutral'
        
        return {
            'average': avg_sentiment,
            'trend': trend,
            'count': len(recent_sentiments)
        }
    
    def get_analysis_summary(self) -> Dict:
        """Get comprehensive analysis summary"""
        themes = self.get_current_themes()
        insights = self.get_key_insights()
        sentiment = self.get_sentiment_summary()
        
        # Categorize insights
        categories = {}
        for insight in insights:
            cat = insight.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(insight)
        
        return {
            'themes': [
                {
                    'title': theme.title,
                    'keywords': theme.keywords,
                    'description': theme.description,
                    'confidence': theme.confidence,
                    'frequency': theme.frequency
                }
                for theme in sorted(themes, key=lambda x: x.confidence, reverse=True)
            ],
            'key_insights': {
                'total': len(insights),
                'by_category': {cat: len(items) for cat, items in categories.items()},
                'recent': [
                    {
                        'text': insight.text,
                        'category': insight.category,
                        'importance': insight.importance_score,
                        'timestamp': insight.timestamp
                    }
                    for insight in insights[-5:]  # Last 5 insights
                ]
            },
            'sentiment': sentiment,
            'analysis_window': self.analysis_window,
            'total_text_chunks': len(self.text_buffer)
        }
    
    def clear_analysis(self):
        """Clear all analysis data"""
        self.text_buffer.clear()
        self.full_text = ""
        self.current_themes.clear()
        self.key_insights.clear()
        self.sentiment_history.clear()
        print("🗑️  Analysis data cleared")