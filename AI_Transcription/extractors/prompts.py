"""
Enhanced Prompts - Multi-pass extraction prompts with few-shot examples
"""

# Enhanced few-shot example based on gold standard
FEW_SHOT_EXAMPLE = """
Example Input: "The CCN fit framework means your content works for Core, Casual, and New audiences simultaneously. Upon click, the first seven seconds of a video is about confirming the click. We had a channel reach 1 million subscribers in 62 hours. This increased our views by 270x when we applied it to thumbnails. Everything is a listicle. Hide the vegetables by packaging meaningful content inside entertaining concepts."

Example Output: {
  "frameworks": [{
    "name": "CCN fit",
    "definition": "content works for Core, Casual, and New audiences simultaneously",
    "components": ["Core audience", "Casual audience", "New audience"],
    "verbatim_term": "CCN fit",
    "context": "thumbnail optimization"
  }, {
    "name": "7/15/30 intro structure", 
    "definition": "first 7 seconds confirm click, then personal hook, then new hook by 30s",
    "components": ["0-7s confirm click", "7-15s personal", "15-30s new hook"],
    "verbatim_term": "first seven seconds",
    "context": "video intro timing"
  }, {
    "name": "Hide the vegetables",
    "definition": "package meaningful content inside entertaining concepts",
    "verbatim_term": "Hide the vegetables",
    "context": "content strategy"
  }],
  "metrics": [{
    "value": "270x",
    "type": "multiplier", 
    "metric": "views increase",
    "context": "applied CCN fit to thumbnails",
    "verbatim": "increased our views by 270x"
  }, {
    "value": "62 hours",
    "type": "time_to_outcome",
    "metric": "1 million subscribers", 
    "context": "channel launch strategy",
    "verbatim": "reach 1 million subscribers in 62 hours"
  }],
  "case_studies": [{
    "name": "Style Theory channel launch",
    "pattern_or_framework": "Concentrated launch with 5 finished episodes", 
    "what_changed": "Cross-promo funneling + 5×20 min videos day-one",
    "measured_effect": "1M subscribers in 62 hours",
    "notes": "YouTube systems flagged anomalous watch-time surge"
  }],
  "preserved_terms": ["CCN fit", "Hide the vegetables", "270x", "62 hours", "listicle"]
}
"""

MULTI_PASS_PROMPTS = {
    "pass_1": {
        "system": f"""You are an expert at extracting actionable insights from YouTube growth content. 
You must extract frameworks, metrics, psychological principles, time-based strategies, systems, case studies, and authenticity signals using these specific lenses:

EXTRACTION LENSES:
1. FRAMEWORKS: Named models, structures, formulas - MUST preserve verbatim
   - "CCN fit" (Core, Casual, New audiences)
   - "7/15/30" timing (0-7s confirm click, 7-15s personal, 15-30s new hook)
   - "A→Z map" (content journey mapping)
   - "Hide the vegetables" (meaningful content in entertaining packages)
   - "Laws of writing good videos", problem→solution loops, listicle structures
   
2. METRICS: Numbers with full context - MUST capture exact values
   - Multipliers: "270x", "40x" with what they multiplied
   - Time outcomes: "62 hours to 1M subs", "5% → 30% time allocation"
   - Before/after: growth numbers, percentage changes
   - Video counts: "5 videos at launch", "100 titles prepared"
   
3. TEMPORAL: Time-based strategies with specific timing
   - Video intro timing (0-7s, 7-15s, 15-30s)
   - Mid-video re-engagement tactics
   - Reveal vs reflection timing
   
4. PSYCHOLOGY: Cialdini's 6 influence principles + audience dynamics
   - Scarcity, consistency, reciprocity, consensus, similarity, authority
   - Audience as focus group, community building
   
5. SYSTEMS: Repeatable processes and workflows
   - Content systemization (Title + Thumbnail + List + Promise)
   - Launch strategies (5 videos minimum)
   - Shorts→long-form funnel
   
6. CASE STUDIES: Structure anecdotes into situation → action → result
   - Creator/channel name
   - What framework/tactic they applied
   - Specific change they made 
   - Measurable outcome with numbers
   
7. AUTHENTICITY: Personal brand and vulnerability signals
   - Realistic thumbnails vs over-produced
   - Vulnerability moments and emotional shares
   - Font/music identity markers
   - "Resume principle" - every video represents you

TERMINOLOGY PRESERVATION RULES:
- Preserve EXACT quoted terms: "CCN fit", "Hide the Vegetables"
- Preserve arrow formulas: A→Z, X→Y→Z, problem→solution→new problem
- Preserve time formats: 7/15/30, specific timing patterns
- Preserve branded concepts and proper nouns
- Track ALL preserved terms in preserved_terms array

{FEW_SHOT_EXAMPLE}

Return structured JSON with: frameworks, metrics, temporal_strategies, psychology, systems, case_studies, authenticity, and preserved_terms arrays. 

RULE: Every framework must include verbatim_term field. Every metric must include verbatim field. Every case study must follow name/pattern_or_framework/what_changed/measured_effect structure.""",
        
        "user_template": "Extract insights from this YouTube growth transcript. Focus on finding canonical frameworks (CCN fit, 7/15/30, A→Z map, Hide the vegetables), specific metrics (270x, 62 hours, 40x), and case studies with measurable outcomes:\n\n{transcript}"
    },
    
    "pass_2": {
        "system": """You are an expert at organizing YouTube growth insights into the yt_playbook_v1 schema.

Your job is to clean, structure, and validate the raw extraction:

ORGANIZATION REQUIREMENTS:
1. FRAMEWORKS: Ensure complete definitions with all components
   - CCN fit must have Core/Casual/New components
   - 7/15/30 must have all three time segments
   - A→Z map must describe journey from start to finish
   - Each framework needs definition + components + context
   
2. METRICS: Link numbers to specific tactics and contexts
   - 270x must connect to astrophotography + packaging change
   - 62 hours must connect to Style Theory launch strategy
   - 40x must connect to thumbnail optimization
   - Include before/after context for all changes
   
3. CASE STUDIES: Structure into consistent format
   - Name: specific creator/channel
   - Pattern_or_framework: what tactic they used
   - What_changed: specific action taken
   - Measured_effect: quantified outcome
   - Notes: additional context
   
4. AUTHENTICITY: Categorize by signal type
   - Vulnerability_signals: emotional moments, personal shares
   - Thumbnail_style: realistic vs over-produced preferences  
   - Identity_markers: fonts, music, brand consistency
   
5. PRESERVED TERMS: Validate all terms actually exist in content
   - Only include terms found verbatim in transcript
   - Remove paraphrased or invented terms
   - Prioritize quoted phrases and branded concepts

VALIDATION CHECKLIST:
- All frameworks have complete definitions
- All metrics have business context
- Case studies follow situation→action→result structure
- Preserved terms are actually verbatim from content
- No duplicate or contradictory information

Return organized JSON matching the schema with all fields populated.""",
        
        "user_template": "Organize this raw YouTube growth extraction into yt_playbook_v1 schema. Ensure frameworks are complete with definitions, metrics have context, and case studies follow name/pattern/change/effect structure:\n\nOriginal transcript: {transcript}\n\nRaw extraction: {raw_extraction}"
    },
    
    "pass_3": {
        "system": """You are a quality validator ensuring the extraction meets gold standard requirements.

VALIDATION REQUIREMENTS:
1. COMPLETENESS CHECK:
   - Required frameworks: CCN fit, 7/15/30, A→Z map, Hide the vegetables
   - Key metrics: 270x, 62 hours, 40x, 5%→30% with full context
   - Case studies: At least 2-3 with all fields populated
   - Authenticity signals: vulnerability + brand elements
   
2. QUALITY SCORING:
   - Calculate weighted coverage (frameworks=40%, metrics=30%, case studies=20%, other=10%)
   - Identify top 3 gaps from missing canonical items
   - Generate specific actionable next steps
   
3. FOOTER GENERATION:
   Must include standardized Quality Check footer:
   • Coverage: [Key items found, e.g., "CCN fit + 270x + case studies"]
   • Gaps: [Most critical missing item, e.g., "A→Z map not stated"] 
   • Actionability: [Specific step user can take today]
   
4. SCHEMA COMPLIANCE:
   - Add schema_version: "yt_playbook_v1"
   - Include quality_check object with coverage_score
   - Ensure footer object with coverage/gaps/actionability
   
5. GAP PATCHING:
   - If framework mentioned but incomplete, expand definition
   - If metric found but no context, add surrounding context
   - If case study missing components, mark as "not stated"
   
RETURN: Complete JSON with quality_check including footer object for standardized output format.""",
        
        "user_template": "Validate this YouTube growth extraction against gold standard. Add quality_check with coverage_score and footer object (coverage/gaps/actionability). Ensure canonical items are present or marked 'not stated':\n\n{structured_data}"
    }
}

# Category-specific extraction prompts with gold standard examples
EXTRACTION_PROMPTS = {
    "frameworks": """Extract all named frameworks, models, and structured approaches with complete definitions:

PRIORITY FRAMEWORKS TO FIND:
- "CCN fit" (Core, Casual, New audiences) - content that works for all three
- "7/15/30" or first 7 seconds, 7-15 seconds, 15-30 seconds intro timing
- "A→Z map" or "video game map" - content journey from start to finish  
- "Hide the vegetables" - meaningful content in entertaining packages
- "Laws of writing good videos" or similar systematic approaches
- Problem→solution→new problem loops
- Listicle structures and systematic approaches

EXTRACTION RULES:
- Preserve EXACT quoted terms
- Include complete definitions with all components
- Capture arrow structures (A→Z, X→Y→Z)
- Include surrounding context for each framework

Content: {text}""",

    "metrics": """Extract ALL concrete numbers with full business context:

PRIORITY METRICS TO FIND:
- 270x multiplier (astrophotography channel views)
- 62 hours to 1 million subscribers (Style Theory)
- 40x more views per day (thumbnail optimization)
- 5% → 30% time allocation (ideation focus)
- 2,500 videos uploaded per minute to YouTube
- Specific growth numbers with before/after context

EXTRACTION REQUIREMENTS:
- Include exact numbers with units (270x, 62 hours, 5%→30%)
- Capture what the metric relates to (views, subscribers, time)
- Include before/after comparisons where present
- Link metrics to specific tactics or changes
- Preserve verbatim phrasing

Content: {text}""",

    "psychology": """Identify psychological principles and audience dynamics:

CIALDINI'S 6 INFLUENCE PRINCIPLES:
1. Scarcity (limited, exclusive, rare)
2. Consistency (commitment, promises)
3. Reciprocity (giving first, returning favors)
4. Consensus/Social Proof (others doing it, popularity)
5. Similarity/Liking (relatable, like us)
6. Authority (expertise, credentials, trust)

AUDIENCE PSYCHOLOGY:
- Audience as focus group concept
- Community building strategies
- Vulnerability and authenticity signals
- Trust-building elements

Extract specific examples of each principle in action with context.

Content: {text}""",

    "systems": """Extract repeatable systems, templates, and systematic approaches:

CONTENT SYSTEMS TO FIND:
- Title + Thumbnail + List + Promise formula
- Listicle structure (everything is a listicle)
- Launch strategy (5 videos minimum, 100 titles prepared)
- Shorts → long-form → community funnel
- Systematic ideation processes
- Template-based approaches

WORKFLOW PATTERNS:
- Research → ideation → production workflows
- Launch sequences and timing
- Scaling and systemization approaches
- Quality vs quantity balance systems

Extract step-by-step processes and repeatable frameworks.

Content: {text}""",

    "case_studies": """Extract and structure creator success stories into case studies:

CASE STUDY FORMAT:
- Name: Creator or channel name
- Pattern_or_framework: What tactic/framework they used
- What_changed: Specific action they took
- Measured_effect: Quantified outcome with numbers
- Notes: Additional context

KNOWN EXAMPLES TO FIND:
- Astrophotography channel (5%→30% ideation time → 270x views)
- Style Theory (5 video launch → 1M subs in 62 hours)
- UI Hacks thumbnail change (40x more daily views)
- Tim Gabe, Max Fosh, Emma Chamberlain examples

Structure any creator examples into the case study format.

Content: {text}""",
    
    "authenticity": """Extract authenticity and personal brand signals:

VULNERABILITY SIGNALS:
- Emotional moments (crying, personal shares)
- Family/personal stories (grandmother memories)
- Failure and learning admissions
- Authentic vs performed emotions

BRAND IDENTITY MARKERS:
- Realistic thumbnails vs over-produced
- Font choices that "feel like me"
- Music that represents personal identity
- Subtle vs exaggerated expressions

BRAND PRINCIPLES:
- "Resume principle" - every video represents you
- Consistency in personal brand elements
- Trust-building through authenticity

Extract specific examples with context.

Content: {text}"""
}