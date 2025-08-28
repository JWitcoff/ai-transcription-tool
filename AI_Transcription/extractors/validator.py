"""
Schema Validator - Validates extraction outputs against rubric with completeness scoring
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

class SchemaValidator:
    """Validates extraction outputs and calculates coverage scores"""
    
    def __init__(self, rubric_path: Optional[str] = None):
        """
        Initialize validator with rubric
        
        Args:
            rubric_path: Path to coverage rubric JSON file
        """
        if rubric_path is None:
            # Default to rubric in same directory
            rubric_path = Path(__file__).parent / "coverage_rubric.json"
        
        self.rubric = self._load_rubric(rubric_path)
        self.schema_version = self.rubric.get("schema_version", "yt_playbook_v1")
    
    def _load_rubric(self, rubric_path: Path) -> Dict:
        """Load the coverage rubric"""
        try:
            with open(rubric_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load rubric from {rubric_path}: {e}")
            return self._default_rubric()
    
    def _default_rubric(self) -> Dict:
        """Default rubric if file loading fails"""
        return {
            "schema_version": "yt_playbook_v1",
            "canonical_checklist": {},
            "scoring": {"thresholds": {"excellent": 0.8, "good": 0.6, "acceptable": 0.4}}
        }
    
    def validate_and_score(self, output: Dict, include_details: bool = True) -> Dict[str, Any]:
        """
        Validate extraction output against rubric and calculate coverage score
        
        Args:
            output: Extraction output to validate
            include_details: Whether to include detailed scoring breakdown
            
        Returns:
            Validation report with score and details
        """
        if not output:
            return self._empty_validation_report("Empty output provided")
        
        # Check schema version
        schema_valid = output.get("schema_version") == self.schema_version
        
        # Calculate coverage score
        coverage_result = self._calculate_coverage_score(output)
        
        # Identify gaps
        gaps = self._identify_gaps(output, coverage_result["details"])
        
        # Build validation report
        report = {
            "validation_timestamp": self._get_timestamp(),
            "schema_valid": schema_valid,
            "schema_version_found": output.get("schema_version"),
            "schema_version_expected": self.schema_version,
            "coverage_score": coverage_result["score"],
            "coverage_grade": self._get_coverage_grade(coverage_result["score"]),
            "gaps": gaps,
            "recommendations": self._generate_recommendations(gaps, coverage_result)
        }
        
        if include_details:
            report["scoring_details"] = coverage_result["details"]
            report["rubric_breakdown"] = self._get_rubric_breakdown(output)
        
        return report
    
    def _calculate_coverage_score(self, output: Dict) -> Dict[str, Any]:
        """Calculate weighted coverage score with completeness checking"""
        total_weight = 0
        achieved_score = 0
        scoring_details = {}
        
        checklist = self.rubric.get("canonical_checklist", {})
        
        for category_name, category_items in checklist.items():
            category_details = {}
            category_score = 0
            category_weight = 0
            
            for item_name, item_config in category_items.items():
                item_weight = item_config.get("weight", 1.0)
                category_weight += item_weight
                total_weight += item_weight
                
                # Check if item is present in output
                item_score = self._score_item_presence(
                    output, category_name, item_name, item_config
                )
                
                category_score += item_score * item_weight
                achieved_score += item_score * item_weight
                
                category_details[item_name] = {
                    "score": item_score,
                    "weight": item_weight,
                    "weighted_score": item_score * item_weight,
                    "completeness": self._assess_completeness(
                        output, category_name, item_name, item_config
                    )
                }
            
            scoring_details[category_name] = {
                "items": category_details,
                "category_score": category_score / category_weight if category_weight > 0 else 0,
                "category_weight": category_weight
            }
        
        final_score = achieved_score / total_weight if total_weight > 0 else 0
        
        return {
            "score": round(final_score, 3),
            "details": scoring_details,
            "total_weight": total_weight,
            "achieved_score": achieved_score
        }
    
    def _score_item_presence(self, output: Dict, category: str, item: str, config: Dict) -> float:
        """Score whether an item is present and how completely"""
        
        # Get category data from output
        category_data = output.get(category, {})
        if not category_data:
            return 0.0
        
        # Check for item using multiple strategies
        keywords = config.get("keywords", [])
        
        # Strategy 1: Direct item name match
        if self._check_direct_match(category_data, item):
            return 1.0
        
        # Strategy 2: Keyword matching in category content
        if self._check_keyword_match(category_data, keywords):
            return 0.8  # Slightly lower score for keyword match vs direct
        
        # Strategy 3: Check in preserved terms (for exact terminology)
        preserved_terms = output.get("preserved_terms", [])
        if self._check_preserved_terms_match(preserved_terms, keywords):
            return 0.9
        
        return 0.0
    
    def _check_direct_match(self, category_data: Any, item: str) -> bool:
        """Check for direct item name match"""
        if isinstance(category_data, dict):
            return item in category_data or item.replace("_", " ") in str(category_data).lower()
        elif isinstance(category_data, list):
            return any(item in str(entry).lower() or item.replace("_", " ") in str(entry).lower() 
                      for entry in category_data)
        else:
            return item in str(category_data).lower() or item.replace("_", " ") in str(category_data).lower()
    
    def _check_keyword_match(self, category_data: Any, keywords: List[str]) -> bool:
        """Check for keyword matches in category data"""
        if not keywords:
            return False
        
        category_text = str(category_data).lower()
        
        # Require at least 2 keywords to match (or 1 if only 1 keyword)
        matches = sum(1 for keyword in keywords if keyword.lower() in category_text)
        required_matches = min(2, len(keywords))
        
        return matches >= required_matches
    
    def _check_preserved_terms_match(self, preserved_terms: List[str], keywords: List[str]) -> bool:
        """Check if keywords appear in preserved terms"""
        if not keywords or not preserved_terms:
            return False
        
        preserved_lower = [term.lower() for term in preserved_terms]
        return any(keyword.lower() in preserved_lower for keyword in keywords)
    
    def _assess_completeness(self, output: Dict, category: str, item: str, config: Dict) -> Dict[str, Any]:
        """Assess how completely an item was extracted"""
        completeness_type = config.get("completeness")
        
        if not completeness_type:
            return {"type": "presence_only", "score": 1.0}
        
        category_data = output.get(category, {})
        
        if completeness_type == "all_three_audiences":
            return self._assess_audience_completeness(category_data)
        elif completeness_type == "all_intervals":
            return self._assess_timing_completeness(category_data)
        elif completeness_type == "count_of_six":
            return self._assess_influence_completeness(category_data, config)
        elif completeness_type == "has_quantified_results":
            return self._assess_metrics_completeness(category_data)
        else:
            return {"type": completeness_type, "score": 0.5, "note": "Completeness type not implemented"}
    
    def _assess_audience_completeness(self, category_data: Any) -> Dict[str, Any]:
        """Assess CCN fit completeness (Core, Casual, New audiences)"""
        text = str(category_data).lower()
        audiences = ["core", "casual", "new"]
        found_audiences = [aud for aud in audiences if aud in text]
        
        score = len(found_audiences) / 3  # 3 expected audiences
        
        return {
            "type": "audience_segmentation",
            "score": score,
            "found_audiences": found_audiences,
            "expected_audiences": audiences
        }
    
    def _assess_timing_completeness(self, category_data: Any) -> Dict[str, Any]:
        """Assess 7/15/30 timing completeness"""
        text = str(category_data).lower()
        intervals = ["0-7", "7-15", "15-30", "first 7", "7 seconds", "15 seconds", "30 seconds"]
        found_intervals = [interval for interval in intervals if interval in text]
        
        # Look for at least evidence of the three time periods
        has_0_7 = any(x in text for x in ["0-7", "first 7", "7 second"])
        has_7_15 = any(x in text for x in ["7-15", "15 second"])
        has_15_30 = any(x in text for x in ["15-30", "30 second"])
        
        found_count = sum([has_0_7, has_7_15, has_15_30])
        score = found_count / 3
        
        return {
            "type": "timing_intervals",
            "score": score,
            "found_intervals": found_intervals,
            "interval_coverage": {"0-7s": has_0_7, "7-15s": has_7_15, "15-30s": has_15_30}
        }
    
    def _assess_influence_completeness(self, category_data: Any, config: Dict) -> Dict[str, Any]:
        """Assess influence principles completeness (Cialdini's 6)"""
        text = str(category_data).lower()
        expected_principles = config.get("expected_items", ["scarcity", "consistency", "reciprocity", "consensus", "similarity", "authority"])
        
        found_principles = [principle for principle in expected_principles if principle in text]
        
        # Also check for alternative terms
        alternatives = {
            "consensus": ["social proof", "others", "popular"],
            "similarity": ["like us", "relatable", "similar"],
            "authority": ["expert", "credentials", "trust"]
        }
        
        for principle, alts in alternatives.items():
            if principle not in found_principles:
                if any(alt in text for alt in alts):
                    found_principles.append(principle)
        
        score = len(found_principles) / len(expected_principles)
        
        return {
            "type": "influence_principles",
            "score": score,
            "found_principles": found_principles,
            "expected_principles": expected_principles
        }
    
    def _assess_metrics_completeness(self, category_data: Any) -> Dict[str, Any]:
        """Assess whether metrics have quantified results"""
        if not category_data:
            return {"type": "metrics", "score": 0.0, "has_numbers": False}
        
        text = str(category_data)
        
        # Look for numbers with context
        import re
        number_patterns = [
            r'\d+x\b',  # Multipliers
            r'\d+%',    # Percentages
            r'\d+\s*(?:million|thousand|M|K|k)\b',  # Large numbers
            r'\d+\s*(?:times|fold)',  # Times/fold
            r'increased?\s+(?:by\s+)?\d+',  # Increases
        ]
        
        has_numbers = any(re.search(pattern, text, re.IGNORECASE) for pattern in number_patterns)
        
        # Look for context words
        context_words = ["increase", "improve", "boost", "growth", "views", "subscribers", "engagement"]
        has_context = any(word in text.lower() for word in context_words)
        
        score = 0.0
        if has_numbers and has_context:
            score = 1.0
        elif has_numbers:
            score = 0.6
        elif has_context:
            score = 0.3
        
        return {
            "type": "quantified_metrics",
            "score": score,
            "has_numbers": has_numbers,
            "has_context": has_context
        }
    
    def _identify_gaps(self, output: Dict, scoring_details: Dict) -> List[Dict[str, Any]]:
        """Identify gaps in extraction"""
        gaps = []
        
        # Check for critical gaps
        if not output.get("preserved_terms"):
            gaps.append({
                "type": "critical",
                "issue": "no_preserved_terminology",
                "description": "No verbatim terms preserved from original content"
            })
        
        if not output.get("frameworks"):
            gaps.append({
                "type": "critical", 
                "issue": "no_frameworks_identified",
                "description": "No named frameworks or structured approaches found"
            })
        
        if not output.get("metrics"):
            gaps.append({
                "type": "major",
                "issue": "no_quantified_evidence", 
                "description": "No metrics or quantified results extracted"
            })
        
        # Check category-specific gaps
        for category, details in scoring_details.items():
            category_score = details.get("category_score", 0)
            if category_score < 0.3:
                gaps.append({
                    "type": "major",
                    "issue": f"weak_{category}_extraction",
                    "description": f"Low coverage in {category} (score: {category_score:.2f})"
                })
        
        return gaps[:5]  # Return top 5 gaps
    
    def _generate_recommendations(self, gaps: List[Dict], coverage_result: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Address critical gaps first
        for gap in gaps:
            if gap["type"] == "critical":
                if gap["issue"] == "no_preserved_terminology":
                    recommendations.append("Improve terminology preservation by identifying quoted terms and proper nouns")
                elif gap["issue"] == "no_frameworks_identified":
                    recommendations.append("Look for structured approaches, named methods, or systematic patterns")
        
        # Coverage-based recommendations
        coverage_score = coverage_result.get("score", 0)
        if coverage_score < 0.4:
            recommendations.append("Consider using more specific extraction prompts targeting missing categories")
        elif coverage_score < 0.7:
            recommendations.append("Focus on completeness - extract all components of identified frameworks")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Continue extracting with current approach - coverage looks good")
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _get_coverage_grade(self, score: float) -> str:
        """Convert coverage score to grade"""
        thresholds = self.rubric.get("scoring", {}).get("thresholds", {})
        
        if score >= thresholds.get("excellent", 0.8):
            return "Excellent"
        elif score >= thresholds.get("good", 0.6):
            return "Good"
        elif score >= thresholds.get("acceptable", 0.4):
            return "Acceptable"
        else:
            return "Needs Improvement"
    
    def _get_rubric_breakdown(self, output: Dict) -> Dict[str, Any]:
        """Get breakdown of how output maps to rubric"""
        breakdown = {}
        checklist = self.rubric.get("canonical_checklist", {})
        
        for category, items in checklist.items():
            breakdown[category] = {
                "items_in_rubric": list(items.keys()),
                "items_found": [],
                "coverage_percentage": 0
            }
            
            # Check which items were found
            category_data = output.get(category, {})
            if category_data:
                for item in items.keys():
                    if self._check_direct_match(category_data, item) or \
                       self._check_keyword_match(category_data, items[item].get("keywords", [])):
                        breakdown[category]["items_found"].append(item)
                
                # Calculate coverage percentage for this category
                if items:
                    coverage = len(breakdown[category]["items_found"]) / len(items)
                    breakdown[category]["coverage_percentage"] = round(coverage * 100, 1)
        
        return breakdown
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _empty_validation_report(self, error_msg: str) -> Dict[str, Any]:
        """Return empty validation report for error cases"""
        return {
            "validation_timestamp": self._get_timestamp(),
            "error": error_msg,
            "schema_valid": False,
            "coverage_score": 0.0,
            "coverage_grade": "Failed",
            "gaps": [{"type": "critical", "issue": "validation_failed", "description": error_msg}],
            "recommendations": ["Please provide valid extraction output"]
        }