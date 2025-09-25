"""
Fact Extraction Module - Named Entity Recognition and Fact Validation
Provides grounded, extractive analysis to prevent AI hallucinations
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from collections import Counter, defaultdict

@dataclass
class ExtractedFact:
    """Represents a validated fact extracted from transcript"""
    fact_type: str  # 'date', 'number', 'event', 'person', 'company', 'quote'
    content: str    # The actual fact text
    context: str    # Surrounding context from transcript
    confidence: float  # Confidence score 0-1
    source_segment: str  # Original transcript segment
    start_pos: int   # Character position in transcript
    end_pos: int     # End character position

@dataclass
class ExtractedQuote:
    """Represents a quote extracted from transcript"""
    text: str
    speaker: Optional[str]
    context: str
    is_memorable: bool  # Based on impact scoring

class FactExtractor:
    """Extracts and validates factual information from transcripts"""

    def __init__(self):
        # Initialize joke/unrealistic term blacklist
        self.joke_blacklist = {
            'iphone 17', 'iphone 18', 'iphone 20', 'iphone 25', 'iphone 30',
            'apple vision pro 2', 'vision pro 3', 'tesla phone', 'google phone 2',
            'windows 20', 'macos 20', 'chrome os 2', 'android 20',
            'chatgpt 10', 'gpt-10', 'claude 10', 'gemini 10'
        }

        # Realistic event/announcement patterns
        self.event_patterns = [
            r'(\w+\s*\w*\s+20\d{2})',  # Events with years
            r'(\w+Con\s+20\d{2})',      # Convention names
            r'(\w+\s+conference)',       # Conference names
            r'(\w+\s+summit)',          # Summit names
            r'(\w+\s+announcement)',     # Announcements
            r'(launch\s+of\s+\w+)',     # Product launches
        ]

        # Numeric patterns for metrics
        self.metric_patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|thousand|k|m|b))',
            r'(\d+(?:\.\d+)?%)',  # Percentages
            r'(\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|thousand|k|m|b))?)',  # Currency
            r'(\d+(?:,\d{3})*(?:\.\d+)?\s+(?:users|subscribers|views|downloads|sales))',  # Counts
        ]

        # Company/organization patterns
        self.company_patterns = [
            r'\b(Google|Apple|Microsoft|Amazon|Meta|Facebook|Netflix|Tesla|OpenAI|Anthropic)\b',
            r'\b([A-Z][a-zA-Z]+\s+(?:Inc|Corp|LLC|Ltd|Company))\b',
            r'\b([A-Z][a-zA-Z]*[A-Z][a-zA-Z]*)\b',  # CamelCase company names
        ]

    def extract_all_facts(self, transcript: str, speaker_segments: Optional[List[Dict]] = None) -> Dict:
        """
        Extract all factual information from transcript

        Args:
            transcript: Full transcript text
            speaker_segments: Optional speaker diarization data

        Returns:
            Dictionary with categorized facts and validation results
        """
        # Clean transcript for better processing
        cleaned_transcript = self._clean_transcript(transcript)

        # Extract different types of facts
        facts = {
            'dates_and_events': self._extract_dates_and_events(cleaned_transcript),
            'metrics_and_numbers': self._extract_metrics(cleaned_transcript),
            'companies_and_entities': self._extract_entities(cleaned_transcript),
            'quotes': self._extract_quotes(cleaned_transcript, speaker_segments),
            'factual_claims': self._extract_factual_claims(cleaned_transcript),
        }

        # Validate all extracted facts
        validated_facts = self._validate_facts(facts, cleaned_transcript)

        # Generate fact-based themes
        themes = self._generate_factual_themes(validated_facts)

        return {
            'facts': validated_facts,
            'themes': themes,
            'validation_summary': self._create_validation_summary(validated_facts),
            'confidence_score': self._calculate_overall_confidence(validated_facts)
        }

    def _clean_transcript(self, transcript: str) -> str:
        """Clean transcript for better fact extraction"""
        # Remove speaker tags if present
        transcript = re.sub(r'^(Speaker [A-Z]:?|[A-Z]+:)', '', transcript, flags=re.MULTILINE)
        # Remove timestamps
        transcript = re.sub(r'\[\d{2}:\d{2}(?::\d{2})?\]', '', transcript)
        # Remove extra whitespace
        transcript = re.sub(r'\s+', ' ', transcript)
        return transcript.strip()

    def _extract_dates_and_events(self, transcript: str) -> List[ExtractedFact]:
        """Extract dates, events, and announcements"""
        facts = []

        # Date patterns
        date_patterns = [
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # MM/DD/YYYY
            r'\b(\d{4}-\d{2}-\d{2})\b',      # YYYY-MM-DD
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})\b',
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                context = self._get_context(transcript, match.start(), match.end())
                facts.append(ExtractedFact(
                    fact_type='date',
                    content=match.group(1),
                    context=context,
                    confidence=0.9,
                    source_segment=context,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))

        # Event patterns
        for pattern in self.event_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                event_text = match.group(1)
                # Validate it's not a joke term
                if not self._is_blacklisted(event_text):
                    context = self._get_context(transcript, match.start(), match.end())
                    facts.append(ExtractedFact(
                        fact_type='event',
                        content=event_text,
                        context=context,
                        confidence=0.8,
                        source_segment=context,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))

        return facts

    def _extract_metrics(self, transcript: str) -> List[ExtractedFact]:
        """Extract numerical metrics and data points"""
        facts = []

        for pattern in self.metric_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                metric_text = match.group(1)
                context = self._get_context(transcript, match.start(), match.end())

                # Higher confidence for specific contexts
                confidence = 0.9 if any(word in context.lower() for word in
                                      ['revenue', 'profit', 'sales', 'users', 'subscribers']) else 0.7

                facts.append(ExtractedFact(
                    fact_type='metric',
                    content=metric_text,
                    context=context,
                    confidence=confidence,
                    source_segment=context,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))

        return facts

    def _extract_entities(self, transcript: str) -> List[ExtractedFact]:
        """Extract companies, organizations, and named entities"""
        facts = []

        for pattern in self.company_patterns:
            for match in re.finditer(pattern, transcript):
                entity_text = match.group(1) if match.groups() else match.group(0)
                context = self._get_context(transcript, match.start(), match.end())

                facts.append(ExtractedFact(
                    fact_type='entity',
                    content=entity_text,
                    context=context,
                    confidence=0.8,
                    source_segment=context,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))

        return facts

    def _extract_quotes(self, transcript: str, speaker_segments: Optional[List[Dict]] = None) -> List[ExtractedQuote]:
        """Extract memorable quotes and direct statements"""
        quotes = []

        # Pattern for quoted text
        quote_patterns = [
            r'"([^"]{20,200})"',  # Text in quotes, 20-200 chars
            r"'([^']{20,200})'",  # Text in single quotes
        ]

        for pattern in quote_patterns:
            for match in re.finditer(pattern, transcript):
                quote_text = match.group(1)
                context = self._get_context(transcript, match.start(), match.end())

                # Determine speaker if possible
                speaker = self._identify_speaker(match.start(), speaker_segments) if speaker_segments else None

                # Score memorability based on impact words
                is_memorable = self._score_quote_memorability(quote_text)

                quotes.append(ExtractedQuote(
                    text=quote_text,
                    speaker=speaker,
                    context=context,
                    is_memorable=is_memorable
                ))

        # Also extract impactful statements without quotes
        impact_patterns = [
            r'\b(The key is to [^.!?]{10,100}[.!?])',
            r'\b(What I learned is [^.!?]{10,100}[.!?])',
            r'\b(The most important thing [^.!?]{10,100}[.!?])',
            r'\b(Here\'s the secret [^.!?]{10,100}[.!?])',
        ]

        for pattern in impact_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                quote_text = match.group(1)
                context = self._get_context(transcript, match.start(), match.end())
                speaker = self._identify_speaker(match.start(), speaker_segments) if speaker_segments else None

                quotes.append(ExtractedQuote(
                    text=quote_text,
                    speaker=speaker,
                    context=context,
                    is_memorable=True  # These patterns are inherently memorable
                ))

        return quotes

    def _extract_factual_claims(self, transcript: str) -> List[ExtractedFact]:
        """Extract specific factual claims that can be verified"""
        facts = []

        # Patterns for factual statements
        claim_patterns = [
            r'\b(according to [^.!?]{10,100}[.!?])',
            r'\b(studies show [^.!?]{10,100}[.!?])',
            r'\b(research indicates [^.!?]{10,100}[.!?])',
            r'\b([A-Z]\w+ announced [^.!?]{10,100}[.!?])',
            r'\b(the data shows [^.!?]{10,100}[.!?])',
        ]

        for pattern in claim_patterns:
            for match in re.finditer(pattern, transcript, re.IGNORECASE):
                claim_text = match.group(1)

                # Skip if contains blacklisted terms
                if not self._is_blacklisted(claim_text):
                    context = self._get_context(transcript, match.start(), match.end())
                    facts.append(ExtractedFact(
                        fact_type='claim',
                        content=claim_text,
                        context=context,
                        confidence=0.7,  # Lower confidence, needs verification
                        source_segment=context,
                        start_pos=match.start(),
                        end_pos=match.end()
                    ))

        return facts

    def _validate_facts(self, facts: Dict[str, List], transcript: str) -> Dict[str, List]:
        """Validate extracted facts for accuracy and reasonableness"""
        validated = {}

        for category, fact_list in facts.items():
            if category == 'quotes':
                # Quotes are validated differently
                validated[category] = [q for q in fact_list if self._is_reasonable_quote(q.text)]
            else:
                validated[category] = []
                for fact in fact_list:
                    # Check against blacklist
                    if not self._is_blacklisted(fact.content):
                        # Check if fact appears in transcript (source validation)
                        if self._validate_source(fact, transcript):
                            # Apply confidence threshold
                            if fact.confidence >= 0.6:
                                validated[category].append(fact)

        return validated

    def _generate_factual_themes(self, validated_facts: Dict) -> List[Dict]:
        """Generate themes based on extracted facts rather than speculation"""
        themes = []

        # Theme 1: Key Events and Announcements
        events = validated_facts.get('dates_and_events', [])
        if events:
            event_content = [f.content for f in events if f.fact_type == 'event']
            if event_content:
                themes.append({
                    'title': 'Key Events & Announcements',
                    'description': f"Discussion covers {len(event_content)} events: {', '.join(event_content[:3])}",
                    'keywords': event_content[:5],
                    'evidence_count': len(event_content)
                })

        # Theme 2: Business Metrics and Data
        metrics = validated_facts.get('metrics_and_numbers', [])
        if metrics:
            metric_types = self._categorize_metrics(metrics)
            if metric_types:
                top_category = max(metric_types.items(), key=lambda x: len(x[1]))[0]
                themes.append({
                    'title': f'Business Metrics: {top_category.title()}',
                    'description': f"Contains {len(metrics)} data points focused on {top_category}",
                    'keywords': [f.content for f in metrics[:5]],
                    'evidence_count': len(metrics)
                })

        # Theme 3: Companies and Organizations
        entities = validated_facts.get('companies_and_entities', [])
        if entities:
            company_names = list(set(f.content for f in entities))
            themes.append({
                'title': 'Companies & Organizations',
                'description': f"Mentions {len(company_names)} organizations: {', '.join(company_names[:3])}",
                'keywords': company_names[:5],
                'evidence_count': len(entities)
            })

        # Theme 4: Key Insights and Quotes
        quotes = validated_facts.get('quotes', [])
        memorable_quotes = [q for q in quotes if q.is_memorable]
        if memorable_quotes:
            themes.append({
                'title': 'Key Insights & Memorable Quotes',
                'description': f"Contains {len(memorable_quotes)} impactful statements and insights",
                'keywords': ['insights', 'quotes', 'key points'],
                'evidence_count': len(memorable_quotes)
            })

        return themes

    def _get_context(self, transcript: str, start: int, end: int, window: int = 100) -> str:
        """Get surrounding context for a match"""
        context_start = max(0, start - window)
        context_end = min(len(transcript), end + window)
        return transcript[context_start:context_end].strip()

    def _is_blacklisted(self, text: str) -> bool:
        """Check if text contains blacklisted joke terms"""
        return any(joke in text.lower() for joke in self.joke_blacklist)

    def _validate_source(self, fact: ExtractedFact, transcript: str) -> bool:
        """Validate that fact actually appears in transcript"""
        # Simple check - fact content should be findable in transcript
        return fact.content.lower() in transcript.lower()

    def _is_reasonable_quote(self, quote_text: str) -> bool:
        """Check if a quote is reasonable (not truncated, makes sense)"""
        # Must be complete sentences
        if not quote_text.strip().endswith(('.', '!', '?')):
            return False
        # Must have reasonable length
        if len(quote_text.split()) < 3:
            return False
        # Must not contain obvious truncation
        if quote_text.strip().endswith('...'):
            return False
        return True

    def _identify_speaker(self, position: int, speaker_segments: Optional[List[Dict]]) -> Optional[str]:
        """Identify speaker at given position if speaker data available"""
        if not speaker_segments:
            return None

        # Find segment containing this position
        for segment in speaker_segments:
            if segment.get('start_pos', 0) <= position <= segment.get('end_pos', 0):
                return segment.get('speaker')

        return None

    def _score_quote_memorability(self, quote_text: str) -> bool:
        """Score quote for memorability based on impact words"""
        impact_words = {
            'key', 'important', 'secret', 'learned', 'discovery', 'insight',
            'critical', 'essential', 'fundamental', 'breakthrough', 'game-changer',
            'surprising', 'shocking', 'amazing', 'incredible', 'powerful'
        }

        quote_lower = quote_text.lower()
        impact_count = sum(1 for word in impact_words if word in quote_lower)

        # Memorable if contains impact words or is a strong statement
        return impact_count >= 2 or any(phrase in quote_lower for phrase in
                                      ['the key is', 'what i learned', 'the secret', 'most important'])

    def _categorize_metrics(self, metrics: List[ExtractedFact]) -> Dict[str, List[ExtractedFact]]:
        """Categorize metrics by type"""
        categories = defaultdict(list)

        for metric in metrics:
            context_lower = metric.context.lower()
            if any(word in context_lower for word in ['revenue', 'profit', 'sales', 'dollar']):
                categories['financial'].append(metric)
            elif any(word in context_lower for word in ['users', 'subscribers', 'audience']):
                categories['audience'].append(metric)
            elif any(word in context_lower for word in ['views', 'clicks', 'engagement']):
                categories['engagement'].append(metric)
            else:
                categories['general'].append(metric)

        return dict(categories)

    def _create_validation_summary(self, validated_facts: Dict) -> Dict:
        """Create summary of validation results"""
        total_facts = sum(len(facts) for facts in validated_facts.values())

        return {
            'total_facts_extracted': total_facts,
            'facts_by_category': {k: len(v) for k, v in validated_facts.items()},
            'validation_notes': 'All facts validated against source transcript and blacklist filtered'
        }

    def _calculate_overall_confidence(self, validated_facts: Dict) -> float:
        """Calculate overall confidence in extracted facts"""
        all_facts = []
        for category, facts in validated_facts.items():
            if category != 'quotes':  # Quotes don't have confidence scores
                all_facts.extend(facts)

        if not all_facts:
            return 0.0

        return sum(fact.confidence for fact in all_facts) / len(all_facts)

def extract_grounded_summary(transcript: str, max_sentences: int = 5) -> str:
    """
    Create an extractive summary using only actual sentences from transcript
    Prevents hallucination by never generating new content
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) >= 5]

    if len(sentences) <= max_sentences:
        return '. '.join(sentences) + '.'

    # Score sentences based on:
    # 1. Length (not too short, not too long)
    # 2. Position (beginning and end are important)
    # 3. Content indicators (factual words)

    scored_sentences = []
    factual_indicators = {'according', 'data', 'study', 'research', 'announced', 'reported', 'shows', 'indicates'}

    for i, sentence in enumerate(sentences):
        words = sentence.split()

        # Length score (prefer 10-25 words)
        length_score = 1.0 if 10 <= len(words) <= 25 else 0.5

        # Position score (prefer beginning and end)
        position_score = 1.0 if i < len(sentences) * 0.3 or i > len(sentences) * 0.7 else 0.7

        # Content score (bonus for factual indicators)
        content_score = 1.0 + 0.2 * sum(1 for word in words if word.lower() in factual_indicators)

        total_score = length_score * position_score * content_score
        scored_sentences.append((i, sentence, total_score))

    # Select top sentences, maintain original order
    scored_sentences.sort(key=lambda x: x[2], reverse=True)
    selected = sorted([(x[0], x[1]) for x in scored_sentences[:max_sentences]])

    summary_sentences = [sentence for _, sentence in selected]
    return '. '.join(summary_sentences) + '.'