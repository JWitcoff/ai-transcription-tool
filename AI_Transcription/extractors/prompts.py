"""
Enhanced Prompts - Multi-pass extraction prompts with few-shot examples
"""

# Few-shot example for consistent extraction
FEW_SHOT_EXAMPLE = """
Example Input: "The CCN fit framework means your content works for Core, Casual, and New audiences simultaneously. This increased our views by 270x when we applied it to thumbnails."

Example Output: {
  "frameworks": [{
    "name": "CCN fit",
    "definition": "content works for Core, Casual, and New audiences simultaneously",
    "components": ["Core audience", "Casual audience", "New audience"],
    "verbatim_term": "CCN fit",
    "context": "thumbnail optimization"
  }],
  "metrics": [{
    "value": "270x",
    "type": "multiplier", 
    "metric": "views increase",
    "context": "applied CCN fit to thumbnails",
    "verbatim": "increased our views by 270x"
  }],
  "preserved_terms": ["CCN fit", "270x"]
}
"""

MULTI_PASS_PROMPTS = {
    "pass_1": {
        "system": f"""You are an expert at extracting actionable insights from content transcripts. 
Extract frameworks, metrics, psychological principles, time-based strategies, and systems using these specific lenses:

EXTRACTION LENSES:
1. FRAMEWORKS: Named models, structures, formulas (e.g., "CCN fit", "A→Z map", "7/15/30", "problem→solution loops", "Laws of X")
2. METRICS: Numbers with context (multipliers like "270x", percentages like "5%→30%", counts, timeframes, before/after)
3. TEMPORAL: Time-based strategies (0-7s, 7-15s, 15-30s tactics, mid-video hooks, reveal timing)
4. PSYCHOLOGY: Persuasion principles (scarcity, consistency, reciprocity, consensus, similarity, authority), audience dynamics
5. SYSTEMS: Repeatable processes, templates, workflows, funnel strategies (shorts→long→community)
6. AUTHENTICITY: Brand signals, vulnerability, personal elements, "resume principle"

TERMINOLOGY RULES:
- Preserve EXACT terms in quotes: "CCN fit", "Hide the Vegetables"
- Preserve formulas and arrows: A→Z, X→Y→Z, 7/15/30
- Keep proper nouns and branded concepts verbatim
- Track all preserved terms in output

{FEW_SHOT_EXAMPLE}

Return structured JSON with frameworks, metrics, temporal_strategies, psychology, systems, authenticity, and preserved_terms arrays.""",
        
        "user_template": "Extract insights from this transcript:\n\n{transcript}"
    },
    
    "pass_2": {
        "system": """You are an expert at organizing extracted insights into a structured schema.

Given raw extraction data, organize it into the yt_playbook_v1 schema format:
- Ensure all components are properly categorized
- Add missing context or definitions where possible
- Validate that preserved terms are actually present in original content
- Check completeness of multi-component frameworks

Maintain all original verbatim terms and add context where helpful.""",
        
        "user_template": "Organize this raw extraction data:\n\nOriginal transcript: {transcript}\n\nRaw extraction: {raw_extraction}"
    },
    
    "pass_3": {
        "system": """You are a quality validator for content extraction.

Review the organized extraction and:
1. Add missing quality_check section with coverage assessment
2. Identify gaps in extraction (missing frameworks, metrics, etc.)
3. Suggest 1-3 actionable next steps
4. Ensure schema_version is present
5. Patch any obvious gaps if possible

Focus on completeness and actionability.""",
        
        "user_template": "Validate and add quality check to this extraction:\n\n{structured_data}"
    }
}

EXTRACTION_PROMPTS = {
    "frameworks": """Extract all named frameworks, models, and structured approaches from this content:
- Look for quoted terms, proper nouns, and branded concepts
- Identify X→Y→Z patterns and numbered structures
- Capture "Laws of X", "X Principle", "X Framework" patterns
- Preserve exact terminology

Content: {text}""",

    "metrics": """Extract all concrete numbers, percentages, and measurable outcomes:
- Multipliers (270x, 40x increase)
- Percentage changes (5%→30%)
- Before/after comparisons
- Time-to-outcome metrics
- Growth numbers with context

Content: {text}""",

    "psychology": """Identify psychological principles and audience dynamics:
- Cialdini's 6 influence principles (scarcity, consistency, reciprocity, consensus, similarity, authority)
- Audience behavior patterns
- Persuasion tactics
- Community building strategies

Content: {text}""",

    "systems": """Extract repeatable systems and templates:
- Content creation workflows
- Systematic approaches
- Template structures
- Funnel strategies (acquisition→retention→loyalty)
- Scalable processes

Content: {text}"""
}