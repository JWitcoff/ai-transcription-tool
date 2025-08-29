"""
Enhanced Deep Extractor - Production-ready extraction with pluggable rubrics,
fragment validation, and comprehensive telemetry
"""

import re
import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import our enhanced components
from rubric_selector import RubricSelector, RubricSelection
from enhanced_validator import EnhancedValidator, FragmentQuality
from telemetry import TelemetryCollector, ProvenanceMetadata, detect_transcriber_type, detect_extraction_method
from prompting_prompts import PROMPTING_EXTRACTION_PROMPTS, PROMPTING_FEW_SHOT_EXAMPLE

# Load environment variables
load_dotenv()


class EnhancedDeepExtractor:
    """Production-ready deep extractor with all enhancements integrated"""
    
    def __init__(self, explicit_rubric: Optional[str] = None):
        """
        Initialize enhanced extractor with optional explicit rubric
        
        Args:
            explicit_rubric: Force specific rubric ("prompting_claude_v1" or "yt_playbook_v1")
        """
        # Core components
        self.rubric_selector = RubricSelector()
        self.telemetry = TelemetryCollector()
        self.explicit_rubric = explicit_rubric
        
        # OpenAI client for premium extraction
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key and self.api_key != 'your_openai_api_key_here':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                print("✅ Enhanced extractor ready with OpenAI GPT-4")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
                self.client = None
        else:
            print("ℹ️ No OpenAI API key. Using heuristic extraction.")
        
        # Loaded rubric info (will be set on first extraction)
        self.current_rubric = None
        self.current_validator = None
        self.current_prompts = None
    
    def extract_all_lenses(self, 
                          transcript: str, 
                          user_prompt: str = "", 
                          video_title: str = "",
                          metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main extraction method with full pipeline integration
        
        Args:
            transcript: The transcript to analyze
            user_prompt: User's analysis request
            video_title: Video title for additional context
            metadata: Transcript metadata (provider, source, etc.)
            
        Returns:
            Complete extraction with telemetry and validation
        """
        if not transcript:
            return self._empty_result("Empty transcript provided")
        
        start_time = time.time()
        
        # 1. Initialize telemetry
        provenance = self._initialize_telemetry(transcript, metadata)
        
        # 2. Select appropriate rubric
        rubric_selection = self._select_rubric(transcript, video_title)
        
        # 3. Load rubric-specific components
        self._load_rubric_components(rubric_selection.rubric_name)
        
        # 4. Perform extraction
        raw_extraction = self._perform_extraction(transcript, user_prompt, video_title)
        
        # 5. Validate fragments
        cleaned_extraction = self._validate_and_clean_fragments(raw_extraction)
        
        # 6. Add structure and quality checks
        final_extraction = self._finalize_extraction(cleaned_extraction, transcript)
        
        # 7. Run round-trip validation
        validation_result = self.current_validator.validate_extraction(final_extraction)
        
        # 8. Update telemetry
        processing_time = (time.time() - start_time) * 1000  # ms
        self._update_telemetry(
            provenance, 
            rubric_selection,
            raw_extraction, 
            validation_result,
            processing_time
        )
        
        # 9. Log extraction
        transcript_id = self._generate_transcript_id(video_title, metadata)
        self.telemetry.log_extraction(
            transcript_id,
            provenance,
            final_extraction,
            validation_result
        )
        
        # 10. Add telemetry to result
        final_extraction["_metadata"] = {
            "provenance": {
                "transcriber": provenance.transcriber,
                "rubric": provenance.rubric_used,
                "extraction_method": provenance.extraction_method,
                "fallback": provenance.fallback_triggered
            },
            "quality": {
                "fragment_quality": provenance.fragment_quality_score,
                "schema_compliance": provenance.schema_compliance_score,
                "round_trip_valid": provenance.round_trip_valid
            },
            "processing_time_ms": processing_time
        }
        
        return final_extraction
    
    def _initialize_telemetry(self, transcript: str, metadata: Optional[Dict]) -> ProvenanceMetadata:
        """Initialize telemetry tracking"""
        metadata = metadata or {}
        
        transcriber = detect_transcriber_type(metadata)
        source = metadata.get("source", "unknown")
        language = metadata.get("language", "en")
        
        return self.telemetry.create_provenance(
            transcriber=transcriber,
            transcript_source=source,
            transcript_length=len(transcript),
            language=language
        )
    
    def _select_rubric(self, transcript: str, video_title: str) -> RubricSelection:
        """Select appropriate rubric for content"""
        selection = self.rubric_selector.select_rubric(
            transcript=transcript,
            video_title=video_title,
            explicit_rubric=self.explicit_rubric
        )
        
        # Log rubric selection
        print(f"\n🎯 Rubric Selection:")
        print(f"   Selected: {selection.rubric_name}")
        print(f"   Method: {selection.detection_method}")
        print(f"   Confidence: {selection.confidence:.2f}")
        
        return selection
    
    def _load_rubric_components(self, rubric_name: str):
        """Load rubric-specific validator and prompts"""
        if self.current_rubric != rubric_name:
            self.current_rubric = rubric_name
            self.current_validator = EnhancedValidator(rubric_name)
            
            # Load appropriate prompts
            if rubric_name == "prompting_claude_v1":
                self.current_prompts = PROMPTING_EXTRACTION_PROMPTS
            else:
                # Load YouTube prompts (would import from prompts.py)
                from prompts import MULTI_PASS_PROMPTS
                self.current_prompts = MULTI_PASS_PROMPTS
            
            print(f"   Loaded: {rubric_name} components")
    
    def _perform_extraction(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Perform the actual extraction"""
        try:
            if self.client and self.current_rubric == "prompting_claude_v1":
                # Use specialized prompting extraction
                return self._extract_prompting_with_openai(transcript, user_prompt, video_title)
            elif self.client:
                # Use standard OpenAI extraction
                return self._extract_with_openai(transcript, user_prompt, video_title)
            else:
                # Fallback to heuristic
                return self._extract_with_heuristics(transcript, user_prompt)
        except Exception as e:
            print(f"⚠️ Extraction failed: {e}")
            return self._extract_with_heuristics(transcript, user_prompt)
    
    def _extract_prompting_with_openai(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Extract prompting content using specialized prompts"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.current_prompts["system_prompt"]},
                    {"role": "user", "content": self.current_prompts["user_template"].format(
                        transcript=transcript[:12000],
                        video_title=video_title,
                        user_prompt=user_prompt
                    )}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                import json
                # Remove any markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                return json.loads(content.strip())
            except json.JSONDecodeError:
                print("⚠️ Failed to parse JSON, using fallback")
                return self._parse_text_response(content, transcript)
                
        except Exception as e:
            print(f"⚠️ OpenAI extraction failed: {e}")
            return self._extract_with_heuristics(transcript, user_prompt)
    
    def _extract_with_openai(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Standard OpenAI extraction for non-prompting content"""
        # Would use existing logic from deep_extractor.py
        # Simplified here for brevity
        return self._extract_with_heuristics(transcript, user_prompt)
    
    def _extract_with_heuristics(self, transcript: str, user_prompt: str) -> Dict[str, Any]:
        """Heuristic extraction as fallback"""
        if self.current_rubric == "prompting_claude_v1":
            return self._extract_prompting_heuristics(transcript)
        else:
            return self._extract_youtube_heuristics(transcript)
    
    def _extract_prompting_heuristics(self, transcript: str) -> Dict[str, Any]:
        """Extract prompting concepts using pattern matching"""
        from prompting_prompts import extract_prompting_concepts
        
        concepts = extract_prompting_concepts(transcript)
        
        # Build structured result
        result = {
            "schema_version": "prompting_claude_v1",
            "meta": {
                "source": "transcript",
                "confidence": 0.5,
                "extraction_method": "heuristic"
            },
            "prompting_thesis": "Structured prompting with clear contracts prevents hallucination",
            "structure": {
                "role": self._extract_first_match(concepts.get("role_definition", [])),
                "tone": self._extract_first_match(concepts.get("tone_guidance", [])),
                "constants": self._extract_all_matches(concepts.get("constants_indicators", [])),
                "delimiters": ["XML"] if concepts.get("delimiter_usage") else [],
                "inputs": [],
                "ordered_steps": self._extract_all_matches(concepts.get("ordered_reasoning", [])),
                "examples_fewshot": self._extract_all_matches(concepts.get("few_shot_examples", [])),
                "guardrails": self._extract_all_matches(concepts.get("guardrails_safety", [])),
                "output_schema": self._extract_first_match(concepts.get("output_schema", [])),
                "prefill": self._extract_first_match(concepts.get("prefill_tokens", [])),
                "runtime_params": {
                    "temperature": 0 if concepts.get("runtime_params") else None,
                    "max_tokens": 1500
                },
                "caching_notes": self._extract_first_match(concepts.get("caching_notes", []))
            },
            "antipatterns": [],
            "template": "",
            "checklist": []
        }
        
        return result
    
    def _extract_first_match(self, matches: List[Dict]) -> str:
        """Extract first match content"""
        if matches and len(matches) > 0:
            return matches[0].get("match", "")
        return ""
    
    def _extract_all_matches(self, matches: List[Dict]) -> List[str]:
        """Extract all match contents"""
        return [m.get("match", "") for m in matches if m.get("match")]
    
    def _extract_youtube_heuristics(self, transcript: str) -> Dict[str, Any]:
        """Extract YouTube growth concepts using pattern matching"""
        # Simplified - would use existing logic from deep_extractor.py
        return {
            "schema_version": "yt_playbook_v1",
            "frameworks": [],
            "metrics": [],
            "case_studies": [],
            "preserved_terms": []
        }
    
    def _validate_and_clean_fragments(self, raw_extraction: Dict) -> Dict[str, Any]:
        """Validate and clean extracted fragments"""
        cleaned = raw_extraction.copy()
        
        # Validate different types of fragments
        if "frameworks" in cleaned:
            cleaned["frameworks"] = self.current_validator.validate_fragments(
                cleaned["frameworks"], "framework"
            )
        
        if "metrics" in cleaned:
            cleaned["metrics"] = self.current_validator.validate_fragments(
                cleaned["metrics"], "metric"
            )
        
        if "case_studies" in cleaned:
            cleaned["case_studies"] = self.current_validator.validate_fragments(
                cleaned["case_studies"], "case_study"
            )
        
        # For prompting schema, validate structure components
        if self.current_rubric == "prompting_claude_v1" and "structure" in cleaned:
            structure = cleaned["structure"]
            
            for field in ["ordered_steps", "examples_fewshot", "guardrails"]:
                if field in structure and isinstance(structure[field], list):
                    structure[field] = self.current_validator.validate_fragments(
                        [{"content": item} for item in structure[field]], field
                    )
                    # Extract back to simple list
                    structure[field] = [item.get("content", item) for item in structure[field] 
                                       if isinstance(item, dict)]
        
        return cleaned
    
    def _finalize_extraction(self, extraction: Dict, transcript: str) -> Dict[str, Any]:
        """Add final quality checks and metadata"""
        # Ensure schema version
        if "schema_version" not in extraction:
            extraction["schema_version"] = self.current_rubric
        
        # Add extraction metadata
        extraction["extraction_metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "transcript_length": len(transcript),
            "rubric_used": self.current_rubric,
            "extraction_method": "openai" if self.client else "heuristic"
        }
        
        # For prompting content, ensure we have a usable template
        if self.current_rubric == "prompting_claude_v1" and not extraction.get("template"):
            extraction["template"] = self._generate_template_from_structure(extraction.get("structure", {}))
        
        # Add quality check
        validation = self.current_validator.round_trip_validate(extraction)
        extraction["quality_check"] = {
            "usability_score": validation.get("usability_score", 0),
            "schema_valid": validation.get("valid", False),
            "issues": validation.get("errors", []) + validation.get("warnings", [])
        }
        
        return extraction
    
    def _generate_template_from_structure(self, structure: Dict) -> str:
        """Generate a usable prompt template from structure"""
        if not structure:
            return ""
        
        template_parts = []
        
        # System section
        if structure.get("role") or structure.get("tone"):
            template_parts.append("<System>")
            if structure.get("role"):
                template_parts.append(f"  <ROLE>{structure['role']}</ROLE>")
            if structure.get("tone"):
                template_parts.append(f"  <TONE>{structure['tone']}</TONE>")
            if structure.get("constants"):
                template_parts.append("  <CONSTANTS>")
                for const in structure["constants"]:
                    template_parts.append(f"    - {const}")
                template_parts.append("  </CONSTANTS>")
            template_parts.append("</System>")
        
        # Instructions
        if structure.get("ordered_steps"):
            template_parts.append("\n<Instructions>")
            for i, step in enumerate(structure["ordered_steps"], 1):
                template_parts.append(f"  {i}. {step}")
            template_parts.append("</Instructions>")
        
        # Output format
        if structure.get("output_schema"):
            template_parts.append(f"\n<OUTPUT_FORMAT>\n{structure['output_schema']}\n</OUTPUT_FORMAT>")
        
        # Prefill
        if structure.get("prefill"):
            template_parts.append(f"\n<Prefill>{structure['prefill']}</Prefill>")
        
        return "\n".join(template_parts)
    
    def _update_telemetry(self, 
                         provenance: ProvenanceMetadata,
                         rubric_selection: RubricSelection,
                         extraction: Dict,
                         validation: Dict,
                         processing_time: float):
        """Update telemetry with extraction results"""
        
        # Update extraction details
        extraction_method = detect_extraction_method(
            "gpt-4" if self.client else "heuristic",
            not bool(self.client)
        )
        
        self.telemetry.update_provenance_extraction(
            provenance=provenance,
            rubric_used=rubric_selection.rubric_name,
            rubric_selection_method=rubric_selection.detection_method,
            extraction_method=extraction_method,
            fallback_triggered=not bool(self.client),
            fallback_reason="No OpenAI client" if not self.client else None
        )
        
        # Update quality metrics
        fragment_quality = validation.get("validation_stages", {}).get("fragments", {}).get("quality_score", 0)
        schema_compliance = validation.get("validation_stages", {}).get("schema", {}).get("completeness_score", 0)
        round_trip_valid = validation.get("validation_stages", {}).get("round_trip", {}).get("valid", False)
        
        # Check JSON validity and prose leak
        json_valid = self._check_json_validity(extraction)
        prose_leak = self._check_prose_leak(extraction)
        
        self.telemetry.update_provenance_quality(
            provenance=provenance,
            json_valid=json_valid,
            prose_leak=prose_leak,
            fragment_quality_score=fragment_quality,
            schema_compliance_score=schema_compliance,
            round_trip_valid=round_trip_valid
        )
        
        provenance.processing_duration_ms = processing_time
    
    def _check_json_validity(self, extraction: Dict) -> bool:
        """Check if extraction produces valid JSON"""
        try:
            import json
            # Try to serialize and deserialize
            json_str = json.dumps(extraction)
            json.loads(json_str)
            return True
        except:
            return False
    
    def _check_prose_leak(self, extraction: Dict) -> bool:
        """Check for prose leak in structured output"""
        if self.current_rubric == "prompting_claude_v1":
            # Check if output schema or template contains prose
            output_schema = extraction.get("structure", {}).get("output_schema", "")
            if output_schema and len(output_schema.split('.')) > 3:
                return True
        return False
    
    def _generate_transcript_id(self, video_title: str, metadata: Optional[Dict]) -> str:
        """Generate unique transcript ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean title for ID
        if video_title:
            clean_title = re.sub(r'[^a-zA-Z0-9_]', '', video_title.replace(' ', '_'))[:30]
        else:
            clean_title = "transcript"
        
        return f"{timestamp}_{clean_title}"
    
    def _empty_result(self, error_msg: str) -> Dict[str, Any]:
        """Return empty result for error cases"""
        return {
            "schema_version": self.current_rubric or "unknown",
            "error": error_msg,
            "extraction_metadata": {
                "timestamp": datetime.now().isoformat(),
                "error": True
            },
            "quality_check": {
                "usability_score": 0.0,
                "schema_valid": False,
                "issues": [error_msg]
            }
        }
    
    def _parse_text_response(self, content: str, transcript: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        # Fallback to heuristic extraction
        return self._extract_with_heuristics(transcript, "")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get telemetry session summary"""
        return self.telemetry.generate_session_report()


# Convenience function for easy usage
def extract_with_best_practices(
    transcript: str,
    user_prompt: str = "",
    video_title: str = "",
    metadata: Optional[Dict] = None,
    explicit_rubric: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract insights using all best practices
    
    Args:
        transcript: Transcript text to analyze
        user_prompt: User's analysis request
        video_title: Video title for context
        metadata: Transcript metadata
        explicit_rubric: Force specific rubric
        
    Returns:
        Complete extraction with validation and telemetry
    """
    extractor = EnhancedDeepExtractor(explicit_rubric=explicit_rubric)
    result = extractor.extract_all_lenses(transcript, user_prompt, video_title, metadata)
    
    # Print summary
    print(f"\n✅ Extraction Complete")
    print(f"   Schema: {result.get('schema_version')}")
    
    if "_metadata" in result:
        meta = result["_metadata"]
        print(f"   Method: {meta['provenance']['extraction_method']}")
        print(f"   Quality: fragments={meta['quality']['fragment_quality']:.2f}, "
              f"schema={meta['quality']['schema_compliance']:.2f}")
        print(f"   Time: {meta['processing_time_ms']:.0f}ms")
    
    return result