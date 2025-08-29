"""
Smart guards against rubric leakage and fragment artifacts
Conservative validation that preserves valid content while blocking junk
"""

import re
from typing import List, Set
from enum import Enum


class GuardResult(Enum):
    VALID = "valid"
    RUBRIC_LEAKAGE = "rubric_leakage"
    MID_SENTENCE = "mid_sentence"
    TOO_SHORT = "too_short"
    NO_CONTENT = "no_content"
    SPEAKER_ARTIFACT = "speaker_artifact"


# Known rubric artifacts that should never appear in clean output
BAD_HEADERS = {
    "CORE FRAMEWORKS", "PSYCHOLOGY PRINCIPLES", "PROVEN TACTICS",
    "QUICK START", "QUALITY CHECK", "ACTIONABLE PLAYBOOK",
    "KEY FRAMEWORKS", "PSYCHOLOGY", "FRAMEWORKS", "SYSTEMS",
    "TEMPORAL STRATEGIES", "AUTHENTICITY", "CASE STUDIES",
    "NEXT STEPS", "RECOMMENDATIONS", "ANALYSIS", "SUMMARY",
    "COVERAGE", "GAPS", "FOUND", "EXTRACTION", "RESULTS"
}

# Patterns for detecting sentence fragments that start incorrectly
_APOS_START = re.compile(r"^'[a-z]\b")  # starts with "'m", "'s", "'re", etc.
_LOWERCASE_START = re.compile(r"^[a-z]")  # starts with lowercase (likely fragment)
_CONJUNCTION_START = re.compile(r"^(?:and|but|or|so|yet|for|nor)\b", re.IGNORECASE)  # conjunction starts

# Common English stopwords for content validation
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", 
    "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", 
    "had", "do", "does", "did", "will", "would", "could", "should", "may", 
    "might", "can", "this", "that", "these", "those", "i", "you", "he", 
    "she", "it", "we", "they", "me", "him", "her", "us", "them"
}


def has_rubric_leakage(text: str) -> bool:
    """
    Detect if text contains rubric artifact headers
    
    Args:
        text: Text to check for rubric leakage
        
    Returns:
        True if rubric artifacts detected
    """
    # Clean lines and check against known bad headers
    lines = [re.sub(r"[^A-Z ]", "", line.upper().strip()) for line in text.splitlines()]
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # Direct match
        if clean_line in BAD_HEADERS:
            return True
            
        # Partial match for variations
        if any(bad in clean_line for bad in ["FRAMEWORK", "PSYCHOLOGY", "PLAYBOOK", "QUALITY CHECK"]):
            if len(clean_line) < 50:  # Short lines are more likely to be headers
                return True
    
    # Check for the specific broken pattern from our analysis
    if "## 🔧 CORE FRAMEWORKS" in text or "## 🧠 PSYCHOLOGY PRINCIPLES" in text:
        return True
        
    # Check for numbered framework patterns that are artifacts
    framework_pattern = re.compile(r"###\s+'[a-z].*?'")
    if framework_pattern.search(text):
        return True
    
    return False


def looks_like_mid_sentence(fragment: str, context_window: str = "") -> bool:
    """
    Conservative detection of sentence fragments
    
    Args:
        fragment: Text fragment to validate
        context_window: Surrounding text for context (if available)
        
    Returns:
        True if fragment appears to be mid-sentence
    """
    frag = fragment.strip()
    
    if not frag:
        return True
    
    # Check for apostrophe contractions at start (but be conservative)
    if _APOS_START.search(frag):
        # Only reject if we have context showing this isn't start of sentence
        if context_window:
            # Look for preceding sentence-final punctuation
            context_clean = context_window.strip()
            if context_clean and not context_clean[-1] in ".!?":
                return True
        else:
            # Without context, be conservative - only reject very short fragments
            if len(frag) < 20:
                return True
    
    # Reject if starts with lowercase and is suspiciously short
    if _LOWERCASE_START.match(frag) and len(frag) < 30:
        # Allow some exceptions for technical terms, names, etc.
        if not any(indicator in frag.lower() for indicator in ["http", "www", "@", "#", "AI", "GPT", "API"]):
            return True
    
    # Reject conjunction starts (likely continuation)
    if _CONJUNCTION_START.match(frag) and len(frag) < 100:
        return True
    
    # Reject if too short and lacks substance
    if len(frag) < 15:
        return True
    
    # Content validation - need some non-stopwords
    words = re.findall(r'\b\w+\b', frag.lower())
    if len(words) >= 3:
        content_words = [w for w in words if w not in STOPWORDS]
        if len(content_words) == 0:  # All stopwords
            return True
    
    return False


def has_speaker_artifacts(text: str) -> bool:
    """
    Detect embedded speaker tags, timestamps, or transcription artifacts
    
    Args:
        text: Text to check for artifacts
        
    Returns:
        True if speaker artifacts detected
    """
    # Speaker tag patterns
    speaker_patterns = [
        r'\b(?:Speaker|SPEAKER)\s*[A-Z0-9]?\s*:',  # Speaker A:, Speaker 1:
        r'\b(?:Host|Guest|Interviewer|Interviewee)\s*:',  # Role-based tags
        r'\b(?:Hannah|Christian|Host|Guest)\s*:',  # Named speakers from training data
        r'→\s*\d+\s*:',  # Line number artifacts
        r'\[\d{1,2}:\d{2}(?::\d{2})?\]',  # Timestamp brackets [00:15]
        r'\d{1,2}:\d{2}(?::\d{2})?(?:\s|$)',  # Bare timestamps
        r'\[(?:inaudible|unclear|crosstalk|music|laughter)\]',  # Transcription notes
        r'\b(?:um|uh|ah|er)\b.*\b(?:um|uh|ah|er)\b',  # Multiple filler words
        r'^[A-Z]:\s',  # Single letter speaker tags
    ]
    
    return any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in speaker_patterns)


def validate_content_quality(text: str, min_content_ratio: float = 0.3) -> bool:
    """
    Validate that text has sufficient content density
    
    Args:
        text: Text to validate
        min_content_ratio: Minimum ratio of content words to total words
        
    Returns:
        True if content quality is acceptable
    """
    words = re.findall(r'\b\w+\b', text.lower())
    
    if len(words) < 3:
        return False
    
    # Count content words (non-stopwords)
    content_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    
    if len(content_words) == 0:
        return False
    
    content_ratio = len(content_words) / len(words)
    return content_ratio >= min_content_ratio


def comprehensive_fragment_check(text: str, context: str = "") -> GuardResult:
    """
    Run all fragment validation checks
    
    Args:
        text: Text fragment to validate
        context: Surrounding context if available
        
    Returns:
        GuardResult indicating validation status
    """
    if not text or not text.strip():
        return GuardResult.NO_CONTENT
    
    text = text.strip()
    
    # Check for rubric leakage first
    if has_rubric_leakage(text):
        return GuardResult.RUBRIC_LEAKAGE
    
    # Check for speaker artifacts
    if has_speaker_artifacts(text):
        return GuardResult.SPEAKER_ARTIFACT
    
    # Check for mid-sentence fragments
    if looks_like_mid_sentence(text, context):
        return GuardResult.MID_SENTENCE
    
    # Check minimum length with content
    if len(text) < 10:
        return GuardResult.TOO_SHORT
    
    # Check content quality
    if not validate_content_quality(text):
        return GuardResult.NO_CONTENT
    
    return GuardResult.VALID


def filter_valid_fragments(fragments: List[str], contexts: List[str] = None) -> List[str]:
    """
    Filter list of fragments to only valid ones
    
    Args:
        fragments: List of text fragments to validate
        contexts: Optional list of context strings for each fragment
        
    Returns:
        List of valid fragments
    """
    if contexts is None:
        contexts = [""] * len(fragments)
    
    valid_fragments = []
    rejection_stats = {}
    
    for fragment, context in zip(fragments, contexts):
        result = comprehensive_fragment_check(fragment, context)
        
        if result == GuardResult.VALID:
            valid_fragments.append(fragment)
        else:
            # Track rejection reasons for debugging
            rejection_stats[result.value] = rejection_stats.get(result.value, 0) + 1
            print(f"🚫 Rejected fragment ({result.value}): '{fragment[:60]}...'")
    
    # Log summary
    total = len(fragments)
    valid = len(valid_fragments)
    print(f"📊 Fragment validation: {valid}/{total} passed ({valid/total*100:.1f}%)")
    
    if rejection_stats:
        reasons = ", ".join([f"{reason}({count})" for reason, count in rejection_stats.items()])
        print(f"   Rejections: {reasons}")
    
    return valid_fragments


def validate_section_headers(text: str) -> List[str]:
    """
    Extract and validate section headers, rejecting rubric artifacts
    
    Args:
        text: Text containing potential section headers
        
    Returns:
        List of valid section headers found
    """
    # Find markdown-style headers
    headers = re.findall(r'^#+\s*(.+?)$', text, re.MULTILINE)
    
    valid_headers = []
    
    for header in headers:
        # Clean header
        clean_header = re.sub(r'[^\w\s]', ' ', header).upper().strip()
        
        # Check against bad headers
        if clean_header in BAD_HEADERS:
            print(f"🚫 Rejected rubric header: '{header}'")
            continue
        
        # Check for partial matches
        if any(bad in clean_header for bad in ["FRAMEWORK", "PSYCHOLOGY", "PLAYBOOK", "QUALITY"]):
            print(f"🚫 Rejected artifact header: '{header}'")
            continue
        
        # Check for the specific broken patterns we saw
        if any(pattern in header.lower() for pattern in ["'m part", "'re going", "'s a lot"]):
            print(f"🚫 Rejected fragment header: '{header}'")
            continue
        
        valid_headers.append(header)
    
    return valid_headers


def clean_text_artifacts(text: str) -> str:
    """
    Remove common transcription artifacts from text
    
    Args:
        text: Raw text possibly containing artifacts
        
    Returns:
        Cleaned text
    """
    # Remove speaker tags
    text = re.sub(r'\b(?:Speaker|SPEAKER)\s*[A-Z0-9]?\s*:\s*', '', text)
    text = re.sub(r'\b(?:Host|Guest|Interviewer)\s*:\s*', '', text)
    
    # Remove timestamps
    text = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', '', text)
    text = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?\s+', '', text)
    
    # Remove transcription notes
    text = re.sub(r'\[(?:inaudible|unclear|crosstalk|music|laughter)\]', '', text, flags=re.IGNORECASE)
    
    # Remove line number artifacts
    text = re.sub(r'→\s*\d+\s*:', '', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


class ContentGuard:
    """Main guard class for comprehensive content validation"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.validation_stats = {
            "total_checked": 0,
            "passed": 0,
            "rejected": 0,
            "rejection_reasons": {}
        }
    
    def validate_extraction(self, extraction_data: dict) -> dict:
        """
        Validate entire extraction output for quality
        
        Args:
            extraction_data: Raw extraction output
            
        Returns:
            Cleaned extraction data
        """
        self.validation_stats["total_checked"] += 1
        
        # Check for rubric leakage at top level
        if has_rubric_leakage(str(extraction_data)):
            print("⚠️ Rubric leakage detected in extraction")
        
        # Clean up any artifacts
        cleaned_data = {}
        
        for key, value in extraction_data.items():
            # Skip known bad keys
            if any(bad in key.upper() for bad in ["FRAMEWORK", "PSYCHOLOGY", "PLAYBOOK", "QUALITY"]):
                print(f"🚫 Skipping rubric artifact key: {key}")
                continue
            
            # Clean text values
            if isinstance(value, str):
                cleaned_value = clean_text_artifacts(value)
                if comprehensive_fragment_check(cleaned_value) == GuardResult.VALID:
                    cleaned_data[key] = cleaned_value
            elif isinstance(value, list):
                # Clean list items
                cleaned_list = []
                for item in value:
                    if isinstance(item, str):
                        cleaned_item = clean_text_artifacts(item)
                        if comprehensive_fragment_check(cleaned_item) == GuardResult.VALID:
                            cleaned_list.append(cleaned_item)
                    elif isinstance(item, dict):
                        cleaned_list.append(self._clean_dict_item(item))
                    else:
                        cleaned_list.append(item)
                cleaned_data[key] = cleaned_list
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
    def _clean_dict_item(self, item: dict) -> dict:
        """Clean dictionary items recursively"""
        cleaned = {}
        for k, v in item.items():
            if isinstance(v, str):
                clean_v = clean_text_artifacts(v)
                if comprehensive_fragment_check(clean_v) == GuardResult.VALID:
                    cleaned[k] = clean_v
            else:
                cleaned[k] = v
        return cleaned
    
    def get_stats(self) -> dict:
        """Get validation statistics"""
        return self.validation_stats.copy()