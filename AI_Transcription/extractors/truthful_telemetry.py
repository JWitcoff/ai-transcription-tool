"""
Truthful Telemetry System - Verifiable metrics without fake data
Replaces inflated coverage percentages and framework counts with accurate measurements
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path


@dataclass
class TruthfulExtractionMetrics:
    """Verifiable metrics that can be independently validated"""
    
    # Accurate content counts (no inflated numbers)
    chapters_extracted: int = 0
    advice_items_extracted: int = 0
    total_items_extracted: int = 0
    
    # Quality indicators (boolean flags, not percentages)
    json_parseable: bool = False
    schema_compliant: bool = False
    has_required_fields: bool = False
    passes_fragment_validation: bool = False
    
    # Processing metadata (factual)
    extraction_method: str = "unknown"
    rubric_used: str = "unknown" 
    fallback_triggered: bool = False
    processing_time_ms: Optional[float] = None
    
    # Provenance (verifiable sources)
    transcriber_used: str = "unknown"
    transcript_length_chars: int = 0
    timestamp_alignment_success: bool = False
    aligned_chapters_count: int = 0
    
    # Error tracking (honest failure reporting)
    validation_errors: List[str] = None
    guard_rejections: List[str] = None
    contract_violations: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
        if self.guard_rejections is None:
            self.guard_rejections = []
        if self.contract_violations is None:
            self.contract_violations = []
        
        # Calculate total items from verified components
        self.total_items_extracted = self.chapters_extracted + self.advice_items_extracted


@dataclass  
class TruthfulSessionStats:
    """Session-level statistics that are verifiable and meaningful"""
    
    session_id: str
    session_start: str
    total_extractions_attempted: int = 0
    total_extractions_successful: int = 0
    
    # Provider usage (factual)
    elevenlabs_scribe_used: int = 0
    whisper_used: int = 0
    
    # Contract compliance (measurable)
    contract_compliant_extractions: int = 0
    contract_violations_detected: int = 0
    
    # Quality gates (pass/fail counts)
    fragment_validation_passes: int = 0
    timestamp_alignment_successes: int = 0
    
    # Processing efficiency (measurable)
    avg_processing_time_ms: Optional[float] = None
    fallback_usage_count: int = 0
    
    # Honest success metrics
    @property
    def success_rate(self) -> float:
        """Actual success rate (not inflated)"""
        if self.total_extractions_attempted == 0:
            return 0.0
        return self.total_extractions_successful / self.total_extractions_attempted
    
    @property
    def contract_compliance_rate(self) -> float:
        """Contract compliance rate (verifiable)"""
        if self.total_extractions_successful == 0:
            return 0.0
        return self.contract_compliant_extractions / self.total_extractions_successful


class TruthfulTelemetryCollector:
    """Collects only truthful, verifiable metrics"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.cwd() / "truthful_telemetry"
        self.output_dir.mkdir(exist_ok=True)
        
        # Session tracking
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_stats = TruthfulSessionStats(
            session_id=session_id,
            session_start=datetime.now().isoformat()
        )
        
        # Individual extraction records
        self.extraction_records: List[Dict[str, Any]] = []
        
    def record_extraction_attempt(self, 
                                extraction_result: Dict[str, Any],
                                transcript_metadata: Dict[str, Any],
                                processing_metadata: Dict[str, Any]) -> TruthfulExtractionMetrics:
        """Record a single extraction with truthful metrics"""
        
        self.session_stats.total_extractions_attempted += 1
        
        # Create truthful metrics by counting actual extracted content
        metrics = TruthfulExtractionMetrics()
        
        # Count actual chapters and advice (no inflation)
        chapters = extraction_result.get("chapters", [])
        advice = extraction_result.get("advice", [])
        
        if isinstance(chapters, list):
            metrics.chapters_extracted = len(chapters)
        if isinstance(advice, list):
            metrics.advice_items_extracted = len(advice)
            
        # Verify JSON structure (boolean, not percentage)
        try:
            json.dumps(extraction_result)
            metrics.json_parseable = True
        except (TypeError, ValueError):
            metrics.json_parseable = False
            
        # Check schema compliance (boolean, not score)
        required_fields = ["chapters", "advice"]
        metrics.has_required_fields = all(field in extraction_result for field in required_fields)
        
        # Record processing metadata (factual)
        metrics.extraction_method = processing_metadata.get("method", "unknown")
        metrics.rubric_used = processing_metadata.get("rubric", "unknown")
        metrics.fallback_triggered = processing_metadata.get("fallback_used", False)
        metrics.processing_time_ms = processing_metadata.get("duration_ms")
        
        # Record transcript metadata (verifiable)
        metrics.transcriber_used = transcript_metadata.get("provider", "unknown")
        transcript_text = transcript_metadata.get("text", "")
        metrics.transcript_length_chars = len(transcript_text) if transcript_text else 0
        
        # Check timestamp alignment (verifiable boolean)
        aligned_chapters = [c for c in chapters if isinstance(c, dict) and "start_ts" in c]
        metrics.aligned_chapters_count = len(aligned_chapters)
        metrics.timestamp_alignment_success = metrics.aligned_chapters_count > 0
        
        # Record validation issues (honest error reporting)
        validation_result = processing_metadata.get("validation", {})
        if isinstance(validation_result, dict):
            metrics.validation_errors = validation_result.get("errors", [])
            metrics.guard_rejections = validation_result.get("rejections", [])
            metrics.contract_violations = validation_result.get("violations", [])
            
        # Update session stats
        if metrics.json_parseable and metrics.has_required_fields:
            self.session_stats.total_extractions_successful += 1
            
        if metrics.has_required_fields and not metrics.contract_violations:
            self.session_stats.contract_compliant_extractions += 1
            
        if metrics.passes_fragment_validation:
            self.session_stats.fragment_validation_passes += 1
            
        if metrics.timestamp_alignment_success:
            self.session_stats.timestamp_alignment_successes += 1
            
        if metrics.fallback_triggered:
            self.session_stats.fallback_usage_count += 1
            
        # Track provider usage
        if "elevenlabs" in metrics.transcriber_used.lower() or "scribe" in metrics.transcriber_used.lower():
            self.session_stats.elevenlabs_scribe_used += 1
        elif "whisper" in metrics.transcriber_used.lower():
            self.session_stats.whisper_used += 1
            
        # Store extraction record
        extraction_record = {
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(metrics),
            "session_id": self.session_stats.session_id
        }
        self.extraction_records.append(extraction_record)
        
        return metrics
    
    def generate_truthful_summary(self, extraction_result: Dict[str, Any], metrics: TruthfulExtractionMetrics) -> str:
        """Generate a truthful, non-inflated summary for display"""
        
        summary_parts = []
        
        # Honest content summary (no fake frameworks)
        if metrics.chapters_extracted > 0 or metrics.advice_items_extracted > 0:
            summary_parts.append("## 📊 EXTRACTION SUMMARY")
            summary_parts.append(f"**Chapters:** {metrics.chapters_extracted}")
            summary_parts.append(f"**Advice:** {metrics.advice_items_extracted}")
            summary_parts.append(f"**Total Items:** {metrics.total_items_extracted}")
        else:
            summary_parts.append("## ⚠️ EXTRACTION SUMMARY")
            summary_parts.append("**Status:** No structured content extracted")
            
        # Quality indicators (honest pass/fail, not percentages)
        quality_parts = []
        if metrics.json_parseable:
            quality_parts.append("✅ Valid JSON")
        if metrics.has_required_fields:
            quality_parts.append("✅ Required fields present")
        if metrics.timestamp_alignment_success:
            quality_parts.append(f"✅ Timestamps aligned ({metrics.aligned_chapters_count} chapters)")
            
        if quality_parts:
            summary_parts.append("**Quality:** " + ", ".join(quality_parts))
            
        # Processing info (factual)
        summary_parts.append(f"**Source:** {metrics.transcriber_used}")
        summary_parts.append(f"**Method:** {metrics.extraction_method}")
        if metrics.rubric_used != "unknown":
            summary_parts.append(f"**Rubric:** {metrics.rubric_used}")
            
        # Honest error reporting
        if metrics.validation_errors or metrics.guard_rejections or metrics.contract_violations:
            summary_parts.append("")
            summary_parts.append("## ⚠️ VALIDATION ISSUES")
            
            if metrics.contract_violations:
                summary_parts.append(f"**Contract violations:** {len(metrics.contract_violations)}")
                for violation in metrics.contract_violations[:3]:  # Show top 3
                    summary_parts.append(f"  - {violation}")
                    
            if metrics.guard_rejections:
                summary_parts.append(f"**Fragment rejections:** {len(metrics.guard_rejections)}")
                    
            if metrics.validation_errors:
                summary_parts.append(f"**Validation errors:** {len(metrics.validation_errors)}")
        
        return "\n".join(summary_parts)
    
    def get_session_report(self) -> Dict[str, Any]:
        """Get truthful session statistics"""
        
        # Calculate average processing time
        processing_times = [
            record["metrics"]["processing_time_ms"] 
            for record in self.extraction_records 
            if record["metrics"]["processing_time_ms"] is not None
        ]
        
        if processing_times:
            self.session_stats.avg_processing_time_ms = sum(processing_times) / len(processing_times)
        
        return {
            "session_stats": asdict(self.session_stats),
            "total_records": len(self.extraction_records),
            "last_updated": datetime.now().isoformat(),
            "metrics_version": "truthful_v1.0"
        }
    
    def print_session_summary(self):
        """Print truthful session summary (no fake metrics)"""
        stats = self.session_stats
        
        print(f"\n📈 TRUTHFUL SESSION SUMMARY ({stats.session_id})")
        print(f"   Extractions attempted: {stats.total_extractions_attempted}")
        print(f"   Extractions successful: {stats.total_extractions_successful}")
        print(f"   Success rate: {stats.success_rate:.1%}")
        
        if stats.total_extractions_successful > 0:
            print(f"   Contract compliance: {stats.contract_compliance_rate:.1%}")
            
        print(f"   Provider usage: Scribe({stats.elevenlabs_scribe_used}) Whisper({stats.whisper_used})")
        
        if stats.fallback_usage_count > 0:
            print(f"   Fallbacks used: {stats.fallback_usage_count}")
            
        if stats.avg_processing_time_ms:
            print(f"   Avg processing time: {stats.avg_processing_time_ms:.0f}ms")
    
    def save_session_report(self):
        """Save truthful session report to file"""
        report = self.get_session_report()
        
        report_file = self.output_dir / f"truthful_session_{self.session_stats.session_id}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"✅ Truthful telemetry saved: {report_file}")
        except Exception as e:
            print(f"⚠️ Failed to save truthful telemetry: {e}")


def replace_fake_quality_check(extraction_result: Dict[str, Any], 
                              truthful_metrics: TruthfulExtractionMetrics) -> Dict[str, Any]:
    """Replace fake quality_check with truthful summary"""
    
    # Remove fake coverage data
    if "quality_check" in extraction_result:
        del extraction_result["quality_check"]
    
    # Add truthful quality summary
    extraction_result["truthful_quality"] = {
        "items_extracted": truthful_metrics.total_items_extracted,
        "chapters": truthful_metrics.chapters_extracted,
        "advice": truthful_metrics.advice_items_extracted,
        "json_valid": truthful_metrics.json_parseable,
        "schema_compliant": truthful_metrics.has_required_fields,
        "timestamp_alignment": {
            "success": truthful_metrics.timestamp_alignment_success,
            "chapters_aligned": truthful_metrics.aligned_chapters_count
        },
        "processing": {
            "method": truthful_metrics.extraction_method,
            "rubric": truthful_metrics.rubric_used,
            "fallback_used": truthful_metrics.fallback_triggered
        },
        "validation_summary": {
            "errors": len(truthful_metrics.validation_errors),
            "rejections": len(truthful_metrics.guard_rejections), 
            "violations": len(truthful_metrics.contract_violations)
        }
    }
    
    return extraction_result


def log_truthful_extraction(transcript_id: str,
                          extraction_result: Dict[str, Any],
                          transcript_metadata: Dict[str, Any], 
                          processing_metadata: Dict[str, Any],
                          collector: TruthfulTelemetryCollector) -> str:
    """Log extraction with truthful metrics and return summary"""
    
    # Record truthful metrics
    truthful_metrics = collector.record_extraction_attempt(
        extraction_result, transcript_metadata, processing_metadata
    )
    
    # Generate truthful summary
    truthful_summary = collector.generate_truthful_summary(extraction_result, truthful_metrics)
    
    # Clean up fake data in result
    cleaned_result = replace_fake_quality_check(extraction_result, truthful_metrics)
    
    # Log to console
    print(f"\n🔍 TRUTHFUL EXTRACTION LOG ({transcript_id})")
    print(f"   Items extracted: {truthful_metrics.total_items_extracted} (chapters: {truthful_metrics.chapters_extracted}, advice: {truthful_metrics.advice_items_extracted})")
    print(f"   JSON valid: {truthful_metrics.json_parseable}")
    print(f"   Schema compliant: {truthful_metrics.has_required_fields}")
    print(f"   Provider: {truthful_metrics.transcriber_used}")
    print(f"   Method: {truthful_metrics.extraction_method}")
    
    if truthful_metrics.validation_errors or truthful_metrics.guard_rejections:
        issue_count = len(truthful_metrics.validation_errors) + len(truthful_metrics.guard_rejections)
        print(f"   ⚠️ Validation issues: {issue_count}")
    
    return truthful_summary


# Global collector instance for session tracking
_global_collector: Optional[TruthfulTelemetryCollector] = None


def get_global_collector() -> TruthfulTelemetryCollector:
    """Get or create global truthful telemetry collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = TruthfulTelemetryCollector()
    return _global_collector


def finalize_session():
    """Print and save final session summary"""
    global _global_collector
    if _global_collector is not None:
        _global_collector.print_session_summary()
        _global_collector.save_session_report()
        _global_collector = None