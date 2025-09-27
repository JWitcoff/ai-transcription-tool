# Changelog

All notable changes to the AI Transcription Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-27

### 🚨 BREAKING CHANGES
- **Output Format Changed:** Analysis output is now a two-part string format (`**SUMMARY**\n...\n\n**ANALYSIS**\n...`) instead of dictionary with separate `summary`, `themes`, and `sentiment` keys
- **Theme Extraction:** `TextAnalyzer.extract_themes()` now returns structured analysis string instead of list of theme dictionaries
- **Analysis API:** Removed `analyze_transcript()` function from `quick_url_transcribe.py` - use `TextAnalyzer.summarize()` or `CustomAnalyzer.analyze_custom()` directly

### Added
- **Narrative Summary Generation:** New coherent 3-6 sentence prose summaries with chronological/importance ordering
- **Phantom Speaker Merging:** `_merge_phantom_speakers()` function prevents false diarization (e.g., showing 6+ speakers when only 1-2 exist)
- **Entity Deduplication:** Fuzzy matching to consolidate duplicates (e.g., "Comic Con 2025" = "CommaCon 2025")
- **Fact Grounding:** All summaries must include at least 3 concrete facts (dates, metrics, names, or quotes)
- **Universal Format Enforcement:** All providers (OpenAI/local) produce identical two-part structure

### Changed
- **analyzer.py:**
  - `summarize()` now generates narrative prose + structured analysis
  - Added `_generate_narrative_summary()`, `_generate_structured_analysis()`, `_deduplicate_entities()` methods
  - `extract_themes()` returns structured categories string instead of dictionary list

- **custom_analyzer.py:**
  - Updated OpenAI prompts to enforce two-part format
  - Modified local analysis fallback to match new format
  - Added explicit deduplication instructions to prompts

- **quick_url_transcribe.py:**
  - Replaced 3 separate analysis calls with single unified call
  - Added phantom speaker post-processing before analysis
  - Updated `save_results()` to handle new string format

### Fixed
- **Type Errors:** Resolved "'str' object has no attribute 'get'" errors throughout analysis pipeline
- **Phantom Speakers:** Fixed diarization creating 6+ false speakers in single-speaker content
- **Entity Duplication:** Prevented multiple variations of same entity appearing in analysis
- **Hallucinations:** Removed "Missing Information" and speculative content from outputs

### Migration Guide

#### Old Format (v1.x)
```python
analysis = {
    'summary': 'Bullet points...',
    'themes': [
        {'title': 'Theme 1', 'description': '...'},
        {'title': 'Theme 2', 'description': '...'}
    ],
    'sentiment': {'label': 'POSITIVE', 'score': 0.8}
}
```

#### New Format (v2.0)
```
**SUMMARY**
Comma hosted a livestream teasing "Something Tiny," an announcement of an announcement. They confirmed CommaCon 2025 on Nov 8 in San Diego, with tickets selling fast. OpenPilot's experimental mode showed its first engagement uptick in four years.

**ANALYSIS**
- Events: CommaCon 2025, "Something Tiny" teaser
- Metrics: Engagement uptick (first in 4 years), ~500 units/week
- Production: SMT expansion, camera focus room
- Community: 200–350 live viewers, Q&A participation
```

### Impact
**Users now get concise, fact-grounded recaps with accurate speaker attribution — eliminating hallucinations, duplicate entities, and phantom diarization.**

## [1.x] - Previous Versions

See git history for changes before 2025-09-27.