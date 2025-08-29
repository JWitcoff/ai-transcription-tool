"""
Contract-based output system with strict validation
Eliminates rubric leakage and enforces user-requested output formats
"""

from pydantic import BaseModel, Field, ValidationError, root_validator
from typing import List, Optional, Literal, Dict, Any
import json
import re


class Chapter(BaseModel):
    """Single chapter with title, summary, and optional timestamp"""
    title: str = Field(min_length=3, max_length=140)
    summary: str = Field(min_length=40, max_length=500)
    start_ts: Optional[float] = Field(None, ge=0)  # seconds

    @root_validator
    def validate_meaningful_content(cls, v):
        title = v.get("title", "")
        summary = v.get("summary", "")
        
        # Reject rubric artifact titles
        if any(bad in title.upper() for bad in ["CORE FRAMEWORKS", "PSYCHOLOGY", "QUICK START"]):
            raise ValueError(f"Chapter title appears to be rubric artifact: {title}")
        
        # Ensure title is descriptive, not just numbers/times
        if re.match(r"^\d+[:\-]\d+", title):
            raise ValueError("Chapter title should be descriptive, not just timestamps")
            
        return v


class Advice(BaseModel):
    """Single piece of actionable advice with category"""
    category: Literal[
        "acquisition", "community", "monetization", "ops", "schedule",
        "seasonality", "brand_safety", "org", "founder_risk", "security", 
        "platform", "creative", "health", "legal", "tools", "mindset"
    ] = Field(..., description="Business category for this advice")
    
    point: str = Field(min_length=20, max_length=240, description="Actionable advice point")

    @root_validator  
    def validate_actionable_advice(cls, v):
        point = v.get("point", "")
        
        # Reject fragments and incomplete sentences
        if point.startswith("'") and len(point) < 100:
            raise ValueError("Advice appears to be sentence fragment")
            
        # Ensure advice is imperative/actionable, not just description
        action_words = ["consider", "use", "avoid", "implement", "try", "focus", "ensure", "build", "create", "plan", "track", "measure", "optimize", "diversify", "budget", "hire", "test", "monitor", "schedule", "negotiate", "document"]
        if not any(word in point.lower() for word in action_words):
            # Check if it's still valid advice format
            if not any(char in point for char in [":", "→", "-", "•"]):
                raise ValueError("Advice should be actionable with clear implementation guidance")
        
        return v


class ChaptersAdvicePayload(BaseModel):
    """Strict contract for chapters + advice output format"""
    chapters: List[Chapter] = Field(min_items=1, max_items=20)
    advice: List[Advice] = Field(min_items=1, max_items=50)
    partial_segment: Optional[bool] = False
    provenance: Literal["contract_based", "rubric_based"] = "contract_based"

    @root_validator
    def minimal_contract_validation(cls, v):
        chapters = v.get("chapters", [])
        advice = v.get("advice", [])
        
        if not chapters:
            raise ValueError("At least one chapter is required")
        if not advice:
            raise ValueError("At least one advice point is required")
            
        # Ensure reasonable distribution 
        if len(chapters) > len(advice) * 2:
            raise ValueError("Too many chapters relative to advice - may be over-segmented")
            
        return v


def enforce_contract(payload: Dict[str, Any]) -> ChaptersAdvicePayload:
    """
    Parse and ensure no extra top-level keys sneak in
    
    Args:
        payload: Raw extraction output
        
    Returns:
        Validated ChaptersAdvicePayload
        
    Raises:
        ValueError: If contract violations found
    """
    # Check for forbidden keys (rubric artifacts)
    allowed = {"chapters", "advice", "partial_segment", "provenance"}
    extra = set(payload.keys()) - allowed
    
    if extra:
        forbidden_artifacts = [k for k in extra if any(
            bad in k.upper() for bad in [
                "FRAMEWORK", "PSYCHOLOGY", "QUICK", "START", "CORE", "PROVEN", 
                "TACTICS", "QUALITY", "CHECK", "PLAYBOOK", "METRICS"
            ]
        )]
        
        if forbidden_artifacts:
            raise ValueError(f"Rubric artifact keys detected: {forbidden_artifacts}")
        else:
            raise ValueError(f"Non-contract keys present: {sorted(extra)}")
    
    try:
        return ChaptersAdvicePayload(**payload)
    except ValidationError as e:
        # Provide clear error message for debugging
        errors = []
        for error in e.errors():
            field_path = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{field_path}: {error['msg']}")
        
        raise ValueError(f"Contract validation failed:\n" + "\n".join(errors))


def auto_repair_payload(payload: Dict[str, Any], user_prompt: str = "") -> Dict[str, Any]:
    """
    Attempt one auto-repair pass before hard-failing
    
    Args:
        payload: Malformed payload
        user_prompt: Original user request for context
        
    Returns:
        Repaired payload or original if no repairs possible
    """
    repaired = payload.copy()
    
    # Remove obvious rubric artifacts
    forbidden_keys = [k for k in repaired.keys() if any(
        bad in k.upper() for bad in [
            "FRAMEWORK", "PSYCHOLOGY", "QUICK", "START", "CORE", "PROVEN",
            "TACTICS", "QUALITY", "CHECK", "PLAYBOOK", "ANALYSIS"
        ]
    )]
    
    for key in forbidden_keys:
        print(f"🔧 Auto-repair: Removing rubric artifact key '{key}'")
        repaired.pop(key, None)
    
    # Try to extract chapters and advice from malformed structure
    if "chapters" not in repaired and any(k for k in repaired.keys() if "chapter" in k.lower()):
        # Try to find chapter-like content
        for key, value in repaired.items():
            if "chapter" in key.lower() and isinstance(value, list):
                print(f"🔧 Auto-repair: Moving '{key}' to 'chapters'")
                repaired["chapters"] = value
                repaired.pop(key, None)
                break
    
    if "advice" not in repaired and any(k for k in repaired.keys() if "advice" in k.lower() or "recommendation" in k.lower()):
        # Try to find advice-like content
        for key, value in repaired.items():
            if ("advice" in key.lower() or "recommendation" in key.lower()) and isinstance(value, list):
                print(f"🔧 Auto-repair: Moving '{key}' to 'advice'")
                repaired["advice"] = value
                repaired.pop(key, None)
                break
    
    # Set provenance if missing
    if "provenance" not in repaired:
        repaired["provenance"] = "rubric_based"  # Likely came from old system
    
    return repaired


def validate_with_repair(payload: Dict[str, Any], user_prompt: str = "") -> ChaptersAdvicePayload:
    """
    Validate payload with one auto-repair attempt
    
    Args:
        payload: Raw extraction output
        user_prompt: Original user request
        
    Returns:
        Validated payload
        
    Raises:
        ValueError: If validation fails after repair attempt
    """
    try:
        # Try direct validation first
        return enforce_contract(payload)
    except ValueError as e:
        print(f"⚠️ Contract validation failed: {e}")
        print("🔧 Attempting auto-repair...")
        
        try:
            repaired = auto_repair_payload(payload, user_prompt)
            result = enforce_contract(repaired)
            print("✅ Auto-repair successful")
            return result
        except ValueError as repair_error:
            # Provide detailed failure report
            error_msg = f"""
Contract validation failed even after auto-repair.

Original request: {user_prompt}

Expected contract:
{{
  "chapters": [
    {{"title": "Chapter Title", "summary": "40+ char summary", "start_ts": 123.4}}
  ],
  "advice": [
    {{"category": "monetization", "point": "Actionable advice 20-240 chars"}}
  ],
  "partial_segment": false,
  "provenance": "contract_based"
}}

Validation errors: {repair_error}

Received keys: {list(payload.keys())}
"""
            raise ValueError(error_msg)


class ContractMatcher:
    """Matches user requests to appropriate output contracts"""
    
    @staticmethod
    def detect_contract_type(user_prompt: str, video_title: str = "") -> str:
        """
        Detect what output contract the user is requesting
        
        Args:
            user_prompt: User's analysis request
            video_title: Video title for context
            
        Returns:
            Contract type identifier
        """
        combined = f"{user_prompt} {video_title}".lower()
        
        # Chapters + advice pattern
        if any(word in combined for word in ["chapter", "advice", "recommendations", "lessons"]):
            if "chapter" in combined and ("advice" in combined or "recommend" in combined):
                return "chapters_advice"
        
        # Timeline/summary pattern  
        if any(word in combined for word in ["timeline", "summary", "breakdown", "overview"]):
            return "timeline_summary"
            
        # Default to chapters_advice for content extraction
        return "chapters_advice"
    
    @staticmethod
    def get_contract_schema(contract_type: str) -> type:
        """Get the Pydantic model for a contract type"""
        if contract_type == "chapters_advice":
            return ChaptersAdvicePayload
        # Add other contract types as needed
        return ChaptersAdvicePayload  # Default


def create_contract_prompt(contract_type: str, user_request: str) -> str:
    """
    Create a prompt that enforces the specific output contract
    
    Args:
        contract_type: Type of contract to enforce
        user_request: Original user request
        
    Returns:
        Prompt that will generate contract-compliant output
    """
    if contract_type == "chapters_advice":
        return f"""You must extract chapters and actionable advice from this content.

USER REQUEST: {user_request}

OUTPUT REQUIREMENTS:
- You MUST return ONLY a JSON object with exactly these keys: "chapters", "advice", "partial_segment", "provenance"
- Do NOT include any other sections like "Core Frameworks", "Psychology", "Quick Start", etc.
- Each chapter must have: title (3-140 chars), summary (40-500 chars), optional start_ts (seconds)
- Each advice must have: category (from enum), point (20-240 chars actionable advice)
- Set provenance to "contract_based"

EXAMPLE OUTPUT:
{{
  "chapters": [
    {{"title": "Revenue Diversification Strategy", "summary": "Discussion of moving beyond platform-dependent income streams...", "start_ts": 123.4}},
    {{"title": "Operational Scaling Challenges", "summary": "How the creator handles team growth and management overhead...", "start_ts": 456.7}}
  ],
  "advice": [
    {{"category": "monetization", "point": "Diversify beyond platform subs - they churn daily and depend on attendance"}},
    {{"category": "ops", "point": "First hire should be an editor - pay base salary plus performance percentage"}}
  ],
  "partial_segment": false,
  "provenance": "contract_based"
}}

Extract meaningful chapters (1-4 minutes each, topic-driven boundaries) and actionable advice only."""
    
    return f"Extract insights from this content based on: {user_request}"