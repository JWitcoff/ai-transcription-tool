"""
Prompting-specific extraction prompts for Claude Code content analysis
"""

# Schema-compliant few-shot example based on the ideal results
PROMPTING_FEW_SHOT_EXAMPLE = """
Example Input: "Set the scene up front: define role, task, domain, tone. Put constants in the system prompt. Use delimiters like XML to label sections. Specify an ordered reasoning plan: analyze the form first, then the sketch. Give few-shot examples for tricky edge cases. Add hallucination guardrails: answer only if confident; cite the evidence. Define the output contract: JSON schema; prefill the first tokens. Tune runtime params: temperature=0, sufficient max tokens."

Example Output: {
  "schema_version": "prompting_claude_v1",
  "meta": {"source": "transcript", "confidence": 0.95},
  "prompting_thesis": "Structured prompting with clear contracts and safety guardrails prevents hallucination and ensures reliable AI output",
  "structure": {
    "role": "You are an LLM assistant embedded in a backend service. Your job: analyze car accident forms (domain: Swedish insurance).",
    "tone": "Be factual, concise, and confident. If evidence is insufficient, say so.",
    "constants": ["Swedish car accident form schema", "17 rows with specific meanings", "Two columns: Vehicle A (left), Vehicle B (right)"],
    "delimiters": ["XML", "Markdown"],
    "inputs": ["FORM image", "SKETCH image", "metadata"],
    "ordered_steps": [
      "1. Read the structured constants in <CONSTANTS>",
      "2. Parse the form FIRST: list detected marks per row",
      "3. THEN analyze the sketch and reconcile with form findings",
      "4. Make determinations only when evidence is explicit"
    ],
    "examples_fewshot": ["Row 3 checked for B + right turn arrow = B at fault"],
    "guardrails": [
      "Do not invent facts not visible in inputs", 
      "Only assert fault when ≥1 explicit evidence present",
      "Otherwise return 'insufficient_evidence'"
    ],
    "output_schema": "{\"fault\": \"A|B|both|neither|insufficient_evidence\", \"evidence\": [\"row_3_B_checked\"]}",
    "prefill": "Begin your response with: {",
    "runtime_params": {"temperature": 0, "max_tokens": 1500, "stop_sequences": []},
    "caching_notes": "Constants section safe to cache - form schema never changes"
  },
  "antipatterns": ["Vague role definition", "No confidence thresholds", "Missing prefill constraint"],
  "template": "Battle-tested prompt template with ROLE, TONE, CONSTANTS, GUARDRAILS, and OUTPUT_FORMAT sections",
  "checklist": [
    "Role and domain clearly defined",
    "Constants placed in system prompt for caching", 
    "Ordered reasoning plan specified",
    "Few-shot examples included",
    "Confidence guardrails present",
    "JSON schema with prefill defined",
    "Temperature=0 for determinism"
  ]
}
"""

PROMPTING_EXTRACTION_PROMPTS = {
    "system_prompt": f"""You are an expert at extracting prompt engineering patterns and best practices from educational content.

Extract structured prompting lessons using the prompting_claude_v1 schema:

EXTRACTION PRIORITIES:
1. ROLE & TASK: How to define the AI's role, job, and domain context
2. TONE & STYLE: Instructions for factual, confident, appropriate communication  
3. CONSTANTS: Background data, schemas, invariants to place in system prompt
4. STRUCTURE: XML tags, markdown, delimiters for organization
5. ORDERED STEPS: Sequential reasoning plans ("analyze X first, then Y")
6. EXAMPLES: Few-shot demonstrations for edge cases and tricky scenarios
7. GUARDRAILS: Confidence thresholds, evidence requirements, hallucination prevention
8. OUTPUT CONTRACT: JSON schemas, structured formats, prefill tokens
9. PARAMETERS: Temperature=0, max_tokens, stop sequences for determinism
10. CACHING: Notes on what's safe to cache (invariant content)

TERMINOLOGY PRESERVATION:
- Preserve exact quoted phrases: "system prompt", "prefill tokens", "temperature=0"
- Preserve technical terms: XML, JSON Schema, few-shot, guardrails
- Preserve structural patterns: ROLE/TONE/CONSTANTS/GUARDRAILS sections
- Track all preserved terms for validation

{PROMPTING_FEW_SHOT_EXAMPLE}

SCHEMA REQUIREMENTS:
- Must include schema_version: "prompting_claude_v1"
- All 10 core structure fields required (role through caching_notes)
- Template must be actionable and usable
- Checklist must be specific and implementable
- Evidence citations required for all examples

Extract lessons that follow this exact JSON structure with no extra prose.""",

    "user_template": """Extract prompt engineering lessons from this educational content. Focus on actionable patterns for building reliable prompts with proper structure, guardrails, and output contracts.

Content: {transcript}

Video context: {video_title}
User focus: {user_prompt}

Return structured JSON following prompting_claude_v1 schema with:
- Core prompting structure (role, tone, constants, delimiters, steps, examples, guardrails, schema, prefill, params, caching)  
- Actionable template
- Specific implementation checklist
- No prose outside the JSON structure""",

    "validation_prompt": """Validate this prompting extraction against the prompting_claude_v1 schema requirements:

VALIDATION CHECKLIST:
1. Schema compliance: All required fields present
2. JSON validity: No syntax errors or prose leaks
3. Actionable content: Template can be used directly
4. Evidence citations: Examples reference specific transcript content
5. Completeness: 10 core structure elements covered
6. Safety: Guardrails and confidence thresholds included

HARD REQUIREMENTS:
- schema_version: "prompting_claude_v1"
- All structure fields: role, tone, constants, delimiters, ordered_steps, examples_fewshot, guardrails, output_schema, prefill, runtime_params
- Valid JSON throughout
- No prose outside schema
- Specific evidence citations

Return validation results with coverage score and missing elements list.

Extraction to validate: {extraction_data}"""
}

# Content-specific extraction patterns
PROMPTING_PATTERNS = {
    "role_definition": [
        r"you are (?:an?|the)?\s*([^.]+)",
        r"your (?:job|task|role):\s*([^.]+)", 
        r"(?:role|persona):\s*([^.]+)",
        r"embedded (?:in|as)\s+([^.]+)"
    ],
    
    "tone_guidance": [
        r"be\s+(factual|confident|concise|professional|clear)(?:\s+and\s+(\w+))?",
        r"tone:\s*([^.]+)",
        r"style:\s*([^.]+)",
        r"if\s+(?:evidence\s+is\s+)?insufficient,?\s+(say\s+so|indicate|mention)"
    ],
    
    "constants_indicators": [
        r"(?:put|place)\s+(?:constants|invariants|background)\s+in\s+(?:the\s+)?system\s+prompt",
        r"(?:constants|background|schema|form\s+structure):\s*([^.]+)",
        r"safe\s+to\s+cache",
        r"never\s+change[ds]?"
    ],
    
    "delimiter_usage": [
        r"XML\s+tags?",
        r"<[a-zA-Z_][^>]*>",
        r"markdown",
        r"delimiters?",
        r"label\s+sections",
        r"wrap\s+in\s+tags"
    ],
    
    "ordered_reasoning": [
        r"(?:analyze|parse|read)\s+(?:the\s+)?(\w+)\s+(?:first|FIRST)",
        r"then\s+(?:analyze|parse|read)\s+(?:the\s+)?(\w+)",
        r"step\s*\d+[:.]\s*([^.]+)",
        r"(?:first|1st|1\.|step\s+1)[:.]\s*([^.]+)"
    ],
    
    "few_shot_examples": [
        r"few[-\s]*shot\s+examples?",
        r"example\s+(?:input|output)",
        r"demonstration",
        r"sample\s+(?:case|input)",
        r"edge\s+cases?"
    ],
    
    "guardrails_safety": [
        r"(?:only|answer\s+only)\s+if\s+confident",
        r"confidence\s+threshold",
        r"(?:cite|include)\s+(?:the\s+)?evidence",
        r"do\s+not\s+invent\s+facts",
        r"hallucination\s+(?:prevention|guardrails?)",
        r"insufficient[_\s]evidence"
    ],
    
    "output_schema": [
        r"JSON\s+schema",
        r"output\s+(?:contract|format)",
        r"structured\s+(?:format|output)",
        r"\{[^}]*\}",
        r"response\s+format"
    ],
    
    "prefill_tokens": [
        r"prefill",
        r"begin\s+(?:your\s+)?response\s+with",
        r"start\s+with",
        r"first\s+tokens?",
        r"response\s+must\s+start"
    ],
    
    "runtime_params": [
        r"temperature\s*=\s*0",
        r"max[_\s]tokens",
        r"determinism",
        r"stop\s+sequences?",
        r"parameters?"
    ],
    
    "caching_notes": [
        r"(?:prompt\s+)?caching",
        r"safe\s+to\s+cache",
        r"invariant\s+(?:content|data)",
        r"never\s+change[ds]?",
        r"static\s+(?:content|data)"
    ]
}

# Validation patterns for quality checking
QUALITY_PATTERNS = {
    "json_schema_present": r'"schema_version":\s*"prompting_claude_v1"',
    "no_prose_leak": r'^[\s]*\{.*\}[\s]*$',  # Only JSON, no extra prose
    "has_prefill": r'"prefill":\s*"[^"]+"',
    "has_temperature": r'"temperature":\s*0',
    "has_guardrails": r'"guardrails":\s*\[',
    "evidence_citations": r'(?:row\s+\d+|form|sketch|transcript|video)',
    "actionable_steps": r'"ordered_steps":\s*\[.*"[^"]*(?:analyze|parse|read|then)[^"]*"'
}

def extract_prompting_concepts(text: str) -> dict:
    """Extract prompting concepts using pattern matching"""
    import re
    
    concepts = {}
    
    for concept_type, patterns in PROMPTING_PATTERNS.items():
        matches = []
        for pattern in patterns:
            found = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in found:
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].strip()
                
                matches.append({
                    "match": match.group(0),
                    "context": context,
                    "groups": match.groups() if match.groups() else []
                })
        
        concepts[concept_type] = matches
    
    return concepts


def validate_prompting_extraction(extraction: dict) -> dict:
    """Validate extraction against prompting schema requirements"""
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "coverage_score": 0.0,
        "missing_required": [],
        "quality_checks": {}
    }
    
    required_fields = [
        "schema_version", "structure.role", "structure.tone", "structure.constants",
        "structure.delimiters", "structure.ordered_steps", "structure.examples_fewshot",
        "structure.guardrails", "structure.output_schema", "structure.prefill", 
        "structure.runtime_params"
    ]
    
    # Check required fields
    missing = []
    for field in required_fields:
        if '.' in field:
            parts = field.split('.')
            current = extraction
            try:
                for part in parts:
                    current = current[part]
            except (KeyError, TypeError):
                missing.append(field)
        else:
            if field not in extraction:
                missing.append(field)
    
    validation_results["missing_required"] = missing
    
    # Calculate coverage
    coverage = (len(required_fields) - len(missing)) / len(required_fields)
    validation_results["coverage_score"] = coverage
    
    # Schema version check
    if extraction.get("schema_version") != "prompting_claude_v1":
        validation_results["errors"].append("Invalid schema_version")
        validation_results["valid"] = False
    
    # Quality pattern checks
    import json
    try:
        json_str = json.dumps(extraction)
        for pattern_name, pattern in QUALITY_PATTERNS.items():
            import re
            match = re.search(pattern, json_str, re.MULTILINE | re.DOTALL)
            validation_results["quality_checks"][pattern_name] = bool(match)
    except Exception as e:
        validation_results["errors"].append(f"JSON serialization error: {e}")
        validation_results["valid"] = False
    
    return validation_results