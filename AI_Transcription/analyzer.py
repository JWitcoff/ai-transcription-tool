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
from fact_extractor import FactExtractor, extract_grounded_summary

class TextAnalyzer:
    """Handles text analysis, summarization, and theme extraction"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.summarizer = None
        self.sentiment_analyzer = None
        self.classifier = None
        self.fact_extractor = FactExtractor()
        self.use_extractive_summary = True  # Use fact-grounded summarization
        
    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        Generate a narrative summary with structured analysis in two-part format

        Args:
            text: Input text to summarize
            max_length: Maximum length of summary (converted to sentence count)
            min_length: Minimum length of summary (converted to sentence count)

        Returns:
            Two-part summary: SUMMARY (narrative) + ANALYSIS (structured)
        """
        if not text.strip():
            return "No text provided for summarization."

        try:
            # Extract facts first for grounding
            fact_analysis = self.fact_extractor.extract_all_facts(text)

            # Generate narrative summary from facts
            narrative_summary = self._generate_narrative_summary(text, fact_analysis)

            # Generate structured analysis
            structured_analysis = self._generate_structured_analysis(fact_analysis)

            # Combine in required format
            if structured_analysis.strip():
                return f"**SUMMARY**\n{narrative_summary}\n\n**ANALYSIS**\n{structured_analysis}"
            else:
                return f"**SUMMARY**\n{narrative_summary}"

        except Exception as e:
            print(f"Fact-grounded summarization failed, using fallback: {e}")
            # Fallback to extractive approach
            return self._fallback_summarize(text, max_length, min_length)

    def _generate_narrative_summary(self, text: str, fact_analysis: Dict) -> str:
        """Generate 3-6 sentence narrative prose from extracted facts"""
        facts = fact_analysis.get('facts', {})

        # Collect key facts for narrative
        events = facts.get('dates_and_events', [])
        metrics = facts.get('metrics_and_numbers', [])
        entities = facts.get('companies_and_entities', [])
        quotes = facts.get('quotes', [])

        # Build narrative sentences with concrete facts
        sentences = []

        # Add event-based sentences
        for event in events[:2]:  # Use top 2 events
            if hasattr(event, 'content') and hasattr(event, 'context'):
                sentences.append(f"{event.context.strip()}")

        # Add metric-based sentences
        for metric in metrics[:2]:  # Use top 2 metrics
            if hasattr(metric, 'content') and hasattr(metric, 'context'):
                sentences.append(f"{metric.context.strip()}")

        # Add entity-based context if available
        if entities:
            entity_names = [e.content for e in entities[:3] if hasattr(e, 'content')]
            if entity_names:
                # Look for context in the original text
                text_lower = text.lower()
                for entity in entity_names:
                    entity_lower = entity.lower()
                    # Find sentences containing the entity
                    text_sentences = re.split(r'[.!?]+', text)
                    for sent in text_sentences:
                        if entity_lower in sent.lower() and len(sent.strip()) > 20:
                            sentences.append(sent.strip())
                            break

        # Add memorable quotes if available
        memorable_quotes = [q for q in quotes if hasattr(q, 'is_memorable') and q.is_memorable]
        for quote in memorable_quotes[:1]:  # Use 1 memorable quote
            if hasattr(quote, 'text') and hasattr(quote, 'speaker'):
                speaker_text = f" ({quote.speaker})" if quote.speaker else ""
                sentences.append(f'"{quote.text}"{speaker_text}')

        # If we don't have enough facts, fall back to extractive summary
        if len(sentences) < 3:
            try:
                extractive_summary = extract_grounded_summary(text, max_sentences=4)
                # Split into sentences and use them
                extract_sentences = re.split(r'[.!?]+', extractive_summary)
                sentences.extend([s.strip() for s in extract_sentences if s.strip()])
            except:
                # Ultimate fallback - use first few sentences of text
                text_sentences = re.split(r'[.!?]+', text)
                sentences.extend([s.strip() for s in text_sentences[:4] if s.strip()])

        # Limit to 3-6 sentences and clean up
        narrative_sentences = []
        for sent in sentences[:6]:
            if sent and len(sent) > 10:  # Skip very short fragments
                # Clean up the sentence
                clean_sent = sent.strip()
                if not clean_sent.endswith('.'):
                    clean_sent += '.'
                narrative_sentences.append(clean_sent)

        # Ensure we have at least 3 sentences
        while len(narrative_sentences) < 3 and len(sentences) > len(narrative_sentences):
            additional = sentences[len(narrative_sentences)].strip()
            if additional and len(additional) > 5:
                if not additional.endswith('.'):
                    additional += '.'
                narrative_sentences.append(additional)

        return ' '.join(narrative_sentences[:6])  # Max 6 sentences

    def _generate_structured_analysis(self, fact_analysis: Dict) -> str:
        """Generate structured analysis with deduplicated entities"""
        facts = fact_analysis.get('facts', {})

        # Collect and deduplicate entities by category
        categories = {}

        # Events
        events = facts.get('dates_and_events', [])
        if events:
            event_names = [e.content for e in events if hasattr(e, 'content')]
            event_names = self._deduplicate_entities(event_names)
            if event_names:
                categories['Events'] = event_names[:5]

        # Metrics
        metrics = facts.get('metrics_and_numbers', [])
        if metrics:
            metric_items = []
            for m in metrics:
                if hasattr(m, 'content') and hasattr(m, 'context'):
                    # Combine metric with context for better understanding
                    context_short = m.context[:50] + "..." if len(m.context) > 50 else m.context
                    metric_items.append(f"{m.content} ({context_short})")
            if metric_items:
                categories['Metrics'] = metric_items[:5]

        # Companies/Entities
        entities = facts.get('companies_and_entities', [])
        if entities:
            entity_names = [e.content for e in entities if hasattr(e, 'content')]
            entity_names = self._deduplicate_entities(entity_names)
            if entity_names:
                categories['Entities'] = entity_names[:5]

        # Format as structured list
        analysis_lines = []
        for category, items in categories.items():
            if items:
                items_str = ', '.join(items)
                analysis_lines.append(f"- {category}: {items_str}")

        return '\n'.join(analysis_lines)

    def _deduplicate_entities(self, entities: List[str]) -> List[str]:
        """Remove duplicate and similar entities using fuzzy matching"""
        if not entities:
            return []

        # Normalize entities for comparison
        normalized_entities = []
        for entity in entities:
            # Basic normalization
            normalized = re.sub(r'[^\w\s]', '', entity.lower().strip())
            normalized = re.sub(r'\s+', ' ', normalized)
            normalized_entities.append((entity, normalized))

        # Remove duplicates and similar items
        unique_entities = []
        seen_normalized = set()

        for original, normalized in normalized_entities:
            # Check for exact matches first
            if normalized in seen_normalized:
                continue

            # Check for fuzzy matches (simple substring approach)
            is_similar = False
            for seen in seen_normalized:
                # If one is substring of another (with some tolerance)
                if (len(normalized) > 3 and normalized in seen) or \
                   (len(seen) > 3 and seen in normalized):
                    # Check if they're similar enough (length difference)
                    length_ratio = min(len(normalized), len(seen)) / max(len(normalized), len(seen))
                    if length_ratio > 0.7:  # 70% similarity threshold
                        is_similar = True
                        break

            if not is_similar:
                unique_entities.append(original)
                seen_normalized.add(normalized)

        return unique_entities

    def _fallback_summarize(self, text: str, max_length: int, min_length: int) -> str:
        """Fallback summary when fact extraction fails"""
        try:
            # Use simple extractive approach
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

            # Take first few sentences as summary
            summary_sentences = sentences[:4]
            narrative = '. '.join(summary_sentences) + '.'

            return f"**SUMMARY**\n{narrative}"
        except:
            return f"**SUMMARY**\nUnable to generate summary from provided text."

    def _generative_summarize(self, text: str, max_length: int, min_length: int) -> str:
        """
        Original generative summarization (with hallucination risk)
        Only used as fallback when extractive fails
        """
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
    
    def extract_themes(self, text: str, num_themes: int = 5) -> str:
        """
        Extract structured categories with deduplicated entities

        Args:
            text: Input text
            num_themes: Number of categories to extract (kept for compatibility)

        Returns:
            Structured analysis string in ANALYSIS format
        """
        if not text.strip():
            return ""

        try:
            # Use fact extractor for grounded analysis
            fact_analysis = self.fact_extractor.extract_all_facts(text)
            return self._generate_structured_analysis(fact_analysis)

        except Exception as e:
            return f"- Error: Theme extraction failed: {str(e)}"
    
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
    
    def _extract_keyword_themes_improved(self, text: str, num_themes: int) -> List[Dict]:
        """Improved keyword-based theme extraction with better validation"""
        # Clean and preprocess text
        cleaned_text = self._clean_text(text)

        # Extract keywords using frequency analysis
        keywords = self._extract_keywords(cleaned_text, top_k=20)

        if not keywords:
            return []

        # Group keywords into meaningful themes with better labeling
        themes = self._cluster_keywords_into_themes_improved(keywords, text, num_themes)

        return themes

    def _cluster_keywords_into_themes_improved(self, keywords: List[str], text: str, num_themes: int) -> List[Dict]:
        """Improved keyword clustering with specific theme names instead of generic labels"""
        if not keywords:
            return []

        # Define domain-specific theme categories based on common patterns
        theme_categories = {
            'business': ['business', 'company', 'revenue', 'profit', 'strategy', 'market', 'customer'],
            'technology': ['technology', 'software', 'digital', 'platform', 'system', 'tool', 'app'],
            'content': ['content', 'video', 'channel', 'audience', 'creator', 'youtube', 'social'],
            'growth': ['growth', 'scale', 'increase', 'improve', 'optimize', 'expand', 'develop'],
            'process': ['process', 'method', 'approach', 'framework', 'system', 'workflow', 'step']
        }

        # Categorize keywords into theme buckets
        theme_buckets = {category: [] for category in theme_categories}
        uncategorized = []

        for keyword in keywords:
            categorized = False
            for category, category_keywords in theme_categories.items():
                if any(cat_word in keyword.lower() or keyword.lower() in cat_word
                      for cat_word in category_keywords):
                    theme_buckets[category].append(keyword)
                    categorized = True
                    break
            if not categorized:
                uncategorized.append(keyword)

        # Create themes from populated buckets
        themes = []
        sentences = re.split(r'[.!?]+', text.lower())

        for category, category_keywords in theme_buckets.items():
            if category_keywords and len(themes) < num_themes:
                # Generate specific theme title based on category
                theme_title = self._generate_specific_theme_title(category, category_keywords, text)
                theme_description = self._generate_theme_description_improved(category_keywords, text)

                themes.append({
                    "title": theme_title,
                    "description": theme_description,
                    "keywords": category_keywords[:5],
                    "category": category,
                    "evidence_count": len(category_keywords)
                })

        # Add uncategorized keywords as general themes if needed
        if len(themes) < num_themes and uncategorized:
            remaining_slots = num_themes - len(themes)
            for i in range(min(remaining_slots, len(uncategorized) // 3)):
                start_idx = i * 3
                theme_keywords = uncategorized[start_idx:start_idx + 3]

                theme_title = f"Key Topics: {', '.join(theme_keywords[:2])}"
                theme_description = self._generate_theme_description_improved(theme_keywords, text)

                themes.append({
                    "title": theme_title,
                    "description": theme_description,
                    "keywords": theme_keywords,
                    "category": "general",
                    "evidence_count": len(theme_keywords)
                })

        return themes

    def _generate_specific_theme_title(self, category: str, keywords: List[str], text: str) -> str:
        """Generate specific theme titles instead of generic ones"""
        # Find the most prominent keyword in context
        keyword_counts = {}
        text_lower = text.lower()

        for keyword in keywords:
            keyword_counts[keyword] = text_lower.count(keyword.lower())

        if keyword_counts:
            primary_keyword = max(keyword_counts, key=keyword_counts.get)

            # Generate specific titles based on category and primary keyword
            if category == 'business':
                return f"Business Strategy: {primary_keyword.title()}"
            elif category == 'technology':
                return f"Technology & Tools: {primary_keyword.title()}"
            elif category == 'content':
                return f"Content Strategy: {primary_keyword.title()}"
            elif category == 'growth':
                return f"Growth & Optimization: {primary_keyword.title()}"
            elif category == 'process':
                return f"Methods & Frameworks: {primary_keyword.title()}"

        # Fallback to category name
        return f"{category.title()} Discussion"

    def _generate_theme_description_improved(self, keywords: List[str], text: str) -> str:
        """Generate factual theme descriptions based on actual content"""
        # Find sentences containing the keywords
        sentences = re.split(r'[.!?]+', text)
        relevant_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            keyword_matches = sum(1 for keyword in keywords if keyword in sentence_lower)
            if keyword_matches >= 2:  # Sentence must contain multiple keywords
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            # Return the most comprehensive sentence (longest with multiple keywords)
            best_sentence = max(relevant_sentences, key=lambda s: len(s.split()))
            return best_sentence[:200] + "..." if len(best_sentence) > 200 else best_sentence
        else:
            # Fallback: count keyword frequency
            keyword_freq = Counter()
            for keyword in keywords:
                keyword_freq[keyword] = text.lower().count(keyword.lower())

            top_keywords = [k for k, _ in keyword_freq.most_common(3)]
            return f"Discussion includes {len(keywords)} related topics: {', '.join(top_keywords)}"
    
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