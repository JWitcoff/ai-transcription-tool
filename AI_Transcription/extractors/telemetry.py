"""
Enhanced Telemetry System - Provenance tracking and quality metrics
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class ExtractionMethod(Enum):
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    HEURISTIC_FALLBACK = "heuristic_fallback"
    UNKNOWN = "unknown"


class TranscriberType(Enum):
    ELEVENLABS_SCRIBE = "scribe"
    OPENAI_WHISPER = "whisper"
    UNKNOWN = "unknown"


@dataclass
class ProvenanceMetadata:
    """Complete provenance information for an extraction"""
    # Input provenance
    transcriber: str  # whisper|scribe
    transcript_source: str  # url, file, live, etc.
    transcript_length: int
    language: str
    
    # Processing provenance  
    rubric_used: str  # prompting_claude_v1, yt_playbook_v1
    rubric_selection_method: str  # flag, heuristic, fallback
    extraction_method: str  # openai_gpt4, heuristic_fallback
    fallback_triggered: bool
    fallback_reason: Optional[str]
    
    # Quality metrics
    json_valid: bool
    prose_leak: bool
    fragment_quality_score: float
    schema_compliance_score: float
    round_trip_valid: bool
    
    # Timing
    extraction_timestamp: str
    processing_duration_ms: Optional[float]
    
    # Version info
    extractor_version: str = "1.0.0"
    schema_version: str = "prompting_claude_v1"


class TelemetryCollector:
    """Collects and manages telemetry data"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.cwd() / "telemetry"
        self.output_dir.mkdir(exist_ok=True)
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.extractions = []
        
        # Counters
        self.success_count = 0
        self.fallback_count = 0
        self.error_count = 0
    
    def create_provenance(self, 
                         transcriber: str,
                         transcript_source: str,
                         transcript_length: int,
                         language: str = "en") -> ProvenanceMetadata:
        """Create initial provenance metadata"""
        return ProvenanceMetadata(
            transcriber=transcriber,
            transcript_source=transcript_source,
            transcript_length=transcript_length,
            language=language,
            rubric_used="unknown",
            rubric_selection_method="unknown",
            extraction_method="unknown",
            fallback_triggered=False,
            fallback_reason=None,
            json_valid=False,
            prose_leak=False,
            fragment_quality_score=0.0,
            schema_compliance_score=0.0,
            round_trip_valid=False,
            extraction_timestamp=datetime.now().isoformat()
        )
    
    def update_provenance_extraction(self,
                                   provenance: ProvenanceMetadata,
                                   rubric_used: str,
                                   rubric_selection_method: str,
                                   extraction_method: str,
                                   fallback_triggered: bool = False,
                                   fallback_reason: Optional[str] = None) -> ProvenanceMetadata:
        """Update provenance with extraction details"""
        provenance.rubric_used = rubric_used
        provenance.rubric_selection_method = rubric_selection_method
        provenance.extraction_method = extraction_method
        provenance.fallback_triggered = fallback_triggered
        provenance.fallback_reason = fallback_reason
        
        # Update counters
        if fallback_triggered:
            self.fallback_count += 1
        else:
            self.success_count += 1
            
        return provenance
    
    def update_provenance_quality(self,
                                provenance: ProvenanceMetadata,
                                json_valid: bool,
                                prose_leak: bool,
                                fragment_quality_score: float,
                                schema_compliance_score: float,
                                round_trip_valid: bool) -> ProvenanceMetadata:
        """Update provenance with quality metrics"""
        provenance.json_valid = json_valid
        provenance.prose_leak = prose_leak
        provenance.fragment_quality_score = fragment_quality_score
        provenance.schema_compliance_score = schema_compliance_score
        provenance.round_trip_valid = round_trip_valid
        
        return provenance
    
    def log_extraction(self,
                      transcript_id: str,
                      provenance: ProvenanceMetadata,
                      extraction_result: Dict[str, Any],
                      validation_result: Optional[Dict[str, Any]] = None) -> None:
        """Log a complete extraction with results"""
        
        log_entry = {
            "transcript_id": transcript_id,
            "session_id": self.session_id,
            "provenance": asdict(provenance),
            "extraction_summary": {
                "schema_version": extraction_result.get("schema_version"),
                "items_extracted": self._count_extracted_items(extraction_result),
                "has_template": bool(extraction_result.get("template")),
                "has_checklist": bool(extraction_result.get("checklist"))
            },
            "validation_summary": validation_result.get("validation_stages", {}) if validation_result else {}
        }
        
        self.extractions.append(log_entry)
        
        # Log to console with appropriate status
        status = self._get_extraction_status(provenance, validation_result)
        self._print_extraction_log(transcript_id, provenance, status)
        
        # Save to file
        self._save_extraction_log(transcript_id, log_entry)
    
    def _count_extracted_items(self, extraction: Dict) -> Dict[str, int]:
        """Count items by type in extraction"""
        counts = {}
        
        # Count different item types
        for field in ["frameworks", "metrics", "case_studies", "preserved_terms"]:
            items = extraction.get(field, [])
            counts[field] = len(items) if isinstance(items, list) else (1 if items else 0)
        
        # For prompting schema, count structure elements
        if extraction.get("schema_version") == "prompting_claude_v1":
            structure = extraction.get("structure", {})
            for field in ["ordered_steps", "examples_fewshot", "guardrails"]:
                items = structure.get(field, [])
                counts[f"structure_{field}"] = len(items) if isinstance(items, list) else (1 if items else 0)
        
        return counts
    
    def _get_extraction_status(self, provenance: ProvenanceMetadata, validation: Optional[Dict]) -> str:
        """Determine overall extraction status"""
        if not validation:
            return "⚠️  NO_VALIDATION"
        
        if not validation.get("overall_valid", False):
            return "❌ FAILED"
        elif provenance.fallback_triggered:
            return "🔄 FALLBACK"
        elif provenance.fragment_quality_score < 0.8:
            return "⚠️  LOW_QUALITY"
        else:
            return "✅ SUCCESS"
    
    def _print_extraction_log(self, transcript_id: str, provenance: ProvenanceMetadata, status: str):
        """Print extraction log to console"""
        print(f"\n📊 EXTRACTION TELEMETRY")
        print(f"   ID: {transcript_id}")
        print(f"   Status: {status}")
        print(f"   Transcriber: {provenance.transcriber}")
        print(f"   Rubric: {provenance.rubric_used} ({provenance.rubric_selection_method})")
        print(f"   Extraction: {provenance.extraction_method}")
        
        if provenance.fallback_triggered:
            print(f"   ⚠️ Fallback: {provenance.fallback_reason}")
        
        quality_indicators = []
        if provenance.json_valid:
            quality_indicators.append("json_valid")
        if not provenance.prose_leak:
            quality_indicators.append("no_prose_leak") 
        if provenance.round_trip_valid:
            quality_indicators.append("round_trip_ok")
        
        if quality_indicators:
            print(f"   Quality: {', '.join(quality_indicators)}")
        
        print(f"   Scores: fragments={provenance.fragment_quality_score:.2f}, schema={provenance.schema_compliance_score:.2f}")
    
    def _save_extraction_log(self, transcript_id: str, log_entry: Dict):
        """Save individual extraction log to file"""
        log_file = self.output_dir / f"{transcript_id}_telemetry.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save telemetry log: {e}")
    
    def generate_session_report(self) -> Dict[str, Any]:
        """Generate summary report for the session"""
        if not self.extractions:
            return {"session_id": self.session_id, "total_extractions": 0}
        
        # Calculate aggregate metrics
        total_extractions = len(self.extractions)
        
        # Transcriber distribution
        transcriber_counts = {}
        rubric_counts = {}
        extraction_method_counts = {}
        fallback_reasons = {}
        
        quality_scores = {
            "fragment_scores": [],
            "schema_scores": [],
            "avg_fragment_quality": 0.0,
            "avg_schema_compliance": 0.0
        }
        
        for extraction in self.extractions:
            provenance = extraction["provenance"]
            
            # Count distributions
            transcriber = provenance["transcriber"]
            transcriber_counts[transcriber] = transcriber_counts.get(transcriber, 0) + 1
            
            rubric = provenance["rubric_used"]
            rubric_counts[rubric] = rubric_counts.get(rubric, 0) + 1
            
            method = provenance["extraction_method"]
            extraction_method_counts[method] = extraction_method_counts.get(method, 0) + 1
            
            if provenance["fallback_triggered"] and provenance["fallback_reason"]:
                reason = provenance["fallback_reason"]
                fallback_reasons[reason] = fallback_reasons.get(reason, 0) + 1
            
            # Collect quality scores
            quality_scores["fragment_scores"].append(provenance["fragment_quality_score"])
            quality_scores["schema_scores"].append(provenance["schema_compliance_score"])
        
        # Calculate averages
        if quality_scores["fragment_scores"]:
            quality_scores["avg_fragment_quality"] = sum(quality_scores["fragment_scores"]) / len(quality_scores["fragment_scores"])
        if quality_scores["schema_scores"]:
            quality_scores["avg_schema_compliance"] = sum(quality_scores["schema_scores"]) / len(quality_scores["schema_scores"])
        
        # Success rates
        success_rate = (self.success_count / total_extractions) * 100 if total_extractions > 0 else 0
        fallback_rate = (self.fallback_count / total_extractions) * 100 if total_extractions > 0 else 0
        
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_extractions": total_extractions,
                "success_count": self.success_count,
                "fallback_count": self.fallback_count,
                "error_count": self.error_count,
                "success_rate": round(success_rate, 1),
                "fallback_rate": round(fallback_rate, 1)
            },
            "distributions": {
                "transcribers": transcriber_counts,
                "rubrics": rubric_counts,
                "extraction_methods": extraction_method_counts,
                "fallback_reasons": fallback_reasons
            },
            "quality_metrics": quality_scores,
            "recommendations": self._generate_recommendations(
                transcriber_counts, fallback_rate, quality_scores["avg_fragment_quality"]
            )
        }
        
        # Save session report
        report_file = self.output_dir / f"session_{self.session_id}_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save session report: {e}")
        
        return report
    
    def _generate_recommendations(self, transcriber_counts: Dict, fallback_rate: float, avg_quality: float) -> List[str]:
        """Generate actionable recommendations based on telemetry"""
        recommendations = []
        
        # High fallback rate
        if fallback_rate > 30:
            recommendations.append("High fallback rate detected - consider improving primary extraction method or input quality")
        
        # Low quality scores
        if avg_quality < 0.6:
            recommendations.append("Low fragment quality - review concept whitelists and validation rules")
        
        # Transcriber performance
        if "whisper" in transcriber_counts and "scribe" in transcriber_counts:
            whisper_count = transcriber_counts["whisper"]
            scribe_count = transcriber_counts["scribe"]
            if whisper_count > scribe_count * 2:
                recommendations.append("Frequently falling back to Whisper - check ElevenLabs Scribe availability")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("System performing well - continue monitoring quality metrics")
        
        return recommendations
    
    def print_session_summary(self):
        """Print session summary to console"""
        report = self.generate_session_report()
        
        print(f"\n📈 SESSION SUMMARY ({self.session_id})")
        print(f"   Extractions: {report['summary']['total_extractions']}")
        print(f"   Success rate: {report['summary']['success_rate']}%")
        
        if report['summary']['fallback_count'] > 0:
            print(f"   Fallback rate: {report['summary']['fallback_rate']}%")
        
        quality = report['quality_metrics']
        print(f"   Avg quality: fragments={quality['avg_fragment_quality']:.2f}, schema={quality['avg_schema_compliance']:.2f}")
        
        # Top recommendation
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"   💡 {recommendations[0]}")


class QualityMonitor:
    """Monitors extraction quality and triggers alerts"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = alert_thresholds or {
            "fragment_quality_min": 0.7,
            "schema_compliance_min": 0.8,
            "fallback_rate_max": 0.3,
            "json_validity_min": 0.9
        }
        
        self.alerts = []
    
    def check_quality(self, provenance: ProvenanceMetadata, validation_result: Dict) -> List[str]:
        """Check extraction quality and return alerts"""
        alerts = []
        
        # Fragment quality
        if provenance.fragment_quality_score < self.thresholds["fragment_quality_min"]:
            alerts.append(f"Low fragment quality: {provenance.fragment_quality_score:.2f} < {self.thresholds['fragment_quality_min']}")
        
        # Schema compliance
        if provenance.schema_compliance_score < self.thresholds["schema_compliance_min"]:
            alerts.append(f"Low schema compliance: {provenance.schema_compliance_score:.2f} < {self.thresholds['schema_compliance_min']}")
        
        # JSON validity
        if not provenance.json_valid:
            alerts.append("Invalid JSON output detected")
        
        # Prose leak
        if provenance.prose_leak:
            alerts.append("Prose leak detected in structured output")
        
        # Round-trip failure
        if not provenance.round_trip_valid:
            alerts.append("Round-trip validation failed - output not usable")
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by type"""
        alert_counts = {}
        for alert in self.alerts:
            alert_type = alert.split(':')[0]  # Get part before ':'
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        return alert_counts


def detect_transcriber_type(metadata: Dict) -> str:
    """Detect transcriber type from metadata"""
    provider = metadata.get("provider", "").lower()
    
    if "elevenlabs" in provider or "scribe" in provider:
        return TranscriberType.ELEVENLABS_SCRIBE.value
    elif "whisper" in provider or "openai" in provider:
        return TranscriberType.OPENAI_WHISPER.value
    else:
        return TranscriberType.UNKNOWN.value


def detect_extraction_method(client_type: str, fallback_used: bool) -> str:
    """Detect extraction method used"""
    if fallback_used:
        return ExtractionMethod.HEURISTIC_FALLBACK.value
    elif "gpt-4" in client_type.lower():
        return ExtractionMethod.OPENAI_GPT4.value
    elif "gpt-3" in client_type.lower() or "gpt35" in client_type.lower():
        return ExtractionMethod.OPENAI_GPT35.value
    else:
        return ExtractionMethod.UNKNOWN.value