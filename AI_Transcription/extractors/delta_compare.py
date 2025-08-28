"""
Delta Compare - Compare two analysis outputs and identify differences
"""

from typing import Dict, List, Any
import json
from .validator import SchemaValidator

class DeltaCompare:
    """Compare analyses and identify coverage gaps and differences"""
    
    def __init__(self, rubric_path: str = None):
        self.validator = SchemaValidator(rubric_path)
    
    def compare_analyses(self, analysis1: Dict, analysis2: Dict, 
                        labels: tuple = ("Analysis 1", "Analysis 2")) -> Dict[str, Any]:
        """
        Compare two analyses using deterministic rubric scoring
        
        Args:
            analysis1: First analysis to compare
            analysis2: Second analysis to compare  
            labels: Labels for the analyses
            
        Returns:
            Comparison report with coverage scores and deltas
        """
        if not analysis1 or not analysis2:
            return self._empty_comparison("One or both analyses are empty")
        
        # Calculate coverage scores for both
        validation1 = self.validator.validate_and_score(analysis1, include_details=True)
        validation2 = self.validator.validate_and_score(analysis2, include_details=True)
        
        # Calculate delta between analyses
        delta = self._calculate_delta(analysis1, analysis2)
        
        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(
            validation1, validation2, delta
        )
        
        return {
            "comparison_timestamp": self._get_timestamp(),
            "labels": {"analysis1": labels[0], "analysis2": labels[1]},
            "coverage_scores": {
                labels[0]: {
                    "score": validation1["coverage_score"],
                    "grade": validation1["coverage_grade"]
                },
                labels[1]: {
                    "score": validation2["coverage_score"], 
                    "grade": validation2["coverage_grade"]
                }
            },
            "delta": delta,
            "recommendations": recommendations,
            "detailed_comparison": {
                "validation1": validation1,
                "validation2": validation2
            }
        }
    
    def _calculate_delta(self, analysis1: Dict, analysis2: Dict) -> Dict[str, Any]:
        """Calculate differences between two analyses"""
        delta = {
            "covered_by_both": [],
            "only_in_1": [],
            "only_in_2": [],
            "missing_from_both": []
        }
        
        # Compare frameworks
        frameworks1 = self._extract_framework_names(analysis1.get("frameworks", []))
        frameworks2 = self._extract_framework_names(analysis2.get("frameworks", []))
        
        delta["frameworks"] = {
            "both": list(set(frameworks1) & set(frameworks2)),
            "only_1": list(set(frameworks1) - set(frameworks2)),
            "only_2": list(set(frameworks2) - set(frameworks1))
        }
        
        # Compare metrics
        metrics1 = self._extract_metric_values(analysis1.get("metrics", []))
        metrics2 = self._extract_metric_values(analysis2.get("metrics", []))
        
        delta["metrics"] = {
            "both": list(set(metrics1) & set(metrics2)),
            "only_1": list(set(metrics1) - set(metrics2)),
            "only_2": list(set(metrics2) - set(metrics1))
        }
        
        # Compare preserved terms
        terms1 = set(analysis1.get("preserved_terms", []))
        terms2 = set(analysis2.get("preserved_terms", []))
        
        delta["preserved_terms"] = {
            "both": list(terms1 & terms2),
            "only_1": list(terms1 - terms2),
            "only_2": list(terms2 - terms1)
        }
        
        # Calculate overall coverage overlap
        categories = ["frameworks", "metrics", "psychology", "systems", "temporal_strategies", "authenticity"]
        category_coverage = {}
        
        for category in categories:
            has_1 = bool(analysis1.get(category))
            has_2 = bool(analysis2.get(category))
            
            if has_1 and has_2:
                category_coverage[category] = "both"
            elif has_1:
                category_coverage[category] = "only_1"
            elif has_2:
                category_coverage[category] = "only_2"
            else:
                category_coverage[category] = "neither"
        
        delta["category_coverage"] = category_coverage
        
        return delta
    
    def _extract_framework_names(self, frameworks: List) -> List[str]:
        """Extract framework names for comparison"""
        names = []
        if isinstance(frameworks, list):
            for fw in frameworks:
                if isinstance(fw, dict):
                    names.append(fw.get("name", ""))
                elif isinstance(fw, str):
                    names.append(fw)
        return [name for name in names if name]
    
    def _extract_metric_values(self, metrics: List) -> List[str]:
        """Extract metric values for comparison"""
        values = []
        if isinstance(metrics, list):
            for metric in metrics:
                if isinstance(metric, dict):
                    values.append(metric.get("value", ""))
                elif isinstance(metric, str):
                    values.append(metric)
        return [value for value in values if value]
    
    def _generate_comparison_recommendations(self, validation1: Dict, validation2: Dict, delta: Dict) -> List[str]:
        """Generate actionable recommendations based on comparison"""
        recommendations = []
        
        score1 = validation1.get("coverage_score", 0)
        score2 = validation2.get("coverage_score", 0)
        
        # Score-based recommendations
        if abs(score1 - score2) > 0.2:
            if score1 > score2:
                recommendations.append("Analysis 1 has significantly better coverage - investigate its extraction methods")
            else:
                recommendations.append("Analysis 2 has significantly better coverage - consider adopting its approach")
        
        # Framework-specific recommendations
        fw_delta = delta.get("frameworks", {})
        if fw_delta.get("only_1") and fw_delta.get("only_2"):
            recommendations.append("Both analyses found unique frameworks - combine insights from both")
        elif fw_delta.get("only_1"):
            recommendations.append("Analysis 1 found additional frameworks that Analysis 2 missed")
        elif fw_delta.get("only_2"):
            recommendations.append("Analysis 2 found additional frameworks that Analysis 1 missed")
        
        # Metrics recommendations
        metrics_delta = delta.get("metrics", {})
        if len(metrics_delta.get("only_1", [])) > len(metrics_delta.get("only_2", [])):
            recommendations.append("Analysis 1 extracted more quantified results")
        elif len(metrics_delta.get("only_2", [])) > len(metrics_delta.get("only_1", [])):
            recommendations.append("Analysis 2 extracted more quantified results")
        
        # Category coverage recommendations
        category_coverage = delta.get("category_coverage", {})
        missing_categories = [cat for cat, coverage in category_coverage.items() if coverage == "neither"]
        
        if missing_categories:
            recommendations.append(f"Both analyses missed: {', '.join(missing_categories)}")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Analyses show similar coverage - consider using either approach")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def compare_against_gold_standard(self, analysis: Dict, gold_standard_item: Dict) -> Dict[str, Any]:
        """
        Compare analysis against gold standard expected extraction
        
        Args:
            analysis: Analysis output to validate
            gold_standard_item: Gold standard test case
            
        Returns:
            Detailed comparison against expected results
        """
        expected = gold_standard_item.get("expected_extraction", {})
        expected_scores = gold_standard_item.get("expected_scores", {})
        
        # Validate against expected extraction
        validation = self.validator.validate_and_score(analysis)
        
        # Compare specific elements
        comparison = {
            "test_id": gold_standard_item.get("id"),
            "title": gold_standard_item.get("title"),
            "coverage_score": validation["coverage_score"],
            "expected_score": expected_scores.get("overall", 0.5),
            "score_delta": validation["coverage_score"] - expected_scores.get("overall", 0.5),
            "passes_threshold": validation["coverage_score"] >= expected_scores.get("overall", 0.5),
            "element_comparison": {}
        }
        
        # Compare each expected element
        for category, expected_items in expected.items():
            if category in analysis:
                comparison["element_comparison"][category] = {
                    "expected_count": len(expected_items) if isinstance(expected_items, list) else 1,
                    "actual_count": len(analysis[category]) if isinstance(analysis[category], list) else 1,
                    "found_expected": self._check_expected_items_found(analysis[category], expected_items)
                }
        
        return comparison
    
    def _check_expected_items_found(self, actual: Any, expected: Any) -> bool:
        """Check if expected items are found in actual results"""
        if isinstance(expected, list) and isinstance(actual, list):
            # For lists, check if key elements are present
            expected_names = [item.get("name", "") if isinstance(item, dict) else str(item) for item in expected]
            actual_names = [item.get("name", "") if isinstance(item, dict) else str(item) for item in actual]
            
            # Check if at least 50% of expected items are found
            found_count = sum(1 for name in expected_names if any(name.lower() in actual_name.lower() for actual_name in actual_names))
            return found_count >= len(expected_names) * 0.5
        
        # For other types, do string matching
        return str(expected).lower() in str(actual).lower()
    
    def run_gold_standard_regression(self, extractor, gold_standard_path: str = None) -> Dict[str, Any]:
        """
        Run regression test against gold standard dataset
        
        Args:
            extractor: DeepExtractor instance
            gold_standard_path: Path to gold standard JSON
            
        Returns:
            Regression test results
        """
        if gold_standard_path is None:
            from pathlib import Path
            gold_standard_path = Path(__file__).parent.parent / "test_data" / "gold_standard.json"
        
        try:
            with open(gold_standard_path, 'r', encoding='utf-8') as f:
                gold_standard = json.load(f)
        except Exception as e:
            return {"error": f"Could not load gold standard: {e}"}
        
        results = {
            "test_timestamp": self._get_timestamp(),
            "total_tests": len(gold_standard.get("transcripts", [])),
            "passed": 0,
            "failed": 0,
            "test_results": []
        }
        
        for test_case in gold_standard.get("transcripts", []):
            try:
                # Run extraction
                extraction = extractor.extract_all_lenses(
                    test_case["snippet"], 
                    "", 
                    test_case.get("title", "")
                )
                
                # Compare against expected
                comparison = self.compare_against_gold_standard(extraction, test_case)
                
                # Record result
                if comparison["passes_threshold"]:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                
                results["test_results"].append(comparison)
                
            except Exception as e:
                results["failed"] += 1
                results["test_results"].append({
                    "test_id": test_case.get("id"),
                    "error": f"Test failed: {e}",
                    "passes_threshold": False
                })
        
        results["pass_rate"] = results["passed"] / results["total_tests"] if results["total_tests"] > 0 else 0
        
        return results
    
    def _empty_comparison(self, error_msg: str) -> Dict[str, Any]:
        """Return empty comparison for error cases"""
        return {
            "comparison_timestamp": self._get_timestamp(),
            "error": error_msg,
            "coverage_scores": {},
            "delta": {},
            "recommendations": ["Please provide valid analyses to compare"]
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()