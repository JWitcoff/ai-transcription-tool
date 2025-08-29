"""
Enhanced Fragment Validator - Advanced validation with sentence boundaries, 
concept whitelisting, and round-trip schema compliance checks
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum


class FragmentQuality(Enum):
    VALID = "valid"
    TOO_SHORT = "too_short" 
    MID_SENTENCE = "mid_sentence"
    NO_VERB = "no_verb"
    SPEAKER_TAGS = "speaker_tags"
    UNKNOWN_CONCEPT = "unknown_concept"
    TIMESTAMP_NOISE = "timestamp_noise"


class FragmentValidation:
    """Result of fragment validation"""
    def __init__(self, quality: FragmentQuality, reason: str):
        self.quality = quality
        self.reason = reason


class EnhancedValidator:
    """Enhanced validator with fragment quality checks and round-trip validation"""
    
    def __init__(self, rubric_type: str = "prompting_claude_v1"):
        self.rubric_type = rubric_type
        self.rubric = self._load_rubric()
        
        # Initialize concept whitelists based on rubric type
        self._init_concept_whitelists()
        
        # Quality thresholds
        self.min_fragment_length = 2  # words
        self.min_quality_score = 0.7
        
    def _load_rubric(self) -> Dict:
        """Load rubric based on type"""
        if self.rubric_type == "prompting_claude_v1":
            rubric_path = Path(__file__).parent / "prompting_rubric.json"
        else:
            rubric_path = Path(__file__).parent / "coverage_rubric.json"
            
        try:
            with open(rubric_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load rubric: {e}")
            return self._default_rubric()
    
    def _default_rubric(self) -> Dict:
        """Default rubric structure"""
        return {
            "schema_version": self.rubric_type,
            "canonical_checklist": {},
            "scoring": {"thresholds": {"excellent": 0.9, "good": 0.8, "acceptable": 0.7}}
        }
    
    def _init_concept_whitelists(self):
        """Initialize concept whitelists based on rubric type"""
        if self.rubric_type == "prompting_claude_v1":
            self.concept_whitelist = {
                # Core structure concepts
                "role", "task", "persona", "assistant", "system", "user", "job", "LLM",
                "tone", "style", "factual", "confident", "professional", "concise",
                "constants", "background", "schema", "invariant", "context", "form",
                "delimiters", "XML", "tags", "markdown", "structure", "sections", "organize",
                
                # Processing concepts  
                "steps", "analyze", "parse", "process", "sequence", "order", "reasoning", "first", "then",
                "examples", "few-shot", "demonstration", "sample", "case", "edge cases", "input", "output",
                "guardrails", "confidence", "evidence", "safety", "threshold", "cite", "insufficient",
                
                # Output concepts
                "JSON", "format", "contract", "response", "prefill", "begin", "start", "tokens",
                "parameters", "temperature", "max_tokens", "determinism", "stop",
                "caching", "cache", "static", "prompt", "reuse", "invariant"
            }
        else:  # YouTube growth
            self.concept_whitelist = {
                "CCN", "fit", "core", "casual", "new", "audience", "segments",
                "timing", "seconds", "intro", "retention", "7/15/30", "confirm", "click",
                "journey", "map", "A→Z", "video", "game", "content", "path",
                "hide", "vegetables", "meaningful", "entertaining", "packaging",
                "thumbnail", "optimization", "views", "clicks", "impressions", 
                "algorithm", "growth", "viral", "subscribers", "channel", "creator", "youtuber"
            }
    
    def validate_fragments(self, extracted_items: List[Dict], item_type: str = "framework") -> List[Dict]:
        """Validate fragments and return only valid ones"""
        if not extracted_items:
            return []
            
        validated_items = []
        rejected_count = 0
        rejection_reasons = {}
        
        for item in extracted_items:
            text = self._extract_text_from_item(item, item_type)
            if not text:
                continue
                
            validation_result = self._validate_fragment_quality(text)
            
            if validation_result.quality == FragmentQuality.VALID:
                validated_items.append(item)
            else:
                rejected_count += 1
                reason = validation_result.quality.value
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                
                print(f"🚫 Rejected {item_type}: '{text[:60]}...' ({reason}: {validation_result.reason})")
        
        # Log validation summary
        total = len(extracted_items)
        print(f"✅ Fragment validation: {len(validated_items)}/{total} {item_type}s passed")
        if rejected_count > 0:
            reasons_str = ', '.join([f"{reason}({count})" for reason, count in rejection_reasons.items()])
            print(f"   Rejections: {reasons_str}")
        
        return validated_items
    
    def _extract_text_from_item(self, item: Dict, item_type: str) -> str:
        """Extract validatable text from different item types"""
        if item_type == "framework":
            return item.get("name", "") or item.get("verbatim_term", "")
        elif item_type == "metric":
            return item.get("verbatim", "") or item.get("value", "")
        elif item_type == "case_study":
            return item.get("name", "") or item.get("pattern_or_framework", "")
        elif item_type in ["step", "guardrail", "example"]:
            return str(item) if isinstance(item, str) else item.get("content", "")
        else:
            return str(item)
    
    def _validate_fragment_quality(self, text: str) -> FragmentValidation:
        """Comprehensive fragment quality validation"""
        text = text.strip()
        
        if not text:
            return FragmentValidation(FragmentQuality.TOO_SHORT, "Empty text")
        
        # 1. Length check (word-based, not character-based)
        words = text.split()
        if len(words) < self.min_fragment_length:
            return FragmentValidation(FragmentQuality.TOO_SHORT, f"Only {len(words)} words")
        
        # 2. Sentence boundary check
        if not self._has_proper_sentence_boundary(text):
            return FragmentValidation(FragmentQuality.MID_SENTENCE, "Improper sentence boundary")
        
        # 3. Verb presence (grammatical validity)
        if len(words) > 3 and not self._has_verb(text):
            return FragmentValidation(FragmentQuality.NO_VERB, "No verb found - likely fragment")
        
        # 4. Speaker tags or timestamps
        if self._has_speaker_tags_or_timestamps(text):
            return FragmentValidation(FragmentQuality.SPEAKER_TAGS, "Contains metadata noise")
        
        # 5. Concept whitelist check
        if not self._matches_concept_whitelist(text):
            return FragmentValidation(FragmentQuality.UNKNOWN_CONCEPT, f"No {self.rubric_type} concepts found")
        
        return FragmentValidation(FragmentQuality.VALID, "Fragment passed all quality checks")
    
    def _has_proper_sentence_boundary(self, text: str) -> bool:
        """Check for proper sentence boundaries"""
        # Must start with capital letter, number, or special symbol
        if not (text[0].isupper() or text[0].isdigit() or text[0] in '"\'<([{'):
            return False
        
        # Check ending - more permissive for technical content
        last_char = text[-1]
        
        # Proper sentence endings
        if last_char in '.!?:;':
            return True
        
        # Technical pattern endings (CCN fit, 7/15/30, A→Z map, etc.)
        technical_endings = [
            r'\b\w+\s*fit$',  # CCN fit
            r'\d+/\d+/\d+$',  # 7/15/30
            r'\w\s*→\s*\w$',  # A→Z
            r'\w+\s*map$',    # journey map
            r'\d+[xX]$',      # 270x
            r'\d+%$',         # percentages
            r'temperature\s*=\s*0$',  # parameters
            r'max_tokens$',   # technical terms
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in technical_endings)
    
    def _has_verb(self, text: str) -> bool:
        """Enhanced verb detection for technical content"""
        # Verb patterns including technical/instruction verbs
        verb_patterns = [
            # Standard verbs
            r'\\b(?:is|are|was|were|be|been|being)\\b',
            r'\\b(?:have|has|had|do|does|did|will|would|can|could|should|may|might)\\b',
            
            # Technical/instruction verbs
            r'\\b(?:define|set|specify|provide|include|add|create|build|analyze|extract|process|validate|check|ensure|prevent|cite|prefill|begin|start|parse|read|configure|enable|implement|apply|use)\\b',
            
            # Action indicators
            r'\\w+(?:ed|ing|es|s)\\b',  # Verb forms
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in verb_patterns)
    
    def _has_speaker_tags_or_timestamps(self, text: str) -> bool:
        """Detect embedded metadata that shouldn't be in clean extractions"""
        noise_patterns = [
            r'\\b(?:Speaker|SPEAKER|Host|Guest)\\s*[A-Z0-9]?:',  # Speaker labels
            r'\\[\\d{1,2}:\\d{2}(?::\\d{2})?.*?\\]',  # Timestamps [00:00]
            r'\\d{1,2}:\\d{2}(?::\\d{2})?',  # Bare timestamps
            r'\\b(?:Hannah|Christian|Host|Guest|Interviewer|Interviewee)\\s*:',  # Named speakers
            r'→\\s*\\d+',  # Line number artifacts
            r'\\[inaudible\\]|\\[unclear\\]|\\[crosstalk\\]',  # Transcription artifacts
            r'\\b(?:um|uh|ah|er)\\b.*\\b(?:um|uh|ah|er)\\b',  # Multiple filler words
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in noise_patterns)
    
    def _matches_concept_whitelist(self, text: str) -> bool:
        """Check if text contains domain-relevant concepts"""
        text_lower = text.lower()
        
        # Must contain at least one domain concept
        concept_matches = [concept for concept in self.concept_whitelist 
                          if concept.lower() in text_lower]
        
        # For very short fragments, require exact concept match
        if len(text.split()) <= 3:
            return len(concept_matches) > 0
        
        # For longer text, be more flexible but require relevance
        if len(concept_matches) > 0:
            return True
        
        # Check for domain-specific patterns even if not in whitelist
        if self.rubric_type == "prompting_claude_v1":
            technical_patterns = [
                r'\\b[A-Z]+\\s+(?:prompt|format|schema)\\b',  # Technical formats
                r'\\b(?:JSON|XML)\\s+\\w+',  # Data formats
                r'temperature\\s*=\\s*\\d',  # Parameters
                r'\\{[^}]*\\}',  # JSON-like structures
            ]
        else:  # YouTube
            technical_patterns = [
                r'\\d+[xX]\\s+(?:more|views|growth)',  # Multipliers
                r'\\d+/\\d+/\\d+',  # Timing patterns
                r'\\b\\w+\\s*→\\s*\\w+',  # Arrow patterns
                r'\\d+%\\s*(?:to|→)\\s*\\d+%',  # Percentage changes
            ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in technical_patterns)
    
    def round_trip_validate(self, extracted_data: Dict) -> Dict[str, Any]:
        """Round-trip validation - can we use what we extracted?"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "usability_score": 0.0,
            "schema_compliance": {},
            "template_viability": {}
        }
        
        # 1. Schema compliance check
        schema_check = self._validate_schema_compliance(extracted_data)
        validation_results["schema_compliance"] = schema_check
        
        if not schema_check["valid"]:
            validation_results["valid"] = False
            validation_results["errors"].extend(schema_check["errors"])
        
        # 2. Template reconstruction test (for prompting content)
        if self.rubric_type == "prompting_claude_v1":
            template_check = self._validate_template_reconstruction(extracted_data)
            validation_results["template_viability"] = template_check
            
            if not template_check["usable"]:
                validation_results["warnings"].extend(template_check["issues"])
        
        # 3. Calculate overall usability score
        validation_results["usability_score"] = self._calculate_usability_score(
            schema_check, validation_results.get("template_viability", {})
        )
        
        return validation_results
    
    def _validate_schema_compliance(self, data: Dict) -> Dict[str, Any]:
        """Validate against schema requirements"""
        schema_validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "completeness_score": 0.0
        }
        
        # Check schema version
        expected_version = self.rubric_type
        actual_version = data.get("schema_version")
        
        if actual_version != expected_version:
            schema_validation["errors"].append(f"Schema version mismatch: got {actual_version}, expected {expected_version}")
            schema_validation["valid"] = False
        
        # Check required fields based on rubric type
        if self.rubric_type == "prompting_claude_v1":
            required_fields = [
                "structure.role", "structure.tone", "structure.constants",
                "structure.ordered_steps", "structure.guardrails", 
                "structure.output_schema", "structure.prefill"
            ]
        else:
            required_fields = ["frameworks", "metrics", "preserved_terms"]
        
        missing_fields = []
        present_fields = 0
        
        for field in required_fields:
            if self._check_nested_field(data, field):
                present_fields += 1
            else:
                missing_fields.append(field)
        
        if missing_fields:
            schema_validation["errors"].extend([f"Missing required field: {field}" for field in missing_fields])
            schema_validation["valid"] = False
        
        schema_validation["completeness_score"] = present_fields / len(required_fields)
        
        return schema_validation
    
    def _check_nested_field(self, data: Dict, field_path: str) -> bool:
        """Check if nested field exists and has content"""
        if '.' not in field_path:
            value = data.get(field_path)
            return value is not None and value != "" and value != []
        
        parts = field_path.split('.')
        current = data
        
        try:
            for part in parts:
                current = current[part]
            return current is not None and current != "" and current != []
        except (KeyError, TypeError):
            return False
    
    def _validate_template_reconstruction(self, data: Dict) -> Dict[str, Any]:
        """Test if extracted data can be used to build a working prompt template"""
        template_validation = {
            "usable": True,
            "issues": [],
            "components_present": {},
            "json_valid": False,
            "prefill_valid": False,
            "prose_leak": False
        }
        
        # Check if we have the core components
        structure = data.get("structure", {})
        components = ["role", "tone", "constants", "ordered_steps", "guardrails", "output_schema", "prefill"]
        
        for component in components:
            present = component in structure and structure[component]
            template_validation["components_present"][component] = present
            
            if not present:
                template_validation["issues"].append(f"Missing {component} - template will be incomplete")
        
        # Test JSON schema validity
        try:
            output_schema = structure.get("output_schema", "")
            if output_schema:
                # Try to parse as JSON if it looks like JSON
                if output_schema.strip().startswith('{'):
                    json.loads(output_schema)
                template_validation["json_valid"] = True
        except json.JSONDecodeError:
            template_validation["issues"].append("Output schema is not valid JSON")
        
        # Check prefill format
        prefill = structure.get("prefill", "")
        if prefill:
            if prefill.strip().startswith('{') or 'begin' in prefill.lower():
                template_validation["prefill_valid"] = True
            else:
                template_validation["issues"].append("Prefill doesn't constrain output format properly")
        
        # Check for prose leak (template should be structured, not narrative)
        template_str = data.get("template", "")
        if template_str and len(template_str.split('.')) > 5:  # Many sentences = likely prose
            template_validation["prose_leak"] = True
            template_validation["issues"].append("Template contains too much prose - should be structured")
        
        # Overall usability
        critical_components = ["role", "output_schema", "prefill"]
        has_critical = all(template_validation["components_present"].get(comp, False) for comp in critical_components)
        
        if not has_critical:
            template_validation["usable"] = False
        
        return template_validation
    
    def _calculate_usability_score(self, schema_check: Dict, template_check: Dict) -> float:
        """Calculate overall usability score"""
        schema_score = schema_check.get("completeness_score", 0.0)
        
        if template_check:
            # Weight template components
            components = template_check.get("components_present", {})
            critical_components = ["role", "output_schema", "prefill"]
            important_components = ["tone", "constants", "guardrails", "ordered_steps"]
            
            critical_score = sum(components.get(comp, False) for comp in critical_components) / len(critical_components)
            important_score = sum(components.get(comp, False) for comp in important_components) / len(important_components)
            
            template_score = (critical_score * 0.7) + (important_score * 0.3)
            
            # Penalties
            if template_check.get("prose_leak"):
                template_score *= 0.8
            if not template_check.get("json_valid") and components.get("output_schema"):
                template_score *= 0.9
            
            return (schema_score * 0.4) + (template_score * 0.6)
        else:
            return schema_score
    
    def validate_extraction(self, extraction_output: Dict, include_fragment_validation: bool = True) -> Dict[str, Any]:
        """Complete validation of extraction output"""
        validation_report = {
            "timestamp": self._get_timestamp(),
            "rubric_type": self.rubric_type,
            "overall_valid": True,
            "quality_score": 0.0,
            "validation_stages": {}
        }
        
        # Stage 1: Fragment validation
        if include_fragment_validation:
            fragment_results = self._validate_all_fragments(extraction_output)
            validation_report["validation_stages"]["fragments"] = fragment_results
            
            if fragment_results["quality_score"] < self.min_quality_score:
                validation_report["overall_valid"] = False
        
        # Stage 2: Schema compliance
        schema_results = self._validate_schema_compliance(extraction_output)
        validation_report["validation_stages"]["schema"] = schema_results
        
        if not schema_results["valid"]:
            validation_report["overall_valid"] = False
        
        # Stage 3: Round-trip validation
        roundtrip_results = self.round_trip_validate(extraction_output)
        validation_report["validation_stages"]["round_trip"] = roundtrip_results
        
        if not roundtrip_results["valid"]:
            validation_report["overall_valid"] = False
        
        # Calculate overall quality score
        scores = []
        if "fragments" in validation_report["validation_stages"]:
            scores.append(validation_report["validation_stages"]["fragments"]["quality_score"])
        scores.append(schema_results["completeness_score"])
        scores.append(roundtrip_results["usability_score"])
        
        validation_report["quality_score"] = sum(scores) / len(scores)
        
        return validation_report
    
    def _validate_all_fragments(self, output: Dict) -> Dict[str, Any]:
        """Validate all fragments in extraction output"""
        validation_results = {
            "total_items": 0,
            "valid_items": 0, 
            "rejected_items": 0,
            "rejection_reasons": {},
            "quality_score": 0.0
        }
        
        # Check different item types
        item_types = [
            ("frameworks", "framework"),
            ("metrics", "metric"), 
            ("case_studies", "case_study")
        ]
        
        # For prompting schema, also check structure components
        if self.rubric_type == "prompting_claude_v1":
            structure = output.get("structure", {})
            for component in ["ordered_steps", "examples_fewshot", "guardrails"]:
                items = structure.get(component, [])
                if isinstance(items, list):
                    item_types.append((f"structure.{component}", component))
        
        for field_name, item_type in item_types:
            if '.' in field_name:
                # Nested field
                items = output.get("structure", {}).get(field_name.split('.')[1], [])
            else:
                items = output.get(field_name, [])
            
            if not isinstance(items, list):
                continue
                
            for item in items:
                validation_results["total_items"] += 1
                
                text = self._extract_text_from_item(item, item_type)
                if text:
                    quality_check = self._validate_fragment_quality(text)
                    
                    if quality_check.quality == FragmentQuality.VALID:
                        validation_results["valid_items"] += 1
                    else:
                        validation_results["rejected_items"] += 1
                        reason = quality_check.quality.value
                        validation_results["rejection_reasons"][reason] = \
                            validation_results["rejection_reasons"].get(reason, 0) + 1
        
        # Calculate quality score
        if validation_results["total_items"] > 0:
            validation_results["quality_score"] = validation_results["valid_items"] / validation_results["total_items"]
        
        return validation_results
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()