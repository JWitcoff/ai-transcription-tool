#!/usr/bin/env python3
"""
Test script for improved analysis system
Tests the fact-grounded analysis to prevent hallucinations
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyzer import TextAnalyzer
from custom_analyzer import CustomAnalyzer
from fact_extractor import FactExtractor, extract_grounded_summary

def test_with_sample_transcript():
    """Test with a sample transcript that could trigger hallucinations"""

    # Sample transcript that could cause issues in the original system
    sample_transcript = """
    Welcome to our channel! Today we're going to talk about the latest tech announcements.

    Recently, Apple made some interesting announcements at WWDC 2024. They revealed new features
    for iOS 18 and introduced Apple Intelligence. The event took place in June 2024.

    Google also had their I/O conference this year where they announced new AI features.
    Microsoft has been working on integrating AI into Office 365.

    Some key metrics from the tech industry: Apple's revenue reached $383 billion last year.
    Google's parent company Alphabet reported 15% growth in cloud revenue.

    As one industry expert said, "The AI revolution is just beginning, and we're seeing
    unprecedented innovation across all major tech companies."

    The competition between these companies is driving rapid innovation. What does this mean
    for consumers? We'll see more AI-powered features in everyday apps.
    """

    print("🧪 TESTING IMPROVED ANALYSIS SYSTEM")
    print("=" * 60)
    print(f"Testing with {len(sample_transcript.split())} word transcript")
    print("=" * 60)

    # Test 1: Fact extraction
    print("\n📊 TEST 1: FACT EXTRACTION")
    print("-" * 40)

    fact_extractor = FactExtractor()
    fact_analysis = fact_extractor.extract_all_facts(sample_transcript)

    print(f"✅ Facts extracted: {fact_analysis['validation_summary']['total_facts_extracted']}")
    print(f"✅ Confidence score: {fact_analysis['confidence_score']:.2f}")
    print(f"✅ Theme count: {len(fact_analysis['themes'])}")

    # Show extracted facts
    for category, facts in fact_analysis['facts'].items():
        if facts and category != 'quotes':
            print(f"\n{category.upper().replace('_', ' ')}:")
            for fact in facts[:3]:  # Show first 3
                print(f"  • {fact.content} (confidence: {fact.confidence:.2f})")
        elif category == 'quotes' and facts:
            print(f"\nQUOTES:")
            for quote in facts[:2]:
                print(f"  • \"{quote.text}\"")

    # Show themes
    print(f"\nFACT-BASED THEMES:")
    for i, theme in enumerate(fact_analysis['themes'], 1):
        print(f"  {i}. {theme['title']}")
        print(f"     {theme['description'][:100]}...")

    # Test 2: Extractive summarization
    print("\n📝 TEST 2: EXTRACTIVE SUMMARIZATION")
    print("-" * 40)

    extractive_summary = extract_grounded_summary(sample_transcript, max_sentences=3)
    print("EXTRACTIVE SUMMARY (no hallucination risk):")
    print(extractive_summary)

    # Test 3: Improved TextAnalyzer
    print("\n🔍 TEST 3: IMPROVED TEXT ANALYZER")
    print("-" * 40)

    analyzer = TextAnalyzer()

    # Test extractive summarization
    summary = analyzer.summarize(sample_transcript, max_length=150)
    print("ANALYZER SUMMARY:")
    print(summary)

    # Test improved themes
    themes = analyzer.extract_themes(sample_transcript, num_themes=4)
    print(f"\nIMPROVED THEMES ({len(themes)} found):")
    for i, theme in enumerate(themes, 1):
        print(f"{i}. {theme['title']}")
        print(f"   {theme['description'][:100]}...")
        if 'evidence_count' in theme:
            print(f"   Evidence: {theme['evidence_count']} references")

    # Test 4: Custom analyzer with fact grounding
    print("\n🤖 TEST 4: FACT-GROUNDED CUSTOM ANALYZER")
    print("-" * 40)

    custom_analyzer = CustomAnalyzer()

    # Test with a prompt that could cause hallucinations
    test_prompts = [
        "What new Apple products were announced?",
        "List all the specific metrics and numbers mentioned",
        "Extract the key quotes and who said them"
    ]

    for prompt in test_prompts:
        print(f"\n📝 PROMPT: {prompt}")
        result = custom_analyzer.analyze_custom(sample_transcript, prompt, "Tech News Video")

        if result['success']:
            print(f"PROVIDER: {result['provider']}")
            if 'confidence_score' in result:
                print(f"CONFIDENCE: {result['confidence_score']:.2f}")
            print("ANALYSIS:")
            print(result['analysis'][:300] + "..." if len(result['analysis']) > 300 else result['analysis'])
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("🎉 TESTING COMPLETED")
    print("Key improvements:")
    print("✅ Extractive summarization prevents hallucinations")
    print("✅ Fact-based theme generation with evidence counts")
    print("✅ Named entity recognition and validation")
    print("✅ Blacklist filtering for joke terms")
    print("✅ Source attribution and confidence scoring")
    print("=" * 60)

def test_blacklist_filtering():
    """Test the blacklist filtering specifically"""
    print("\n🛡️  TESTING BLACKLIST FILTERING")
    print("-" * 40)

    # Transcript with joke terms that should be filtered
    problematic_transcript = """
    Apple just announced the iPhone 17 at their latest event.
    They also revealed the Vision Pro 2 with amazing new features.
    Tesla is working on a Tesla Phone to compete with smartphones.
    ChatGPT 10 will be released next year according to rumors.
    """

    fact_extractor = FactExtractor()
    fact_analysis = fact_extractor.extract_all_facts(problematic_transcript)

    print("TESTING JOKE TERM FILTERING:")
    print(f"Raw transcript mentions: iPhone 17, Vision Pro 2, Tesla Phone, ChatGPT 10")

    # Check if these terms were filtered out
    all_facts = []
    for category, facts in fact_analysis['facts'].items():
        if category != 'quotes':
            all_facts.extend([f.content for f in facts])

    joke_terms_found = []
    for fact in all_facts:
        fact_lower = fact.lower()
        if any(joke in fact_lower for joke in ['iphone 17', 'vision pro 2', 'tesla phone', 'chatgpt 10']):
            joke_terms_found.append(fact)

    if joke_terms_found:
        print(f"❌ FAILED: Found blacklisted terms: {joke_terms_found}")
    else:
        print("✅ SUCCESS: All joke terms filtered out")

    print(f"Total facts extracted: {len(all_facts)}")
    print(f"Valid facts found: {all_facts}")

if __name__ == "__main__":
    test_with_sample_transcript()
    test_blacklist_filtering()