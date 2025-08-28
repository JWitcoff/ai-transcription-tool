"""
Custom Analyzer - User-directed analysis based on specific prompts
Enhanced with deep extraction pipeline for frameworks, metrics, and psychology
"""

import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CustomAnalyzer:
    """Performs custom analysis with enhanced deep extraction capabilities"""
    
    def __init__(self, use_deep_extraction: bool = True):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        self.use_deep_extraction = use_deep_extraction
        self.deep_extractor = None
        self.validator = None
        
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
        
        # Use deep extraction pipeline if available
        if self.use_deep_extraction and self.deep_extractor:
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
        
        # Core frameworks section
        frameworks = extraction.get("frameworks", [])
        if frameworks:
            playbook_parts.append("## 🔧 CORE FRAMEWORKS")
            for fw in frameworks[:5]:
                if isinstance(fw, dict):
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
        
        # Psychology principles
        psychology = extraction.get("psychology", {})
        influence_principles = psychology.get("influence_principles", []) if psychology else []
        if influence_principles:
            playbook_parts.append("## 🧠 PSYCHOLOGY PRINCIPLES")
            for principle in influence_principles[:5]:
                if isinstance(principle, dict):
                    name = principle.get("principle", "")
                    context = principle.get("context", "")
                    playbook_parts.append(f"- **{name.title()}:** {context}")
            playbook_parts.append("")
        
        # Quality check footer
        if quality_check:
            playbook_parts.append("## ✅ QUALITY CHECK")
            coverage_score = quality_check.get("coverage_score", 0)
            playbook_parts.append(f"**Coverage:** {coverage_score:.1%} of key elements extracted")
            
            gaps = quality_check.get("gaps", [])
            if gaps:
                playbook_parts.append(f"**Gaps:** {', '.join(gaps[:3])}")
            
            extraction_stats = quality_check.get("extraction_stats", {})
            if extraction_stats:
                playbook_parts.append(f"**Found:** {extraction_stats.get('frameworks', 0)} frameworks, {extraction_stats.get('metrics', 0)} metrics")
        
        return "\n".join(playbook_parts)
    
    def _analyze_with_openai(self, transcript: str, user_prompt: str, video_title: str) -> Dict[str, Any]:
        """Use OpenAI GPT for custom analysis"""
        try:
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
                "provider": "OpenAI GPT-4"
            }
            
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            # Fallback to local
            return self._analyze_with_local(transcript, user_prompt)
    
    def _analyze_with_local(self, transcript: str, user_prompt: str) -> Dict[str, Any]:
        """Use local models for custom analysis (fallback)"""
        try:
            from analyzer import TextAnalyzer
            local_analyzer = TextAnalyzer()
            
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
                "provider": "Local Models",
                "note": "For best results with custom prompts, configure OpenAI API key"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {e}",
                "prompt": user_prompt,
                "analysis": ""
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