"""
Custom Analyzer - User-directed analysis based on specific prompts
Enhanced with deep extraction pipeline for frameworks, metrics, and psychology
"""

import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from fact_extractor import FactExtractor, extract_grounded_summary

# Load environment variables
load_dotenv()

class CustomAnalyzer:
    """Performs custom analysis with enhanced deep extraction capabilities"""
    
    def __init__(self, use_deep_extraction: bool = False):  # Disabled by default due to quality issues
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        self.use_deep_extraction = use_deep_extraction
        self.deep_extractor = None
        self.validator = None
        self.fact_extractor = FactExtractor()  # For fact validation and grounding
        self.use_factual_grounding = True  # Enable fact-based analysis
        
        # Initialize deep extraction components
        if self.use_deep_extraction:
            try:
                from extractors import DeepExtractor, SchemaValidator
                self.deep_extractor = DeepExtractor()
                self.validator = SchemaValidator()
                print("✅ Custom analyzer ready with deep extraction pipeline")
            except ImportError as e:
                print(f"⚠️  Deep extraction not available: {e}")
                self.use_deep_extraction = False
        
        # Fallback to basic OpenAI/local analysis
        if self.api_key and self.api_key != 'your_openai_api_key_here':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                if not self.use_deep_extraction:
                    print("✅ Custom analyzer ready with OpenAI GPT")
            except ImportError:
                print("⚠️  OpenAI package not installed. Using local fallback.")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}")
        else:
            if not self.use_deep_extraction:
                print("ℹ️  No OpenAI API key. Using local analysis.")
    
    def analyze_custom(self, transcript: str, user_prompt: str, video_title: str = "") -> Dict[str, Any]:
        """
        Perform custom analysis based on user's specific request
        Enhanced with deep extraction pipeline for comprehensive insights
        
        Args:
            transcript: The full transcript text
            user_prompt: User's specific question or analysis request
            video_title: Optional video title for context
            
        Returns:
            Dictionary with analysis results including structured extraction
        """
        if not transcript or not user_prompt:
            return {
                "success": False,
                "error": "Missing transcript or prompt",
                "analysis": ""
            }
        
        # If no prompt provided, return empty analysis
        if user_prompt.lower() in ['', 'none', 'skip']:
            return {
                "success": True,
                "prompt": "Standard analysis",
                "analysis": None
            }
        
        # Use enhanced extraction if available
        if hasattr(self, 'use_enhanced') and self.use_enhanced and hasattr(self, 'enhanced_extractor') and self.enhanced_extractor:
            return self._analyze_with_enhanced_extraction(transcript, user_prompt, video_title)
        # Use deep extraction pipeline if available
        elif self.use_deep_extraction and self.deep_extractor:
            return self._analyze_with_deep_extraction(transcript, user_prompt, video_title)
        elif self.client:
            return self._analyze_with_openai(transcript, user_prompt, video_title)
        else:
            return self._analyze_with_local(transcript, user_prompt)
    
    def _analyze_with_enhanced_extraction(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Use enhanced extraction pipeline with automatic rubric selection"""
        try:
            print("\n🚀 Using ENHANCED extraction pipeline...")
            
            # Prepare metadata
            metadata = {
                "source": video_title or "direct_input",
                "provider": "unknown",
                "language": "en"
            }
            
            # Run enhanced extraction
            result = self.enhanced_extractor.extract_all_lenses(
                transcript=transcript,
                user_prompt=user_prompt,
                video_title=video_title,
                metadata=metadata
            )
            
            # Format based on schema type
            if result.get("schema_version") == "prompting_claude_v1":
                formatted_analysis = self._format_prompting_analysis(result)
            else:
                formatted_analysis = self._format_youtube_analysis(result)
            
            return {
                "success": True,
                "prompt": user_prompt,
                "analysis": formatted_analysis,
                "provider": "EnhancedExtractor",
                "structured_data": result,
                "schema_version": result.get("schema_version"),
                "quality_metrics": result.get("_metadata", {}).get("quality", {})
            }
            
        except Exception as e:
            print(f"⚠️ Enhanced extraction failed: {e}")
            # Fallback to standard extraction
            if self.deep_extractor:
                return self._analyze_with_deep_extraction(transcript, user_prompt, video_title)
            elif self.client:
                return self._analyze_with_openai(transcript, user_prompt, video_title)
            else:
                return self._analyze_with_local(transcript, user_prompt)
    
    def _analyze_with_deep_extraction(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Use deep extraction pipeline for comprehensive analysis"""
        try:
            # Step 1: Extract structured insights using deep extractor
            deep_extraction = self.deep_extractor.extract_all_lenses(transcript, user_prompt, video_title)
            
            # Step 2: Validate extraction quality
            validation = self.validator.validate_and_score(deep_extraction)
            
            # Step 3: Generate user-focused analysis based on prompt
            user_analysis = self._generate_user_focused_analysis(deep_extraction, user_prompt, video_title)
            
            # Step 4: Format as comprehensive playbook
            playbook = self._format_as_playbook(deep_extraction, user_analysis, user_prompt)
            
            return {
                "success": True,
                "prompt": user_prompt,
                "analysis": playbook,
                "provider": "DeepExtractor",
                "structured_data": deep_extraction,
                "validation_report": validation,
                "schema_version": deep_extraction.get("schema_version", "yt_playbook_v1")
            }
            
        except Exception as e:
            print(f"Deep extraction failed: {e}")
            # Fallback to OpenAI or local
            if self.client:
                return self._analyze_with_openai(transcript, user_prompt, video_title)
            else:
                return self._analyze_with_local(transcript, user_prompt)
    
    def _generate_user_focused_analysis(self, deep_extraction: Dict, user_prompt: str, video_title: str) -> str:
        """Generate analysis focused on user's specific prompt using extracted insights"""
        
        if self.client:
            try:
                # Use OpenAI to synthesize extracted insights into user-focused analysis
                system_prompt = f"""You are an expert at creating actionable analysis from structured insights.

Given extracted frameworks, metrics, psychology principles, and systems from content, 
create a focused analysis that directly addresses the user's specific question.

INSTRUCTIONS:
- Use the structured insights as evidence and examples
- Address the user's specific question directly
- Include concrete metrics and frameworks where relevant
- Make it actionable with specific next steps
- Preserve exact terminology from the extraction

USER'S QUESTION: {user_prompt}
VIDEO TITLE: {video_title}

Format as a comprehensive answer with:
1. Direct response to user's question
2. Supporting frameworks and evidence
3. Specific metrics and examples
4. Actionable next steps"""
                
                # Build context from extraction
                extraction_context = self._build_extraction_context(deep_extraction)
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Structured insights:\n\n{extraction_context}\n\nCreate focused analysis addressing: {user_prompt}"}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"User-focused analysis generation failed: {e}")
        
        # Fallback: Generate analysis from structured data directly
        return self._generate_analysis_from_structure(deep_extraction, user_prompt)
    
    def _build_extraction_context(self, extraction: Dict) -> str:
        """Build context string from extraction for OpenAI analysis"""
        context_parts = []
        
        # Add frameworks
        if extraction.get("frameworks"):
            context_parts.append("FRAMEWORKS:")
            for fw in extraction["frameworks"][:5]:  # Top 5
                if isinstance(fw, dict):
                    name = fw.get("name", "Framework")
                    definition = fw.get("definition", "")
                    context_parts.append(f"- {name}: {definition}")
        
        # Add metrics
        if extraction.get("metrics"):
            context_parts.append("\nMETRICS:")
            for metric in extraction["metrics"][:5]:  # Top 5
                if isinstance(metric, dict):
                    value = metric.get("value", "")
                    context = metric.get("context", "")
                    context_parts.append(f"- {value}: {context}")
        
        # Add psychology principles
        psychology = extraction.get("psychology", {})
        if psychology:
            context_parts.append("\nPSYCHOLOGY PRINCIPLES:")
            influence = psychology.get("influence_principles", [])
            for principle in influence[:3]:  # Top 3
                if isinstance(principle, dict):
                    name = principle.get("principle", "")
                    context = principle.get("context", "")
                    context_parts.append(f"- {name}: {context}")
        
        # Add systems
        systems = extraction.get("systems", {})
        if systems:
            context_parts.append("\nSYSTEMS:")
            content_systems = systems.get("content_systems", [])
            for system in content_systems[:3]:  # Top 3
                if isinstance(system, dict):
                    name = system.get("system", "")
                    context_parts.append(f"- {name}")
        
        # Add preserved terms
        if extraction.get("preserved_terms"):
            terms = extraction["preserved_terms"][:10]  # Top 10
            context_parts.append(f"\nPRESERVED TERMS: {', '.join(terms)}")
        
        return "\n".join(context_parts)
    
    def _generate_analysis_from_structure(self, extraction: Dict, user_prompt: str) -> str:
        """Generate analysis directly from structured data (fallback)"""
        analysis_parts = []
        
        analysis_parts.append(f"ANALYSIS: {user_prompt}")
        analysis_parts.append("=" * 50)
        
        # Add relevant frameworks
        frameworks = extraction.get("frameworks", [])
        if frameworks:
            analysis_parts.append("\n🔧 RELEVANT FRAMEWORKS:")
            for fw in frameworks[:3]:
                if isinstance(fw, dict):
                    name = fw.get("name", "Framework")
                    definition = fw.get("definition", "No definition provided")
                    analysis_parts.append(f"• {name}: {definition}")
        
        # Add supporting metrics
        metrics = extraction.get("metrics", [])
        if metrics:
            analysis_parts.append("\n📊 SUPPORTING METRICS:")
            for metric in metrics[:3]:
                if isinstance(metric, dict):
                    value = metric.get("value", "")
                    context = metric.get("context", "")
                    analysis_parts.append(f"• {value} - {context}")
        
        # Add next steps from quality check
        quality_check = extraction.get("quality_check", {})
        if quality_check.get("next_steps"):
            analysis_parts.append("\n🎯 NEXT STEPS:")
            for step in quality_check["next_steps"]:
                analysis_parts.append(f"• {step}")
        
        return "\n".join(analysis_parts)
    
    def _is_valid_framework(self, fw: Dict) -> bool:
        """Check if a framework extraction is actually valid"""
        if not isinstance(fw, dict):
            return False
        
        name = fw.get('name', '')
        definition = fw.get('definition', '')
        
        # Filter out garbage extractions
        if len(name) < 5 or len(definition) < 10:  # Too short
            return False
        if name.lower().startswith("i don't"):  # Not a framework
            return False
        if name.count(' ') > 15:  # Too long, probably a full sentence
            return False
        if not any(c.isalpha() for c in name):  # No letters
            return False
            
        return True
    
    def _is_valid_principle(self, principle: Dict) -> bool:
        """Check if a psychology principle is actually valid"""
        if not isinstance(principle, dict):
            return False
            
        name = principle.get('name', '')
        context = principle.get('context', '')
        
        # Single words are not principles
        if len(name.split()) <= 1:
            return False
        # Must have meaningful context
        if len(context) < 20:
            return False
        # Check for truncated context (ends mid-word)
        if context and not context[-1] in '.!?"\'':
            return False
            
        return True
    
    def _format_as_playbook(self, extraction: Dict, user_analysis: str, user_prompt: str) -> str:
        """Format the analysis as an actionable playbook"""
        
        playbook_parts = []
        
        # Title and user prompt
        playbook_parts.append("# ACTIONABLE PLAYBOOK")
        playbook_parts.append("=" * 70)
        playbook_parts.append(f"**Your Request:** {user_prompt}")
        playbook_parts.append("")
        
        # Main analysis
        playbook_parts.append("## 📋 ANALYSIS")
        playbook_parts.append(user_analysis)
        playbook_parts.append("")
        
        # Quick start section
        quality_check = extraction.get("quality_check", {})
        if quality_check.get("next_steps"):
            playbook_parts.append("## 🚀 QUICK START (Do Today)")
            for i, step in enumerate(quality_check["next_steps"], 1):
                playbook_parts.append(f"{i}. {step}")
            playbook_parts.append("")
        
        # Core frameworks section - WITH VALIDATION
        frameworks = extraction.get("frameworks", [])
        valid_frameworks = [fw for fw in frameworks if self._is_valid_framework(fw)]
        
        if valid_frameworks:
            playbook_parts.append("## 🔧 CORE FRAMEWORKS")
            for fw in valid_frameworks[:5]:  # Limit to 5 valid ones
                name = fw.get("name", "Framework")
                definition = fw.get("definition", "")
                components = fw.get("components", [])
                
                playbook_parts.append(f"### {name}")
                if definition:
                    playbook_parts.append(f"**Definition:** {definition}")
                if components:
                    playbook_parts.append("**Components:**")
                    for component in components:
                        playbook_parts.append(f"- {component}")
                playbook_parts.append("")
        
        # Proven tactics section
        metrics = extraction.get("metrics", [])
        if metrics:
            playbook_parts.append("## 📊 PROVEN TACTICS (With Metrics)")
            for metric in metrics[:5]:
                if isinstance(metric, dict):
                    value = metric.get("value", "")
                    context = metric.get("context", "")
                    playbook_parts.append(f"- **{value}** - {context}")
            playbook_parts.append("")
        
        # Psychology principles - DISABLED due to poor extraction quality
        # The extractor is just grabbing random words, not actual psychological principles
        # Uncomment and improve validation if this feature is needed in future
        
        # psychology = extraction.get("psychology", {})
        # influence_principles = psychology.get("influence_principles", []) if psychology else []
        # valid_principles = [p for p in influence_principles if self._is_valid_principle(p)]
        # 
        # if valid_principles:
        #     playbook_parts.append("## 🧠 PSYCHOLOGY PRINCIPLES")
        #     for principle in valid_principles[:3]:  # Limit to 3 valid ones
        #         name = principle.get("principle", "")
        #         context = principle.get("context", "")
        #         if len(context) > 20:  # Only show if context is meaningful
        #             playbook_parts.append(f"- **{name.title()}:** {context}")
        #     playbook_parts.append("")
        
        # Truthful quality summary (replacing fake coverage percentages)
        truthful_quality = extraction.get("truthful_quality")
        if truthful_quality:
            playbook_parts.append("## 📊 EXTRACTION SUMMARY")
            
            # Show actual items extracted (no inflation)
            items = truthful_quality.get("items_extracted", {})
            summary = truthful_quality.get("extraction_summary", "No structured content")
            playbook_parts.append(f"**Content:** {summary}")
            
            # Show key concepts found (factual)
            key_concepts = truthful_quality.get("key_concepts_found", [])
            if key_concepts:
                playbook_parts.append(f"**Key Concepts:** {', '.join(key_concepts)}")
            
            # Show honest gaps assessment
            gaps = truthful_quality.get("potential_gaps", [])
            if gaps:
                playbook_parts.append(f"**Potential Gaps:** {', '.join(gaps)}")
            
            # Show processing method (verifiable)
            schema_info = truthful_quality.get("schema_compliance", {})
            method = schema_info.get("extraction_method", "unknown")
            playbook_parts.append(f"**Method:** {method}")
        elif quality_check:
            # Legacy fallback - show honest metrics without fake percentages
            playbook_parts.append("## 📊 EXTRACTION SUMMARY")
            extraction_stats = quality_check.get("extraction_stats", {})
            if extraction_stats:
                frameworks = extraction_stats.get('frameworks', 0)
                metrics = extraction_stats.get('metrics', 0)
                case_studies = extraction_stats.get('case_studies', 0)
                
                summary_parts = []
                if frameworks > 0:
                    summary_parts.append(f"{frameworks} frameworks")
                if metrics > 0:
                    summary_parts.append(f"{metrics} metrics")
                if case_studies > 0:
                    summary_parts.append(f"{case_studies} case studies")
                    
                if summary_parts:
                    playbook_parts.append(f"**Content:** {', '.join(summary_parts)}")
                else:
                    playbook_parts.append("**Content:** No structured content extracted")
        
        return "\n".join(playbook_parts)
    
    def _analyze_with_openai(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Use OpenAI GPT with fact-grounded prompts to prevent hallucinations"""
        try:
            # First extract facts for grounding
            if self.use_factual_grounding:
                fact_analysis = self.fact_extractor.extract_all_facts(transcript)
                return self._analyze_with_fact_grounded_prompt(transcript, user_prompt, video_title, fact_analysis)
            else:
                return self._analyze_with_basic_prompt(transcript, user_prompt, video_title)

        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            # Fallback to local
            return self._analyze_with_local(transcript, user_prompt)

    def _analyze_with_fact_grounded_prompt(self, transcript: str, user_prompt: str,
                                         video_title: str, fact_analysis: Dict) -> Dict[str, Any]:
        """Fact-grounded analysis that prevents hallucinations"""
        # Extract key facts for grounding
        validated_facts = fact_analysis.get('facts', {})

        # Build fact context
        fact_context = self._build_fact_context(validated_facts)

        # Create constrained system message
        system_message = """You are a fact-based analyst. You must ONLY use information explicitly provided in the transcript and fact summary.

CRITICAL RULES:
1. NEVER invent or speculate about information not in the transcript
2. ONLY reference facts, quotes, and data points that are explicitly provided
3. If information is missing, say "not mentioned in transcript" rather than guessing
4. Quote directly from the source material when making claims
5. Focus on extractive analysis rather than generative interpretation
6. Mark any inference clearly as "based on context" vs "explicitly stated"

Your goal is to provide accurate, grounded analysis based solely on the provided content."""

        # Build context with video title if available
        context_parts = []
        if video_title:
            context_parts.append(f"Video Title: {video_title}")

        context_parts.append("\n=== EXTRACTED FACTS ===")
        context_parts.append(fact_context)

        context_parts.append("\n=== USER REQUEST ===")
        context_parts.append(f"Please {user_prompt}")

        context_parts.append("\n=== TRANSCRIPT EXCERPT ===")
        context_parts.append(transcript[:6000])  # Limit to avoid token limits

        context_parts.append("\n=== INSTRUCTIONS ===")
        context_parts.append("""Base your analysis ONLY on the facts and transcript provided above.
Structure your response with:
- Clear headers and bullet points
- Direct quotes from transcript when relevant
- Distinction between explicit facts vs contextual inferences
- "Not mentioned" for missing information rather than speculation""")

        full_context = "\n".join(context_parts)

        response = self.client.chat.completions.create(
            model="gpt-4o",  # Use more capable model for better instruction following
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_context}
            ],
            temperature=0.1,  # Low temperature for factual accuracy
            max_tokens=2000
        )

        analysis = response.choices[0].message.content.strip()

        # Validate the analysis doesn't contain blacklisted terms
        validated_analysis = self._validate_analysis_output(analysis, validated_facts)

        return {
            "success": True,
            "prompt": user_prompt,
            "analysis": validated_analysis,
            "provider": "OpenAI GPT-4 (Fact-Grounded)",
            "fact_validation": fact_analysis.get('validation_summary', {}),
            "confidence_score": fact_analysis.get('confidence_score', 0.0)
        }

    def _analyze_with_basic_prompt(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Basic OpenAI analysis (original method with hallucination risk)"""
        # Build context
        context = f"Video Title: {video_title}\n\n" if video_title else ""

        # Create system message for better results
        system_message = """You are an expert analyst helping users extract specific information from video transcripts.
        Provide clear, structured, and actionable insights based on the user's request.
        Use bullet points, numbered lists, and clear sections where appropriate.
        Be specific and quote relevant parts of the transcript when helpful."""

        # Construct the prompt
        full_prompt = f"""{context}Based on this transcript, please {user_prompt}

Transcript:
{transcript[:8000]}  # Limit to avoid token limits

Please provide a comprehensive response with:
- Clear organization (use headers, bullet points, etc.)
- Specific examples from the transcript
- Actionable insights where relevant"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        analysis = response.choices[0].message.content.strip()

        return {
            "success": True,
            "prompt": user_prompt,
            "analysis": analysis,
            "provider": "OpenAI GPT-4 (Basic)"
        }
    
    def _analyze_with_local(self, transcript: str, user_prompt: str) -> Dict[str, Any]:
        """Use fact-grounded local analysis (improved fallback)"""
        try:
            from analyzer import TextAnalyzer
            local_analyzer = TextAnalyzer()

            # Use fact extraction for grounding
            if self.use_factual_grounding:
                fact_analysis = self.fact_extractor.extract_all_facts(transcript)
                return self._analyze_local_with_facts(transcript, user_prompt, fact_analysis, local_analyzer)
            else:
                return self._analyze_local_basic(transcript, user_prompt, local_analyzer)

        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {e}",
                "prompt": user_prompt,
                "analysis": ""
            }

    def _analyze_local_with_facts(self, transcript: str, user_prompt: str,
                                fact_analysis: Dict, local_analyzer) -> Dict[str, Any]:
        """Local analysis grounded in extracted facts"""
        validated_facts = fact_analysis.get('facts', {})
        themes = fact_analysis.get('themes', [])

        # Parse the user prompt to determine what they want
        prompt_lower = user_prompt.lower()

        # Build response based on keywords in prompt
        analysis_parts = []
        analysis_parts.append(f"FACT-GROUNDED ANALYSIS: {user_prompt}")
        analysis_parts.append("=" * 50)

        # Check for common request types and use factual data
        if any(word in prompt_lower for word in ['summary', 'summarize', 'overview']):
            # Use extractive summary to prevent hallucinations
            summary = extract_grounded_summary(transcript, max_sentences=5)
            analysis_parts.append(f"\nEXTRACTIVE SUMMARY:\n{summary}")

        if any(word in prompt_lower for word in ['theme', 'topic', 'subject']):
            if themes:
                analysis_parts.append("\nFACT-BASED THEMES:")
                for i, theme in enumerate(themes[:5], 1):
                    title = theme.get('title', f'Theme {i}')
                    description = theme.get('description', 'No description')
                    evidence_count = theme.get('evidence_count', 0)
                    analysis_parts.append(f"{i}. {title}")
                    analysis_parts.append(f"   {description}")
                    if evidence_count > 0:
                        analysis_parts.append(f"   (Based on {evidence_count} factual references)")
            else:
                analysis_parts.append("\nNo clear factual themes identified in transcript.")

        if any(word in prompt_lower for word in ['fact', 'data', 'metric', 'number']):
            # Show extracted facts
            self._add_fact_summary(analysis_parts, validated_facts)

        if any(word in prompt_lower for word in ['quote', 'said', 'statement']):
            quotes = validated_facts.get('quotes', [])
            if quotes:
                memorable_quotes = [q for q in quotes if q.is_memorable][:3]
                analysis_parts.append("\nKEY QUOTES:")
                for quote in memorable_quotes:
                    speaker = f" ({quote.speaker})" if quote.speaker else ""
                    analysis_parts.append(f'• "{quote.text}"{speaker}')
            else:
                analysis_parts.append("\nNo clear quotes extracted from transcript.")

        if any(word in prompt_lower for word in ['sentiment', 'emotion', 'feeling', 'mood']):
            sentiment = local_analyzer.analyze_sentiment(transcript)
            sentiment_text = f"\nSENTIMENT ANALYSIS:\n{sentiment.get('label', 'Unknown')} "
            sentiment_text += f"(confidence: {sentiment.get('confidence', 0):.1%})"
            analysis_parts.append(sentiment_text)

        # If no specific keywords matched, provide a comprehensive analysis
        if len(analysis_parts) <= 2:  # Only header added
            analysis_parts.append("\nCOMPREHENSIVE FACTUAL ANALYSIS:")

            # Add extractive summary
            summary = extract_grounded_summary(transcript, max_sentences=4)
            analysis_parts.append(f"\nSummary: {summary}")

            # Add fact summary
            self._add_fact_summary(analysis_parts, validated_facts)

            # Add themes if available
            if themes:
                analysis_parts.append("\nMain Topics:")
                for theme in themes[:3]:
                    analysis_parts.append(f"• {theme.get('title', 'Topic')}")

        # Add validation summary
        validation_summary = fact_analysis.get('validation_summary', {})
        total_facts = validation_summary.get('total_facts_extracted', 0)
        confidence = fact_analysis.get('confidence_score', 0.0)

        analysis_parts.append(f"\n[Analysis based on {total_facts} validated facts, confidence: {confidence:.1%}]")

        return {
            "success": True,
            "prompt": user_prompt,
            "analysis": "\n".join(analysis_parts),
            "provider": "Local Models (Fact-Grounded)",
            "fact_validation": validation_summary,
            "confidence_score": confidence
        }

    def _analyze_local_basic(self, transcript: str, user_prompt: str, local_analyzer) -> Dict[str, Any]:
        """Basic local analysis (original method with hallucination risk)"""
        # Parse the user prompt to determine what they want
        prompt_lower = user_prompt.lower()

        # Build response based on keywords in prompt
        analysis_parts = []

        # Check for common request types
        if any(word in prompt_lower for word in ['summary', 'summarize', 'overview']):
            summary = local_analyzer.summarize(transcript, max_length=200)
            analysis_parts.append(f"SUMMARY:\n{summary}")

        if any(word in prompt_lower for word in ['theme', 'topic', 'subject']):
            themes = local_analyzer.extract_themes(transcript, num_themes=5)
            themes_text = "\n\nKEY THEMES:\n"
            for i, theme in enumerate(themes, 1):
                themes_text += f"{i}. {theme.get('title', 'Theme')}\n"
                if theme.get('description'):
                    themes_text += f"   {theme['description']}\n"
            analysis_parts.append(themes_text)

        if any(word in prompt_lower for word in ['sentiment', 'emotion', 'feeling', 'mood']):
            sentiment = local_analyzer.analyze_sentiment(transcript)
            sentiment_text = f"\n\nSENTIMENT:\n{sentiment.get('label', 'Unknown')} "
            sentiment_text += f"(confidence: {sentiment.get('confidence', 0):.1%})"
            analysis_parts.append(sentiment_text)

        # If no specific keywords matched, provide a general analysis
        if not analysis_parts:
            analysis_parts.append("Note: Using local analysis (limited capabilities).")
            analysis_parts.append(f"\nYour request: {user_prompt}")
            analysis_parts.append("\nGenerating basic analysis...")

            # Provide summary and themes as default
            summary = local_analyzer.summarize(transcript, max_length=150)
            analysis_parts.append(f"\nSUMMARY:\n{summary}")

            themes = local_analyzer.extract_themes(transcript, num_themes=3)
            if themes:
                analysis_parts.append("\n\nMAIN TOPICS:")
                for theme in themes:
                    analysis_parts.append(f"• {theme.get('title', 'Topic')}")

        return {
            "success": True,
            "prompt": user_prompt,
            "analysis": "\n".join(analysis_parts),
            "provider": "Local Models (Basic)",
            "note": "For best results with custom prompts, configure OpenAI API key"
        }
    
    def suggest_prompts(self, video_title: str = "", video_description: str = "") -> List[str]:
        """
        Suggest relevant analysis prompts based on video metadata
        
        Returns:
            List of suggested prompts
        """
        suggestions = []
        
        # Analyze title/description for content type
        content = (video_title + " " + video_description).lower()
        
        # Interview detection
        if any(word in content for word in ['interview', 'conversation', 'discussion', 'talk']):
            suggestions.extend([
                "Extract key insights and advice from each speaker",
                "List the most important quotes and who said them",
                "Summarize each person's main points separately"
            ])
        
        # Tutorial/How-to detection  
        elif any(word in content for word in ['how to', 'tutorial', 'guide', 'tips', 'learn']):
            suggestions.extend([
                "List all steps or instructions mentioned",
                "Extract all tips and best practices",
                "Create a summary of the key learning points"
            ])
        
        # YouTube/Creator content
        elif any(word in content for word in ['youtube', 'creator', 'content', 'channel', 'subscriber']):
            suggestions.extend([
                "Extract all YouTube growth tips and strategies mentioned",
                "List advice about thumbnails, titles, and content creation",
                "Summarize the content strategy recommendations"
            ])
        
        # Presentation/Lecture
        elif any(word in content for word in ['presentation', 'lecture', 'keynote', 'conference']):
            suggestions.extend([
                "Outline the main points and supporting arguments",
                "Extract key concepts and definitions",
                "List any action items or conclusions"
            ])
        
        # Meeting/Business
        elif any(word in content for word in ['meeting', 'agenda', 'business', 'project']):
            suggestions.extend([
                "Extract all action items and who's responsible",
                "List decisions made and next steps",
                "Summarize key discussion points and outcomes"
            ])
        
        # Default suggestions if no specific type detected
        if not suggestions:
            suggestions = [
                "Provide a detailed summary with key points",
                "Extract the most important insights and lessons",
                "List all actionable advice mentioned"
            ]
        
        return suggestions

    def _build_fact_context(self, validated_facts: Dict) -> str:
        """Build context string from validated facts"""
        context_parts = []

        # Add dates and events
        events = validated_facts.get('dates_and_events', [])
        if events:
            context_parts.append("DATES & EVENTS:")
            for fact in events[:5]:
                context_parts.append(f"• {fact.content} - {fact.context[:100]}")

        # Add metrics and numbers
        metrics = validated_facts.get('metrics_and_numbers', [])
        if metrics:
            context_parts.append("\nMETRICS & DATA:")
            for fact in metrics[:5]:
                context_parts.append(f"• {fact.content} - {fact.context[:100]}")

        # Add companies and entities
        entities = validated_facts.get('companies_and_entities', [])
        if entities:
            entity_names = list(set(f.content for f in entities))
            context_parts.append(f"\nCOMPANIES/ENTITIES: {', '.join(entity_names[:10])}")

        # Add memorable quotes
        quotes = validated_facts.get('quotes', [])
        memorable_quotes = [q for q in quotes if q.is_memorable][:3]
        if memorable_quotes:
            context_parts.append("\nKEY QUOTES:")
            for quote in memorable_quotes:
                speaker = f" ({quote.speaker})" if quote.speaker else ""
                context_parts.append(f'• "{quote.text}"{speaker}')

        return "\n".join(context_parts) if context_parts else "No specific facts extracted."

    def _validate_analysis_output(self, analysis: str, validated_facts: Dict) -> str:
        """Validate analysis output to ensure it doesn't contain blacklisted terms"""
        # Check for joke terms that should not appear
        joke_terms = {
            'iphone 17', 'iphone 18', 'iphone 20', 'tesla phone',
            'vision pro 2', 'chatgpt 10', 'gpt-10'
        }

        analysis_lower = analysis.lower()

        # Flag potential hallucinations
        hallucination_warnings = []
        for term in joke_terms:
            if term in analysis_lower:
                hallucination_warnings.append(term)

        if hallucination_warnings:
            warning_text = f"\n\n⚠️ WARNING: Analysis may contain speculative content: {', '.join(hallucination_warnings)}"
            warning_text += "\nThis information was not validated against the transcript."
            analysis += warning_text

        return analysis

    def _add_fact_summary(self, analysis_parts: List[str], validated_facts: Dict) -> None:
        """Add fact summary to analysis parts"""
        events = validated_facts.get('dates_and_events', [])
        metrics = validated_facts.get('metrics_and_numbers', [])
        entities = validated_facts.get('companies_and_entities', [])

        if events or metrics or entities:
            analysis_parts.append("\nEXTRACTED FACTS:")

            if events:
                event_content = [f.content for f in events[:3]]
                analysis_parts.append(f"• Events: {', '.join(event_content)}")

            if metrics:
                metric_content = [f.content for f in metrics[:3]]
                analysis_parts.append(f"• Metrics: {', '.join(metric_content)}")

            if entities:
                entity_names = list(set(f.content for f in entities))[:3]
                analysis_parts.append(f"• Entities: {', '.join(entity_names)}")
        else:
            analysis_parts.append("\nNo specific factual data extracted from transcript.")
    
    def _format_prompting_analysis(self, extraction: Dict) -> str:
        """Format prompting extraction for display"""
        structure = extraction.get("structure", {})
        
        sections = []
        
        # Title
        sections.append("=" * 60)
        sections.append("PROMPT ENGINEERING BEST PRACTICES")
        sections.append("=" * 60)
        
        # Key lessons
        sections.append("\n## 🎯 KEY PROMPTING LESSONS\n")
        
        if structure.get("role"):
            sections.append(f"**Role Definition:** {structure['role']}")
        
        if structure.get("tone"):
            sections.append(f"**Tone Guidance:** {structure['tone']}")
        
        if structure.get("ordered_steps"):
            sections.append("\n**Ordered Reasoning Steps:**")
            for i, step in enumerate(structure["ordered_steps"][:5], 1):
                sections.append(f"  {i}. {step}")
        
        if structure.get("guardrails"):
            sections.append("\n**Safety Guardrails:**")
            for guardrail in structure["guardrails"][:3]:
                sections.append(f"  • {guardrail}")
        
        # Template
        if extraction.get("template"):
            sections.append("\n## 📝 BATTLE-TESTED PROMPT TEMPLATE\n")
            sections.append("```")
            sections.append(extraction["template"][:1500])  # Truncate if too long
            sections.append("```")
        
        # Checklist
        if extraction.get("checklist"):
            sections.append("\n## ✅ IMPLEMENTATION CHECKLIST\n")
            for item in extraction["checklist"][:7]:
                sections.append(f"  ☐ {item}")
        
        # Quality metrics
        if "_metadata" in extraction:
            quality = extraction["_metadata"].get("quality", {})
            sections.append(f"\n## 📊 EXTRACTION QUALITY")
            sections.append(f"  Fragment Quality: {quality.get('fragment_quality', 0):.1%}")
            sections.append(f"  Schema Compliance: {quality.get('schema_compliance', 0):.1%}")
            sections.append(f"  Round-trip Valid: {'✅' if quality.get('round_trip_valid') else '❌'}")
        
        return "\n".join(sections)
    
    def _format_youtube_analysis(self, extraction: Dict) -> str:
        """Format YouTube extraction for display"""
        sections = []
        
        # Title
        sections.append("=" * 60)
        sections.append("YOUTUBE GROWTH PLAYBOOK")
        sections.append("=" * 60)
        
        # Frameworks
        if extraction.get("frameworks"):
            sections.append("\n## 🔧 FRAMEWORKS & STRATEGIES\n")
            for fw in extraction["frameworks"][:5]:
                name = fw.get("name", "Unknown")
                definition = fw.get("definition", "")
                if definition:
                    sections.append(f"**{name}:** {definition}")
                else:
                    sections.append(f"**{name}**")
        
        # Metrics
        if extraction.get("metrics"):
            sections.append("\n## 📈 KEY METRICS & RESULTS\n")
            for metric in extraction["metrics"][:5]:
                value = metric.get("value", "")
                context = metric.get("context", "")
                sections.append(f"  • **{value}** - {context}")
        
        # Case studies
        if extraction.get("case_studies"):
            sections.append("\n## 💡 CASE STUDIES\n")
            for case in extraction["case_studies"][:3]:
                name = case.get("name", "Unknown")
                pattern = case.get("pattern_or_framework", "")
                effect = case.get("measured_effect", "")
                sections.append(f"**{name}:**")
                if pattern:
                    sections.append(f"  Strategy: {pattern}")
                if effect:
                    sections.append(f"  Result: {effect}")
        
        # Quality check
        if extraction.get("quality_check"):
            qc = extraction["quality_check"]
            sections.append(f"\n## ✅ QUALITY CHECK")
            if qc.get("footer"):
                footer = qc["footer"]
                sections.append(f"  Coverage: {footer.get('coverage', 'N/A')}")
                sections.append(f"  Gaps: {footer.get('gaps', 'None')}")
                sections.append(f"  Action: {footer.get('actionability', 'Review insights')}")
        
        return "\n".join(sections)
    
    def get_template_prompts(self) -> Dict[str, str]:
        """
        Get pre-defined template prompts for common use cases
        
        Returns:
            Dictionary of template names and prompts
        """
        return {
            "youtube_creator": "Extract all tips about: video creation, thumbnails, titles, "
                              "audience growth, monetization, and content strategy",
            
            "interview_insights": "For each speaker, list: main points, key quotes, advice given, "
                                 "and interesting stories or examples shared",
            
            "tutorial_steps": "Create a numbered list of all steps, instructions, and procedures "
                             "mentioned. Include any warnings, tips, or requirements",
            
            "meeting_notes": "Extract: agenda items discussed, decisions made, action items "
                            "(with owners), deadlines mentioned, and follow-up tasks",
            
            "lecture_outline": "Create an outline with: main topics, key concepts defined, "
                              "examples given, important points emphasized, and conclusions",
            
            "podcast_highlights": "Extract: interesting stories, surprising facts, expert opinions, "
                                 "book/resource recommendations, and quotable moments",
            
            "product_review": "Summarize: pros mentioned, cons mentioned, features discussed, "
                             "comparisons made, and final recommendations",
            
            "news_analysis": "Extract: main events, key facts and figures, quotes from officials, "
                            "implications discussed, and expert opinions"
        }