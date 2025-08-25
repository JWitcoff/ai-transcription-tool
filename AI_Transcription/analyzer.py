import os
import re
from typing import List, Dict, Optional
from collections import Counter
import numpy as np
from transformers import (
    pipeline, 
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM
)
import torch

class TextAnalyzer:
    """Handles text analysis, summarization, and theme extraction"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.summarizer = None
        self.sentiment_analyzer = None
        self.classifier = None
        
    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        Generate a summary of the input text
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            
        Returns:
            Summary string
        """
        if not text.strip():
            return "No text provided for summarization."
        
        # Load summarizer if not loaded
        if self.summarizer is None:
            self._load_summarizer()
        
        try:
            # Split text into chunks if too long
            chunks = self._split_text(text, max_chunk_size=1000)
            
            if len(chunks) == 1:
                # Single chunk - direct summarization
                summary = self.summarizer(chunks[0], 
                                        max_length=max_length, 
                                        min_length=min_length, 
                                        do_sample=False)[0]['summary_text']
            else:
                # Multiple chunks - summarize each then combine
                chunk_summaries = []
                for chunk in chunks:
                    chunk_summary = self.summarizer(chunk, 
                                                  max_length=max_length//len(chunks), 
                                                  min_length=min_length//len(chunks),
                                                  do_sample=False)[0]['summary_text']
                    chunk_summaries.append(chunk_summary)
                
                # Combine and summarize again
                combined_text = " ".join(chunk_summaries)
                summary = self.summarizer(combined_text,
                                        max_length=max_length,
                                        min_length=min_length,
                                        do_sample=False)[0]['summary_text']
            
            return summary.strip()
            
        except Exception as e:
            return f"Summarization failed: {str(e)}"
    
    def extract_themes(self, text: str, num_themes: int = 5) -> List[Dict]:
        """
        Extract key themes from text
        
        Args:
            text: Input text
            num_themes: Number of themes to extract
            
        Returns:
            List of theme dictionaries
        """
        if not text.strip():
            return []
        
        try:
            # Clean and preprocess text
            cleaned_text = self._clean_text(text)
            
            # Extract keywords using frequency analysis
            keywords = self._extract_keywords(cleaned_text, top_k=20)
            
            # Group keywords into themes using simple clustering
            themes = self._cluster_keywords_into_themes(keywords, text, num_themes)
            
            return themes
            
        except Exception as e:
            return [{"title": "Error", "description": f"Theme extraction failed: {str(e)}", "keywords": []}]
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of the text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not text.strip():
            return {"label": "NEUTRAL", "score": 0.0, "confidence": 0.0}
        
        # Load sentiment analyzer if not loaded
        if self.sentiment_analyzer is None:
            self._load_sentiment_analyzer()
        
        try:
            # Split text into chunks for analysis
            chunks = self._split_text(text, max_chunk_size=500)
            
            all_results = []
            for chunk in chunks:
                result = self.sentiment_analyzer(chunk)[0]
                all_results.append(result)
            
            # Aggregate results
            if len(all_results) == 1:
                sentiment_result = all_results[0]
            else:
                # Average the scores
                labels = [r['label'] for r in all_results]
                scores = [r['score'] for r in all_results]
                
                # Find most common label
                label_counts = Counter(labels)
                most_common_label = label_counts.most_common(1)[0][0]
                
                # Average score
                avg_score = np.mean(scores)
                
                sentiment_result = {
                    'label': most_common_label,
                    'score': avg_score
                }
            
            # Add additional analysis
            emotion = self._analyze_emotion(text)
            
            return {
                'label': sentiment_result['label'],
                'score': sentiment_result['score'],
                'confidence': sentiment_result['score'],
                'emotion': emotion
            }
            
        except Exception as e:
            return {
                'label': 'ERROR',
                'score': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_text_statistics(self, text: str) -> Dict:
        """
        Get basic statistics about the text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with text statistics
        """
        if not text.strip():
            return {}
        
        # Basic counts
        word_count = len(text.split())
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        sentence_count = len(re.findall(r'[.!?]+', text))
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Average calculations
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        avg_chars_per_word = char_count_no_spaces / max(word_count, 1)
        
        # Reading time estimate (average 200 words per minute)
        reading_time_minutes = word_count / 200
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'character_count_no_spaces': char_count_no_spaces,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'avg_words_per_sentence': round(avg_words_per_sentence, 1),
            'avg_chars_per_word': round(avg_chars_per_word, 1),
            'estimated_reading_time_minutes': round(reading_time_minutes, 1)
        }
    
    def _load_summarizer(self):
        """Load summarization model"""
        try:
            # Use a lightweight summarization model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if self.device == "cuda" else -1
            )
        except Exception:
            # Fallback to a smaller model
            try:
                self.summarizer = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6",
                    device=0 if self.device == "cuda" else -1
                )
            except Exception:
                # Final fallback - create a simple extractive summarizer
                self.summarizer = self._create_extractive_summarizer()
    
    def _load_sentiment_analyzer(self):
        """Load sentiment analysis model"""
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
        except Exception:
            # Fallback to default model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                device=0 if self.device == "cuda" else -1
            )
    
    def _create_extractive_summarizer(self):
        """Create a simple extractive summarizer as fallback"""
        def extractive_summarize(text, max_length=150, min_length=30, **kwargs):
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 3:
                return [{"summary_text": " ".join(sentences)}]
            
            # Simple scoring based on sentence length and position
            scores = []
            for i, sentence in enumerate(sentences):
                # Prefer sentences that are not too short or too long
                length_score = 1.0 if 10 <= len(sentence.split()) <= 30 else 0.5
                # Prefer sentences from the beginning and end
                position_score = 1.0 if i < len(sentences) * 0.3 or i > len(sentences) * 0.7 else 0.8
                scores.append(length_score * position_score)
            
            # Select top sentences
            indexed_scores = list(enumerate(scores))
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 3 sentences, maintain original order
            selected_indices = sorted([x[0] for x in indexed_scores[:3]])
            summary_sentences = [sentences[i] for i in selected_indices]
            
            summary = ". ".join(summary_sentences) + "."
            return [{"summary_text": summary}]
        
        return extractive_summarize
    
    def _split_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        return text.strip()
    
    def _extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """Extract keywords using simple frequency analysis"""
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'within', 'without', 'around', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'our', 'their', 'what', 'which', 'who', 'when',
            'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'just', 'now', 'here', 'there', 'then', 'also', 'well', 'like', 'get',
            'go', 'come', 'see', 'know', 'think', 'say', 'tell', 'want', 'need', 'make', 'take'
        }
        
        # Extract words and count frequency
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter([word for word in words if word not in stop_words])
        
        # Return top keywords
        return [word for word, _ in word_freq.most_common(top_k)]
    
    def _cluster_keywords_into_themes(self, keywords: List[str], text: str, num_themes: int) -> List[Dict]:
        """Simple keyword clustering into themes"""
        if not keywords:
            return []
        
        # Simple approach: group keywords by co-occurrence
        themes = []
        used_keywords = set()
        
        # Create themes by finding related keywords
        sentences = re.split(r'[.!?]+', text.lower())
        
        for i in range(min(num_themes, len(keywords))):
            if len(used_keywords) >= len(keywords):
                break
                
            # Find an unused keyword
            primary_keyword = None
            for keyword in keywords:
                if keyword not in used_keywords:
                    primary_keyword = keyword
                    break
            
            if not primary_keyword:
                break
            
            # Find related keywords (co-occurring in same sentences)
            related_keywords = [primary_keyword]
            used_keywords.add(primary_keyword)
            
            for sentence in sentences:
                if primary_keyword in sentence:
                    for keyword in keywords:
                        if (keyword not in used_keywords and 
                            keyword in sentence and 
                            len(related_keywords) < 5):
                            related_keywords.append(keyword)
                            used_keywords.add(keyword)
            
            # Create theme
            theme_title = f"Theme {i+1}: {primary_keyword.title()}"
            theme_description = self._generate_theme_description(related_keywords, text)
            
            themes.append({
                "title": theme_title,
                "description": theme_description,
                "keywords": related_keywords
            })
        
        return themes
    
    def _generate_theme_description(self, keywords: List[str], text: str) -> str:
        """Generate a description for a theme based on keywords"""
        # Find sentences containing the keywords
        sentences = re.split(r'[.!?]+', text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            # Return the first relevant sentence as description
            return relevant_sentences[0][:200] + "..." if len(relevant_sentences[0]) > 200 else relevant_sentences[0]
        else:
            return f"This theme relates to {', '.join(keywords[:3])} and related concepts."
    
    def _analyze_emotion(self, text: str) -> str:
        """Simple emotion analysis based on keywords"""
        emotion_keywords = {
            'joy': ['happy', 'joy', 'excited', 'pleased', 'delighted', 'cheerful', 'glad'],
            'sadness': ['sad', 'depressed', 'unhappy', 'melancholy', 'sorrow', 'grief'],
            'anger': ['angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'nervous'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'stunned'],
            'trust': ['trust', 'confidence', 'faith', 'believe', 'reliable'],
            'anticipation': ['excited', 'eager', 'hopeful', 'optimistic', 'looking forward']
        }
        
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        else:
            return 'neutral'