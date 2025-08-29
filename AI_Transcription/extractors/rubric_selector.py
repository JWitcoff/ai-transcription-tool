"""
Rubric Selector - Automatic content-type detection and rubric selection
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class ContentType(Enum):
    PROMPTING_CLAUDE = "prompting_claude_v1"
    YOUTUBE_GROWTH = "yt_playbook_v1"
    UNKNOWN = "unknown"


@dataclass
class RubricSelection:
    rubric_name: str
    confidence: float
    detection_method: str  # "flag", "heuristic", "fallback"
    signals_found: List[str]
    reasoning: str


class RubricSelector:
    """Selects appropriate rubric based on content type detection"""
    
    def __init__(self):
        # Signal patterns for content type detection
        self.prompting_signals = {
            "system_prompt": [r"\bsystem\s+prompt\b", r"<system>", r"system\s*:", r"system\s+message"],
            "xml_tags": [r"<[a-zA-Z_][^>]*>", r"<\/[a-zA-Z_]+>", r"XML\s+tags?", r"delimiters?"],
            "prefill": [r"\bprefill\b", r"prefill\s+token", r"begin\s+your\s+response\s+with"],
            "temperature": [r"temperature\s*=\s*0", r"temperature\s*:\s*0", r"temp\s*=\s*0"],
            "output_schema": [r"output\s+schema", r"JSON\s+schema", r"output\s+format", r"response\s+format"],
            "few_shot": [r"few\s*[-\s]*shot", r"examples?:", r"example\s+input", r"example\s+output"],
            "guardrails": [r"guardrails?", r"safety", r"confidence\s+threshold", r"only\s+if\s+confident"],
            "constants": [r"constants?", r"invariants?", r"background\s+detail", r"context\s+information"],
            "caching": [r"caching", r"cache", r"prompt\s+caching", r"safe\s+to\s+cache"],
            "claude_specific": [r"\bclaude\b", r"anthropic", r"claude\s+code", r"AI\s+assistant"]
        }
        
        self.youtube_signals = {
            "ccn_fit": [r"\bCCN\s+fit\b", r"core,?\s*casual,?\s*(?:and\s+)?new", r"core\s+audience"],
            "timing_structure": [r"7/?15/?30", r"first\s+7\s+seconds", r"15\s*[-–]\s*30\s+seconds"],
            "az_map": [r"A\s*[→->]\s*Z", r"A\s+to\s+Z", r"journey\s+map", r"video\s+game\s+map"],
            "thumbnails": [r"thumbnails?", r"thumbnail\s+optimization", r"packaging"],
            "hide_vegetables": [r"hide\s+the\s+vegetables", r"meaningful\s+content.*entertaining"],
            "retention": [r"retention", r"watch\s+time", r"audience\s+retention", r"drop\s*[-\s]*off"],
            "youtube_metrics": [r"\d+[xX]\s*(?:more|increase|views)", r"\d+\s*million\s+(?:views|subs)", r"subscribers?"],
            "creator_terms": [r"creator", r"youtuber", r"channel", r"upload", r"monetiz"],
            "growth_tactics": [r"growth", r"viral", r"algorithm", r"shorts", r"long\s*[-\s]*form"]
        }
        
        # Minimum confidence thresholds
        self.min_confidence = {
            ContentType.PROMPTING_CLAUDE: 0.6,
            ContentType.YOUTUBE_GROWTH: 0.5,
            ContentType.UNKNOWN: 0.0
        }
    
    def select_rubric(self, transcript: str, video_title: str = "", 
                     explicit_rubric: Optional[str] = None) -> RubricSelection:
        """
        Select appropriate rubric based on content analysis
        
        Args:
            transcript: The content to analyze
            video_title: Optional video title for additional context
            explicit_rubric: Override rubric selection (--rubric flag)
            
        Returns:
            RubricSelection with chosen rubric and reasoning
        """
        # 1. Explicit flag takes priority
        if explicit_rubric:
            if explicit_rubric in ["prompting_claude_v1", "yt_playbook_v1"]:
                return RubricSelection(
                    rubric_name=explicit_rubric,
                    confidence=1.0,
                    detection_method="flag",
                    signals_found=[],
                    reasoning=f"Explicitly set via --rubric {explicit_rubric}"
                )
        
        # 2. Run heuristic detection
        combined_text = f"{video_title} {transcript}".lower()
        
        prompting_score, prompting_signals = self._score_content(combined_text, self.prompting_signals)
        youtube_score, youtube_signals = self._score_content(combined_text, self.youtube_signals)
        
        # 3. Determine best match
        if prompting_score >= self.min_confidence[ContentType.PROMPTING_CLAUDE] and prompting_score > youtube_score:
            return RubricSelection(
                rubric_name=ContentType.PROMPTING_CLAUDE.value,
                confidence=prompting_score,
                detection_method="heuristic",
                signals_found=prompting_signals,
                reasoning=f"Prompting content detected (score: {prompting_score:.2f} vs YouTube: {youtube_score:.2f})"
            )
        elif youtube_score >= self.min_confidence[ContentType.YOUTUBE_GROWTH] and youtube_score > prompting_score:
            return RubricSelection(
                rubric_name=ContentType.YOUTUBE_GROWTH.value,
                confidence=youtube_score,
                detection_method="heuristic",
                signals_found=youtube_signals,
                reasoning=f"YouTube growth content detected (score: {youtube_score:.2f} vs Prompting: {prompting_score:.2f})"
            )
        else:
            # 4. Fallback to prompting as default (more general)
            return RubricSelection(
                rubric_name=ContentType.PROMPTING_CLAUDE.value,
                confidence=max(prompting_score, 0.3),  # Minimum confidence for fallback
                detection_method="fallback",
                signals_found=prompting_signals + youtube_signals,
                reasoning=f"Fallback to prompting rubric (scores: prompting={prompting_score:.2f}, youtube={youtube_score:.2f})"
            )
    
    def _score_content(self, text: str, signal_patterns: Dict[str, List[str]]) -> Tuple[float, List[str]]:
        """Score content against signal patterns"""
        total_signals = 0
        found_signals = []
        weighted_score = 0.0
        
        # Weight different signal types
        signal_weights = {
            "system_prompt": 2.0, "xml_tags": 1.5, "prefill": 2.0, "temperature": 1.5,
            "ccn_fit": 2.0, "timing_structure": 2.0, "az_map": 1.8, "thumbnails": 1.2
        }
        
        for signal_type, patterns in signal_patterns.items():
            total_signals += 1
            weight = signal_weights.get(signal_type, 1.0)
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found_signals.append(f"{signal_type}:{pattern}")
                    weighted_score += weight
                    break  # Only count each signal type once
        
        # Normalize score (0-1 range)
        if total_signals == 0:
            return 0.0, found_signals
        
        max_possible_score = sum(signal_weights.get(sig, 1.0) for sig in signal_patterns.keys())
        normalized_score = min(weighted_score / max_possible_score, 1.0)
        
        return normalized_score, found_signals
    
    def get_available_rubrics(self) -> Dict[str, str]:
        """Get available rubrics with descriptions"""
        return {
            ContentType.PROMPTING_CLAUDE.value: "Prompt engineering and Claude interaction content",
            ContentType.YOUTUBE_GROWTH.value: "YouTube growth strategies and content creation",
        }
    
    def validate_rubric_name(self, rubric_name: str) -> bool:
        """Validate that rubric name is supported"""
        valid_names = {ct.value for ct in ContentType if ct != ContentType.UNKNOWN}
        return rubric_name in valid_names


class RubricLogger:
    """Logs rubric selection decisions for analysis"""
    
    def __init__(self):
        self.selections = []
    
    def log_selection(self, selection: RubricSelection, transcript_id: str = ""):
        """Log a rubric selection decision"""
        log_entry = {
            "transcript_id": transcript_id,
            "rubric": selection.rubric_name,
            "confidence": selection.confidence,
            "method": selection.detection_method,
            "signals": selection.signals_found,
            "reasoning": selection.reasoning
        }
        self.selections.append(log_entry)
        
        # Print for immediate feedback
        print(f"🎯 Rubric selected: {selection.rubric_name}")
        print(f"   Method: {selection.detection_method} (confidence: {selection.confidence:.2f})")
        print(f"   Signals: {', '.join(selection.signals_found[:3])}{'...' if len(selection.signals_found) > 3 else ''}")
        print(f"   Reasoning: {selection.reasoning}")
    
    def get_selection_stats(self) -> Dict[str, any]:
        """Get statistics on rubric selections"""
        if not self.selections:
            return {}
        
        rubric_counts = {}
        method_counts = {}
        avg_confidence = {}
        
        for entry in self.selections:
            rubric = entry["rubric"]
            method = entry["method"]
            confidence = entry["confidence"]
            
            rubric_counts[rubric] = rubric_counts.get(rubric, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
            
            if rubric not in avg_confidence:
                avg_confidence[rubric] = []
            avg_confidence[rubric].append(confidence)
        
        # Calculate averages
        for rubric in avg_confidence:
            avg_confidence[rubric] = sum(avg_confidence[rubric]) / len(avg_confidence[rubric])
        
        return {
            "total_selections": len(self.selections),
            "rubric_distribution": rubric_counts,
            "detection_methods": method_counts,
            "average_confidence": avg_confidence
        }