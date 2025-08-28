"""
Deep Extractor - Multi-lens analysis engine for extracting frameworks, 
metrics, psychology, and systems from transcripts with terminology preservation
"""

import re
import os
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeepExtractor:
    """Unified extractor handling all analysis lenses internally"""
    
    def __init__(self):
        self.schema_version = "yt_playbook_v1"
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        # Terminology preservation rules
        self.terminology_rules = {
            "preserve_quoted": True,  # "CCN fit", "Hide the Vegetables" 
            "preserve_proper_nouns": True,  # A→Z map, 7/15/30
            "preserve_formulas": True  # X→Y→Z structures
        }
        
        # Initialize OpenAI if available
        if self.api_key and self.api_key != 'your_openai_api_key_here':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️ OpenAI package not installed. Using fallback extraction.")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
        
        # Few-shot exemplar for consistent extraction
        self.few_shot_example = """
Example Input: "The CCN fit framework means your content works for Core, Casual, and New audiences simultaneously. This increased our views by 270x when we applied it to thumbnails."

Example Output: {
  "frameworks": [{
    "name": "CCN fit",
    "definition": "content works for Core, Casual, and New audiences simultaneously",
    "components": ["Core audience", "Casual audience", "New audience"],
    "verbatim_term": "CCN fit",
    "context": "thumbnail optimization"
  }],
  "metrics": [{
    "value": "270x",
    "type": "multiplier",
    "metric": "views increase",
    "context": "applied CCN fit to thumbnails",
    "verbatim": "increased our views by 270x"
  }],
  "preserved_terms": ["CCN fit", "270x"]
}
"""
    
    def extract_all_lenses(self, transcript: str, user_prompt: str = "", video_title: str = "") -> Dict[str, Any]:
        """
        Extract insights using all analysis lenses
        
        Returns:
            Dictionary with structured extraction data
        """
        if not transcript:
            return self._empty_result("Empty transcript provided")
        
        # Multi-pass extraction
        try:
            # Pass 1: Raw extraction with all lenses
            raw_extraction = self._extract_with_all_lenses(transcript, user_prompt, video_title)
            
            # Pass 2: Organize and structure
            structured_data = self._organize_extraction(raw_extraction, transcript)
            
            # Pass 3: Validate and add quality check
            final_result = self._add_quality_check(structured_data, transcript)
            
            return final_result
            
        except Exception as e:
            return self._empty_result(f"Extraction failed: {e}")
    
    def _extract_with_all_lenses(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Pass 1: Raw extraction using all lenses"""
        
        if self.client:
            return self._extract_with_openai(transcript, user_prompt, video_title)
        else:
            return self._extract_with_fallback(transcript, user_prompt)
    
    def _extract_with_openai(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Use OpenAI for comprehensive multi-lens extraction"""
        
        system_prompt = f"""You are an expert at extracting actionable insights from content transcripts. 
Extract frameworks, metrics, psychological principles, time-based strategies, and systems using these specific lenses:

EXTRACTION LENSES:
1. FRAMEWORKS: Named models, structures, formulas (e.g., "CCN fit", "A→Z map", "7/15/30", "problem→solution loops", "Laws of X")
2. METRICS: Numbers with context (multipliers like "270x", percentages like "5%→30%", counts, timeframes, before/after)
3. TEMPORAL: Time-based strategies (0-7s, 7-15s, 15-30s tactics, mid-video hooks, reveal timing)
4. PSYCHOLOGY: Persuasion principles (scarcity, consistency, reciprocity, consensus, similarity, authority), audience dynamics
5. SYSTEMS: Repeatable processes, templates, workflows, funnel strategies (shorts→long→community)
6. AUTHENTICITY: Brand signals, vulnerability, personal elements, "resume principle"

TERMINOLOGY RULES:
- Preserve EXACT terms in quotes: "CCN fit", "Hide the Vegetables"
- Preserve formulas and arrows: A→Z, X→Y→Z, 7/15/30
- Keep proper nouns and branded concepts verbatim
- Track all preserved terms in output

{self.few_shot_example}

Video context: {video_title}
User's focus: {user_prompt}

Return a structured JSON with frameworks, metrics, temporal_strategies, psychology, systems, authenticity, and preserved_terms arrays."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use latest model for best extraction
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract insights from this transcript:\n\n{transcript[:12000]}"}  # Increased limit
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text parsing if needed
            try:
                import json
                return json.loads(content)
            except json.JSONDecodeError:
                return self._parse_text_response(content, transcript)
                
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            return self._extract_with_fallback(transcript, user_prompt)
    
    def _extract_with_fallback(self, transcript: str, user_prompt: str) -> Dict[str, Any]:
        """Fallback extraction using pattern matching and heuristics"""
        
        result = {
            "frameworks": self._extract_frameworks_heuristic(transcript),
            "metrics": self._extract_metrics_heuristic(transcript),
            "temporal_strategies": self._extract_temporal_heuristic(transcript),
            "psychology": self._extract_psychology_heuristic(transcript),
            "systems": self._extract_systems_heuristic(transcript),
            "authenticity": self._extract_authenticity_heuristic(transcript),
            "preserved_terms": self._extract_verbatim_terms(transcript)
        }
        
        return result
    
    def _extract_frameworks_heuristic(self, text: str) -> List[Dict[str, Any]]:
        """Extract frameworks using pattern matching"""
        frameworks = []
        
        # Pattern matching for common framework types
        patterns = [
            r'"([^"]+fit)"',  # "CCN fit", "Product-market fit"
            r'(\w+)→(\w+)→(\w+)',  # A→B→C structures
            r'(\d+)/(\d+)/(\d+)',  # 7/15/30 style
            r'Law[s]? of ([^.]+)',  # Laws of X
            r'([A-Z][^.]+) framework',  # Named frameworks
            r'([A-Z][^.]+) principle',  # Named principles
            r'([A-Z][^.]+) model',  # Named models
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                framework = {
                    "name": match.group(0),
                    "verbatim_term": match.group(0),
                    "context": self._get_surrounding_context(text, match.start(), match.end()),
                    "extraction_method": "heuristic"
                }
                frameworks.append(framework)
        
        return frameworks
    
    def _extract_metrics_heuristic(self, text: str) -> List[Dict[str, Any]]:
        """Extract metrics and numbers using pattern matching"""
        metrics = []
        
        # Pattern matching for metrics
        patterns = [
            r'(\d+)x\b',  # Multipliers: 270x, 40x
            r'(\d+)%\s*(?:to|→)\s*(\d+)%',  # Percentage changes: 5% to 30%
            r'(\d+)\s*(?:hours?|days?|weeks?|months?)\s*to\s*(\d+[MKmk]?)\s*(?:subs?|subscribers?|views?)',  # Time to outcome
            r'\b(\d+)\s*(?:million|thousand|M|K|k)\b',  # Large numbers
            r'increased?\s+(?:by\s+)?(\d+(?:\.\d+)?[x%]?)',  # Increases
            r'from\s+(\d+[%MKmk]?)\s+to\s+(\d+[%MKmk]?)',  # From X to Y
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                metric = {
                    "value": match.group(1) if match.groups() else match.group(0),
                    "verbatim": match.group(0),
                    "context": self._get_surrounding_context(text, match.start(), match.end()),
                    "extraction_method": "heuristic"
                }
                if len(match.groups()) > 1:
                    metric["change_from"] = match.group(1)
                    metric["change_to"] = match.group(2)
                
                metrics.append(metric)
        
        return metrics
    
    def _extract_temporal_heuristic(self, text: str) -> Dict[str, Any]:
        """Extract time-based strategies"""
        temporal = {
            "intro_strategies": [],
            "retention_hooks": [],
            "timing_principles": []
        }
        
        # Look for time-specific advice
        time_patterns = [
            r'(?:first\s+)?(\d+)\s*(?:seconds?|secs?)',
            r'(\d+)[-–](\d+)\s*(?:seconds?|secs?)',
            r'(?:after\s+)?(\d+)\s*minutes?',
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = self._get_surrounding_context(text, match.start(), match.end())
                temporal["timing_principles"].append({
                    "timeframe": match.group(0),
                    "strategy": context,
                    "extraction_method": "heuristic"
                })
        
        return temporal
    
    def _extract_psychology_heuristic(self, text: str) -> Dict[str, Any]:
        """Extract psychological principles"""
        psychology = {
            "influence_principles": [],
            "audience_dynamics": [],
            "persuasion_tactics": []
        }
        
        # Cialdini's principles and related concepts
        influence_keywords = [
            "scarcity", "limited", "exclusive", "rare",
            "consistency", "commitment", "promise",
            "reciprocity", "give", "return", "exchange",
            "consensus", "social proof", "others", "popular",
            "similarity", "like us", "relatable",
            "authority", "expert", "credentials", "trust"
        ]
        
        for keyword in influence_keywords:
            pattern = fr'\b{keyword}\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                psychology["influence_principles"].append({
                    "principle": keyword,
                    "context": self._get_surrounding_context(text, match.start(), match.end()),
                    "extraction_method": "heuristic"
                })
        
        return psychology
    
    def _extract_systems_heuristic(self, text: str) -> Dict[str, Any]:
        """Extract systematic approaches and processes"""
        systems = {
            "content_systems": [],
            "workflow_patterns": [],
            "funnel_strategies": []
        }
        
        # Look for systematic language
        system_patterns = [
            r'(?:always|every\s+time|consistently)\s+([^.]+)',
            r'template\s+(?:for|of)\s+([^.]+)',
            r'system\s+(?:for|of)\s+([^.]+)',
            r'process\s+(?:for|of)\s+([^.]+)'
        ]
        
        for pattern in system_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                systems["content_systems"].append({
                    "system": match.group(1) if match.groups() else match.group(0),
                    "context": self._get_surrounding_context(text, match.start(), match.end()),
                    "extraction_method": "heuristic"
                })
        
        return systems
    
    def _extract_authenticity_heuristic(self, text: str) -> Dict[str, Any]:
        """Extract authenticity and personal brand signals"""
        authenticity = {
            "vulnerability_signals": [],
            "personal_elements": [],
            "brand_principles": []
        }
        
        # Look for personal/vulnerable language
        vulnerability_patterns = [
            r'I\s+(?:failed|struggled|learned|realized)',
            r'(?:my|our)\s+(?:mistake|error|failure)',
            r'(?:honest|real|authentic|genuine)',
        ]
        
        for pattern in vulnerability_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                authenticity["vulnerability_signals"].append({
                    "signal": match.group(0),
                    "context": self._get_surrounding_context(text, match.start(), match.end()),
                    "extraction_method": "heuristic"
                })
        
        return authenticity
    
    def _extract_verbatim_terms(self, text: str) -> List[str]:
        """Extract terms that should be preserved verbatim"""
        preserved_terms = set()
        
        # Extract quoted terms
        if self.terminology_rules["preserve_quoted"]:
            quoted_pattern = r'"([^"]+)"'
            quotes = re.findall(quoted_pattern, text)
            preserved_terms.update(quotes)
        
        # Extract arrow formulas
        if self.terminology_rules["preserve_formulas"]:
            arrow_pattern = r'\b[A-Z]\s*(?:→|->)\s*[A-Z](?:\s*(?:→|->)\s*[A-Z])*'
            arrows = re.findall(arrow_pattern, text)
            preserved_terms.update(arrows)
        
        # Extract time formats like 7/15/30
        time_format_pattern = r'\b\d+/\d+/\d+\b'
        time_formats = re.findall(time_format_pattern, text)
        preserved_terms.update(time_formats)
        
        return list(preserved_terms)
    
    def _get_surrounding_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for extracted terms"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _organize_extraction(self, raw_extraction: Dict, transcript: str) -> Dict[str, Any]:
        """Pass 2: Organize and structure the raw extraction"""
        
        organized = {
            "schema_version": self.schema_version,
            "extraction_metadata": {
                "extraction_method": "openai" if self.client else "heuristic",
                "transcript_length": len(transcript),
                "extraction_timestamp": self._get_timestamp()
            },
            **raw_extraction
        }
        
        return organized
    
    def _add_quality_check(self, structured_data: Dict, transcript: str) -> Dict[str, Any]:
        """Pass 3: Add quality check and validation"""
        
        # Calculate coverage metrics
        framework_count = len(structured_data.get("frameworks", []))
        metrics_count = len(structured_data.get("metrics", []))
        preserved_terms_count = len(structured_data.get("preserved_terms", []))
        
        # Estimate coverage (basic heuristic)
        coverage_items = []
        if framework_count > 0:
            coverage_items.append("frameworks")
        if metrics_count > 0:
            coverage_items.append("metrics")
        if "temporal_strategies" in structured_data and structured_data["temporal_strategies"]:
            coverage_items.append("temporal")
        if "psychology" in structured_data and structured_data["psychology"]:
            coverage_items.append("psychology")
        
        coverage_score = len(coverage_items) / 6  # 6 main categories
        
        # Identify gaps
        gaps = []
        if framework_count == 0:
            gaps.append("No frameworks detected")
        if metrics_count == 0:
            gaps.append("No metrics found")
        if preserved_terms_count == 0:
            gaps.append("No verbatim terms preserved")
        
        # Add quality check
        structured_data["quality_check"] = {
            "coverage_score": round(coverage_score, 2),
            "coverage_items": coverage_items,
            "gaps": gaps[:3],  # Top 3 gaps
            "extraction_stats": {
                "frameworks": framework_count,
                "metrics": metrics_count,
                "preserved_terms": preserved_terms_count
            },
            "next_steps": self._suggest_next_steps(structured_data)
        }
        
        return structured_data
    
    def _suggest_next_steps(self, data: Dict) -> List[str]:
        """Suggest actionable next steps based on extraction"""
        suggestions = []
        
        if data.get("frameworks"):
            # Get first framework for specific suggestion
            first_framework = data["frameworks"][0]
            if isinstance(first_framework, dict):
                name = first_framework.get("name", "framework")
                suggestions.append(f"Test the {name} in your next piece of content")
        
        if data.get("metrics"):
            suggestions.append("Measure your current baseline before applying these tactics")
        
        if not suggestions:
            suggestions.append("Review the extracted insights and identify which applies to your situation")
        
        return suggestions[:3]  # Max 3 suggestions
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result structure for error cases"""
        return {
            "schema_version": self.schema_version,
            "error": error_msg,
            "frameworks": [],
            "metrics": [],
            "temporal_strategies": {},
            "psychology": {},
            "systems": {},
            "authenticity": {},
            "preserved_terms": [],
            "quality_check": {
                "coverage_score": 0.0,
                "coverage_items": [],
                "gaps": ["Extraction failed"],
                "next_steps": ["Please try again with a valid transcript"]
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _parse_text_response(self, content: str, transcript: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        # Fallback to heuristic extraction if GPT response isn't valid JSON
        return self._extract_with_fallback(transcript, "")