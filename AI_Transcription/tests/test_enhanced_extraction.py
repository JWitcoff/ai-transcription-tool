"""
Comprehensive test suite for enhanced AI_Transcription system
Tests rubric selection, fragment validation, and round-trip validation
"""

import unittest
import json
from pathlib import Path
import sys

# Add extractors to path
sys.path.append(str(Path(__file__).parent.parent / "extractors"))

from rubric_selector import RubricSelector, ContentType
from enhanced_validator import EnhancedValidator, FragmentQuality
from prompting_prompts import extract_prompting_concepts, validate_prompting_extraction
from telemetry import TelemetryCollector, ProvenanceMetadata


class TestRubricSelection(unittest.TestCase):
    """Test rubric selection and content type detection"""
    
    def setUp(self):
        self.selector = RubricSelector()
    
    def test_prompting_content_detection(self):
        """Test detection of prompting content"""
        prompting_text = """
        Set the role upfront: define what you are, your task, and domain. 
        Put constants in the system prompt for caching. Use XML tags to 
        structure sections. Specify ordered reasoning: analyze the form 
        first, then the sketch. Add guardrails: answer only if confident, 
        cite evidence. Define output schema with prefill tokens. Set 
        temperature=0 for determinism.
        """
        
        selection = self.selector.select_rubric(prompting_text, "Prompting 101 with Claude")
        
        self.assertEqual(selection.rubric_name, "prompting_claude_v1")
        self.assertGreater(selection.confidence, 0.6)
        self.assertIn("heuristic", selection.detection_method)
        self.assertIn("system_prompt", ' '.join(selection.signals_found))
    
    def test_youtube_content_detection(self):
        """Test detection of YouTube growth content"""
        youtube_text = """
        The CCN fit framework means content works for Core, Casual, and New 
        audiences. First 7 seconds confirm the click, then 15-30 seconds 
        for retention. A→Z map shows the journey. Hide the vegetables by 
        packaging meaningful content. This increased views by 270x when 
        applied to thumbnails.
        """
        
        selection = self.selector.select_rubric(youtube_text, "YouTube Growth Secrets")
        
        self.assertEqual(selection.rubric_name, "yt_playbook_v1") 
        self.assertGreater(selection.confidence, 0.5)
        self.assertIn("ccn_fit", ' '.join(selection.signals_found))
    
    def test_explicit_rubric_override(self):
        """Test explicit rubric selection via flag"""
        generic_text = "This is generic content without specific signals."
        
        selection = self.selector.select_rubric(
            generic_text, 
            explicit_rubric="prompting_claude_v1"
        )
        
        self.assertEqual(selection.rubric_name, "prompting_claude_v1")
        self.assertEqual(selection.confidence, 1.0)
        self.assertEqual(selection.detection_method, "flag")
    
    def test_fallback_behavior(self):
        """Test fallback when no clear signals"""
        generic_text = "This is completely generic text with no domain signals."
        
        selection = self.selector.select_rubric(generic_text)
        
        self.assertEqual(selection.rubric_name, "prompting_claude_v1")  # Default fallback
        self.assertEqual(selection.detection_method, "fallback")


class TestFragmentValidation(unittest.TestCase):
    """Test fragment validation with sentence boundaries and concept whitelists"""
    
    def setUp(self):
        self.validator = EnhancedValidator("prompting_claude_v1")
    
    def test_valid_fragments(self):
        """Test validation of good fragments"""
        valid_fragments = [
            "Define the role upfront with clear task description",
            "Use XML tags to structure and organize sections",
            "Set temperature=0 for deterministic output",
            "Prefill tokens to constrain response format",
            "CCN fit framework",  # Short but valid technical term
        ]
        
        for fragment in valid_fragments:
            with self.subTest(fragment=fragment):
                result = self.validator._validate_fragment_quality(fragment)
                self.assertEqual(result.quality, FragmentQuality.VALID, 
                               f"Fragment '{fragment}' should be valid: {result.reason}")
    
    def test_invalid_fragments_too_short(self):
        """Test rejection of too-short fragments"""
        short_fragments = [
            "Yes",
            "And",
            "",
            "The"
        ]
        
        for fragment in short_fragments:
            with self.subTest(fragment=fragment):
                result = self.validator._validate_fragment_quality(fragment)
                self.assertEqual(result.quality, FragmentQuality.TOO_SHORT)
    
    def test_invalid_fragments_sentence_boundary(self):
        """Test rejection of mid-sentence fragments"""
        bad_boundary_fragments = [
            "part of the Applied AICU here at Anthropic and with me is Christian",  # lowercase start
            "going to use a real world scenario and build",  # no proper ending
            "we can give more clear cut instructions and also make sure we",  # incomplete
        ]
        
        for fragment in bad_boundary_fragments:
            with self.subTest(fragment=fragment):
                result = self.validator._validate_fragment_quality(fragment)
                self.assertIn(result.quality, [FragmentQuality.MID_SENTENCE, FragmentQuality.UNKNOWN_CONCEPT])
    
    def test_invalid_fragments_speaker_tags(self):
        """Test rejection of fragments with speaker tags"""
        speaker_fragments = [
            "Hannah: So today we're going to talk about",
            "Christian → 42: This is an example of the form",
            "[00:15] The next step is to",
            "SPEAKER A: Let me explain this concept",
        ]
        
        for fragment in speaker_fragments:
            with self.subTest(fragment=fragment):
                result = self.validator._validate_fragment_quality(fragment)
                self.assertEqual(result.quality, FragmentQuality.SPEAKER_TAGS)
    
    def test_concept_whitelist_prompting(self):
        """Test concept whitelist for prompting content"""
        # Valid concepts
        valid_concepts = [
            "System prompt definition",
            "XML tag structure", 
            "Temperature equals zero",
            "Prefill token constraint",
            "JSON schema format"
        ]
        
        for concept in valid_concepts:
            with self.subTest(concept=concept):
                self.assertTrue(self.validator._matches_concept_whitelist(concept),
                              f"'{concept}' should match prompting whitelist")
        
        # Invalid concepts for prompting
        invalid_concepts = [
            "Thumbnail optimization strategy",
            "YouTube algorithm secrets",
            "Subscriber growth tactics",
        ]
        
        for concept in invalid_concepts:
            with self.subTest(concept=concept):
                self.assertFalse(self.validator._matches_concept_whitelist(concept),
                               f"'{concept}' should NOT match prompting whitelist")
    
    def test_concept_whitelist_youtube(self):
        """Test concept whitelist for YouTube content"""
        youtube_validator = EnhancedValidator("yt_playbook_v1")
        
        # Valid YouTube concepts
        valid_concepts = [
            "CCN fit for thumbnails",
            "270x views increase", 
            "A→Z content journey",
            "First 7 seconds retention"
        ]
        
        for concept in valid_concepts:
            with self.subTest(concept=concept):
                self.assertTrue(youtube_validator._matches_concept_whitelist(concept),
                              f"'{concept}' should match YouTube whitelist")


class TestSchemaCompliance(unittest.TestCase):
    """Test schema compliance and round-trip validation"""
    
    def setUp(self):
        self.validator = EnhancedValidator("prompting_claude_v1")
    
    def test_valid_prompting_schema(self):
        """Test validation of compliant prompting schema"""
        valid_extraction = {
            "schema_version": "prompting_claude_v1",
            "structure": {
                "role": "You are an AI assistant for analyzing car accident forms",
                "tone": "Be factual and confident",
                "constants": ["Swedish accident form", "17 rows", "Vehicle A and B columns"],
                "delimiters": ["XML", "Markdown"],
                "ordered_steps": [
                    "Read constants first",
                    "Analyze form then sketch",
                    "Make determination with evidence"
                ],
                "guardrails": [
                    "Only answer if confident",
                    "Cite explicit evidence", 
                    "Return insufficient_evidence if unclear"
                ],
                "output_schema": '{"fault": "A|B|both|neither|insufficient_evidence", "evidence": ["string"]}',
                "prefill": "Begin response with: {",
                "runtime_params": {"temperature": 0, "max_tokens": 1500}
            },
            "template": "Complete prompt template",
            "checklist": ["Role defined", "Schema present", "Prefill set"]
        }
        
        schema_result = self.validator._validate_schema_compliance(valid_extraction)
        self.assertTrue(schema_result["valid"])
        self.assertGreater(schema_result["completeness_score"], 0.8)
    
    def test_invalid_schema_missing_fields(self):
        """Test detection of missing required fields"""
        invalid_extraction = {
            "schema_version": "prompting_claude_v1",
            "structure": {
                "role": "You are an AI assistant",
                # Missing: tone, constants, ordered_steps, guardrails, output_schema, prefill
            }
        }
        
        schema_result = self.validator._validate_schema_compliance(invalid_extraction)
        self.assertFalse(schema_result["valid"])
        self.assertLess(schema_result["completeness_score"], 0.5)
        self.assertTrue(len(schema_result["errors"]) > 0)
    
    def test_round_trip_validation(self):
        """Test round-trip validation of extracted templates"""
        good_extraction = {
            "schema_version": "prompting_claude_v1",
            "structure": {
                "role": "You are a claims analysis assistant",
                "tone": "Be factual and confident", 
                "constants": ["Form has 17 rows", "Two vehicle columns"],
                "ordered_steps": ["Read form first", "Then analyze sketch"],
                "guardrails": ["Only if confident", "Cite evidence"],
                "output_schema": '{"fault": "A|B|insufficient"}',
                "prefill": "Begin with: {",
                "runtime_params": {"temperature": 0}
            },
            "template": "Structured template content"
        }
        
        round_trip_result = self.validator.round_trip_validate(good_extraction)
        
        self.assertTrue(round_trip_result["valid"])
        self.assertTrue(round_trip_result["template_viability"]["usable"])
        self.assertGreater(round_trip_result["usability_score"], 0.7)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.validator = EnhancedValidator("prompting_claude_v1")
        self.selector = RubricSelector()
    
    def test_empty_transcript(self):
        """Test handling of empty transcript"""
        selection = self.selector.select_rubric("", "")
        self.assertEqual(selection.detection_method, "fallback")
        
        validation = self.validator.validate_extraction({})
        self.assertFalse(validation["overall_valid"])
    
    def test_ocr_noise(self):
        """Test handling of OCR noise and non-English text"""
        noisy_text = """
        Rôle définition: Vous êtes un système d'IA pour l'analyse des formulaires d'accident.
        Gårdsräkning: Analyser först formuläret, sedan skissen.
        Température = 0 för determinism.
        Output: {"fault": "A|B|insufficient", "evidence": ["row_3_checked"]}
        """
        
        # Should still detect some prompting concepts despite noise
        selection = self.selector.select_rubric(noisy_text, "Mixed Language Prompting")
        # Should fall back gracefully rather than crash
        self.assertIsNotNone(selection.rubric_name)
    
    def test_conflicting_evidence(self):
        """Test handling of conflicting signals"""
        conflicting_text = """
        This content talks about both system prompts and XML structure for AI,
        but also mentions CCN fit and thumbnail optimization for YouTube growth.
        Temperature=0 for determinism, but also 270x views increase.
        """
        
        selection = self.selector.select_rubric(conflicting_text, "Mixed Content")
        # Should make a decision rather than failing
        self.assertIsNotNone(selection.rubric_name)
        self.assertIn("both prompting and YouTube", selection.reasoning.lower() or "")
    
    def test_very_long_input(self):
        """Test truncation handling for very long inputs"""
        long_text = "This is prompting content. " * 1000  # Very repetitive long text
        
        selection = self.selector.select_rubric(long_text[:5000], "Long Content")  # Simulate truncation
        self.assertIsNotNone(selection.rubric_name)
        
        # Validation should handle long inputs gracefully
        long_extraction = {
            "schema_version": "prompting_claude_v1",
            "frameworks": [{"name": f"Framework {i}"} for i in range(100)]  # Many items
        }
        
        validation = self.validator.validate_extraction(long_extraction)
        self.assertIsNotNone(validation["quality_score"])
    
    def test_missing_sketch_form_scenario(self):
        """Test the missing sketch or form scenario mentioned in requirements"""
        # This would be tested in the actual extraction pipeline, 
        # but we can test the validation handles missing data
        incomplete_extraction = {
            "schema_version": "prompting_claude_v1",
            "structure": {
                "role": "Accident analyst",
                "guardrails": [
                    "If form is missing, return insufficient_evidence",
                    "If sketch is missing, analyze form only", 
                    "Never invent missing information"
                ],
                "output_schema": '{"fault": "insufficient_evidence", "reason": "missing_input"}',
                "prefill": "{"
            }
        }
        
        validation = self.validator.validate_extraction(incomplete_extraction)
        # Should validate the guardrails handle missing inputs properly
        self.assertIn("guardrails", validation["validation_stages"]["schema"]["completeness_score"] or {})


class TestTelemetrySystem(unittest.TestCase):
    """Test telemetry and provenance tracking"""
    
    def setUp(self):
        self.telemetry = TelemetryCollector()
    
    def test_provenance_creation(self):
        """Test creation of provenance metadata"""
        provenance = self.telemetry.create_provenance(
            transcriber="whisper",
            transcript_source="https://youtube.com/watch?v=test",
            transcript_length=5000,
            language="en"
        )
        
        self.assertEqual(provenance.transcriber, "whisper")
        self.assertEqual(provenance.transcript_source, "https://youtube.com/watch?v=test")
        self.assertEqual(provenance.transcript_length, 5000)
        self.assertIsNotNone(provenance.extraction_timestamp)
    
    def test_provenance_updates(self):
        """Test updating provenance with extraction details"""
        provenance = self.telemetry.create_provenance("scribe", "file.wav", 3000)
        
        # Update with extraction details
        updated = self.telemetry.update_provenance_extraction(
            provenance=provenance,
            rubric_used="prompting_claude_v1",
            rubric_selection_method="heuristic",
            extraction_method="openai_gpt4",
            fallback_triggered=False
        )
        
        self.assertEqual(updated.rubric_used, "prompting_claude_v1")
        self.assertEqual(updated.extraction_method, "openai_gpt4")
        self.assertFalse(updated.fallback_triggered)
    
    def test_fallback_tracking(self):
        """Test fallback scenario tracking"""
        provenance = self.telemetry.create_provenance("scribe", "url", 2000)
        
        # Simulate fallback scenario
        self.telemetry.update_provenance_extraction(
            provenance=provenance,
            rubric_used="prompting_claude_v1", 
            rubric_selection_method="fallback",
            extraction_method="heuristic_fallback",
            fallback_triggered=True,
            fallback_reason="OpenAI API unavailable"
        )
        
        self.assertTrue(provenance.fallback_triggered)
        self.assertEqual(provenance.fallback_reason, "OpenAI API unavailable")
        self.assertEqual(self.telemetry.fallback_count, 1)
    
    def test_session_report_generation(self):
        """Test session report generation"""
        # Add some mock extractions
        for i in range(3):
            provenance = self.telemetry.create_provenance(
                transcriber="whisper" if i % 2 == 0 else "scribe",
                transcript_source=f"test_{i}.wav",
                transcript_length=1000 * i
            )
            
            self.telemetry.update_provenance_extraction(
                provenance, "prompting_claude_v1", "heuristic", "openai_gpt4",
                fallback_triggered=(i == 2), fallback_reason="API timeout" if i == 2 else None
            )
            
            self.telemetry.log_extraction(f"test_{i}", provenance, {"schema_version": "prompting_claude_v1"})
        
        report = self.telemetry.generate_session_report()
        
        self.assertEqual(report["summary"]["total_extractions"], 3)
        self.assertIn("whisper", report["distributions"]["transcribers"])
        self.assertIn("scribe", report["distributions"]["transcribers"])
        self.assertGreater(report["summary"]["fallback_rate"], 0)  # Should be ~33%


def run_comprehensive_tests():
    """Run all test suites with detailed reporting"""
    print("🧪 Running comprehensive extraction system tests...")
    
    # Create test suite
    test_classes = [
        TestRubricSelection,
        TestFragmentValidation, 
        TestSchemaCompliance,
        TestEdgeCases,
        TestTelemetrySystem
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 TEST SUMMARY")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%" if result.testsRun > 0 else "0%")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print(f"\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback.split('\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)