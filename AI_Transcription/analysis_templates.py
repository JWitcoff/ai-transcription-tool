"""
Analysis Templates - Pre-defined analysis patterns for common use cases
Provides structured prompts for different types of content analysis
"""

from typing import Dict, List, Optional

class AnalysisTemplates:
    """Collection of pre-defined analysis templates"""
    
    def __init__(self):
        self.templates = {
            # YouTube Creator Content
            "youtube_creator": {
                "name": "YouTube Creator Tips",
                "description": "Extract content creation advice and strategies",
                "prompt": """Extract all YouTube growth tips and strategies mentioned in this video, organized by category:

1. **THUMBNAILS**: Tips about thumbnail design, colors, testing, A/B testing
2. **TITLES**: Title writing strategies, keywords, hooks, click-through optimization
3. **CONTENT STRATEGY**: Video ideas, series planning, audience targeting, niche selection
4. **AUDIENCE GROWTH**: Subscriber strategies, community building, engagement tactics
5. **MONETIZATION**: Revenue streams, brand deals, YouTube Partner Program tips
6. **TECHNICAL**: Upload schedules, SEO, analytics, optimization techniques
7. **MINDSET**: Creator advice, dealing with failure, staying motivated

For each tip, include:
- The specific advice given
- Who mentioned it (if multiple speakers)
- Any specific examples or numbers mentioned""",
                "tags": ["youtube", "creator", "content", "growth"]
            },
            
            # Interview Analysis
            "interview_insights": {
                "name": "Interview Key Insights",
                "description": "Extract insights, quotes, and advice from interviews",
                "prompt": """Analyze this interview and extract key information for each speaker:

**For each speaker, provide:**

1. **MAIN POINTS**: 3-5 key points they made
2. **BEST QUOTES**: Most impactful or memorable quotes
3. **ADVICE GIVEN**: Specific actionable advice they shared
4. **STORIES/EXAMPLES**: Interesting anecdotes or case studies mentioned
5. **EXPERTISE AREAS**: What topics they're most knowledgeable about
6. **CONTACT/RESOURCES**: Any books, websites, or resources they mentioned

**OVERALL INTERVIEW ANALYSIS:**
- Key themes discussed
- Most surprising revelations
- Practical takeaways for listeners
- Follow-up questions that could be explored""",
                "tags": ["interview", "insights", "quotes", "advice"]
            },
            
            # Tutorial/Educational Content
            "tutorial_breakdown": {
                "name": "Tutorial Step-by-Step",
                "description": "Create structured breakdown of instructional content",
                "prompt": """Break down this tutorial into a comprehensive guide:

**OVERVIEW:**
- What will be taught/built/achieved
- Prerequisites or requirements
- Expected time to complete

**STEP-BY-STEP INSTRUCTIONS:**
Number each step clearly and include:
1. What to do (action)
2. Why it's important (reason)
3. Common mistakes to avoid
4. Expected results

**TOOLS & RESOURCES:**
- Required software/tools
- Recommended settings or configurations
- Links or resources mentioned

**TROUBLESHOOTING:**
- Common problems and solutions
- Warning signs to watch for
- How to verify everything is working

**NEXT STEPS:**
- What to do after completing this tutorial
- Advanced techniques or improvements
- Related skills to learn""",
                "tags": ["tutorial", "education", "howto", "instructions"]
            },
            
            # Meeting/Business Analysis
            "meeting_notes": {
                "name": "Meeting Summary",
                "description": "Structured meeting notes with action items",
                "prompt": """Create comprehensive meeting notes:

**MEETING OVERVIEW:**
- Date and attendees (if mentioned)
- Main agenda topics covered
- Meeting type (planning, review, brainstorming, etc.)

**KEY DISCUSSIONS:**
For each major topic:
- What was discussed
- Different viewpoints presented
- Decisions reached (if any)

**ACTION ITEMS:**
List all tasks and commitments:
- Task description
- Person responsible
- Deadline (if mentioned)
- Priority level
- Dependencies

**DECISIONS MADE:**
- What was decided
- Rationale behind decisions
- Who made the final call

**FOLLOW-UP ITEMS:**
- Topics to be discussed in future meetings
- Information needed before next steps
- Unresolved questions or issues

**KEY METRICS/NUMBERS:**
- Important figures, dates, budgets mentioned
- Performance metrics discussed
- Targets or goals set""",
                "tags": ["meeting", "business", "action-items", "decisions"]
            },
            
            # Podcast Analysis
            "podcast_highlights": {
                "name": "Podcast Highlights",
                "description": "Extract interesting stories, facts, and recommendations",
                "prompt": """Extract the most interesting content from this podcast:

**KEY STORIES & ANECDOTES:**
- Most interesting personal stories shared
- Surprising or unexpected revelations
- Behind-the-scenes insights

**SURPRISING FACTS:**
- Counter-intuitive information
- Little-known facts or statistics
- Myth-busting moments

**EXPERT OPINIONS:**
- Unique perspectives or hot takes
- Industry insights
- Predictions about the future

**RECOMMENDATIONS:**
- Books, podcasts, or content recommended
- Tools or products endorsed
- People worth following

**QUOTABLE MOMENTS:**
- Most impactful or memorable quotes
- Funny or clever observations
- Profound insights

**ACTIONABLE ADVICE:**
- Specific steps listeners can take
- Life or business improvements suggested
- Skills worth developing

**RESOURCES MENTIONED:**
- Websites, apps, or tools
- Studies or research referenced
- Communities or events mentioned""",
                "tags": ["podcast", "stories", "recommendations", "insights"]
            },
            
            # Product Review Analysis
            "product_review": {
                "name": "Product Review Summary",
                "description": "Structured analysis of product reviews",
                "prompt": """Analyze this product review comprehensively:

**PRODUCT OVERVIEW:**
- Product name and category
- Price point mentioned
- Main use cases or target audience

**PROS (Positive Aspects):**
- Features that work well
- Benefits highlighted
- Standout qualities
- Value for money aspects

**CONS (Negative Aspects):**
- Limitations or drawbacks
- Missing features
- Issues encountered
- Overpriced elements

**DETAILED FEATURES:**
For each major feature discussed:
- How it works
- Performance rating (if given)
- Comparison to competitors (if mentioned)

**USE CASES:**
- Best scenarios for this product
- Who should buy it
- Who should avoid it

**COMPARISONS:**
- Alternative products mentioned
- How it stacks against competitors
- Unique selling points

**FINAL VERDICT:**
- Overall rating or recommendation
- Best value proposition
- Deal-breakers to consider

**PURCHASE ADVICE:**
- Where to buy (if mentioned)
- Best time to purchase
- Things to consider before buying""",
                "tags": ["review", "product", "comparison", "buying-guide"]
            },
            
            # News/Current Events
            "news_analysis": {
                "name": "News Analysis",
                "description": "Structured breakdown of news content",
                "prompt": """Analyze this news content systematically:

**MAIN STORY:**
- What happened (the core event/announcement)
- When and where it occurred
- Key people or organizations involved

**KEY FACTS & FIGURES:**
- Important statistics or numbers
- Dates and timelines
- Financial figures (if relevant)
- Scale or impact measurements

**STAKEHOLDERS:**
- Who is affected and how
- Winners and losers
- Different perspectives on the issue

**EXPERT OPINIONS:**
- Analyst predictions
- Industry expert commentary
- Different viewpoints presented

**CONTEXT & BACKGROUND:**
- Why this is happening now
- Historical context
- Related previous events

**IMPLICATIONS:**
- Short-term consequences
- Long-term potential impacts
- How this affects various groups

**QUOTES:**
- Key statements from officials
- Expert opinions
- Reaction quotes from affected parties

**WHAT'S NEXT:**
- Expected developments
- Timeline for changes
- Things to watch for""",
                "tags": ["news", "analysis", "current-events", "politics"]
            },
            
            # Lecture/Academic Content
            "lecture_notes": {
                "name": "Lecture Notes",
                "description": "Academic content organization for study purposes",
                "prompt": """Create comprehensive lecture notes:

**LECTURE OVERVIEW:**
- Course/topic title
- Main learning objectives
- Key concepts to be covered

**MAIN CONCEPTS:**
For each major concept:
- Clear definition
- Why it's important
- How it relates to other concepts
- Real-world applications

**EXAMPLES & CASE STUDIES:**
- Specific examples given
- Case studies analyzed
- Problem-solving demonstrations
- Historical examples or context

**FORMULAS & METHODS:**
- Important equations or formulas
- Step-by-step procedures
- Problem-solving approaches
- Common mistakes to avoid

**KEY TERMS & DEFINITIONS:**
- Technical vocabulary
- Important terminology
- Acronyms and their meanings

**ASSIGNMENTS & REQUIREMENTS:**
- Homework or project assignments
- Reading recommendations
- Exam information
- Due dates and requirements

**STUDY TIPS:**
- Areas emphasized by instructor
- Likely exam topics
- Recommended review strategies
- Additional resources mentioned

**QUESTIONS FOR REVIEW:**
- Unclear points that need clarification
- Topics for further study
- Practice problems to work on""",
                "tags": ["lecture", "academic", "education", "study-notes"]
            },
            
            # Q&A Session Analysis
            "qa_session": {
                "name": "Q&A Session Summary",
                "description": "Organize questions and answers from Q&A sessions",
                "prompt": """Organize this Q&A session systematically:

**SESSION OVERVIEW:**
- Topic or context of the Q&A
- Number of questions covered
- Main themes of inquiries

**QUESTIONS & ANSWERS:**
For each Q&A pair:
- **Question**: [Complete question asked]
- **Answer**: [Summary of the response]
- **Key Points**: [Main takeaways from the answer]
- **Follow-up**: [Any additional clarification provided]

**MOST VALUABLE Q&As:**
- Questions with the most practical answers
- Surprising or unexpected responses
- Questions many people probably have

**COMMON THEMES:**
- Topics that came up multiple times
- Areas of most confusion or interest
- Patterns in the types of questions

**UNANSWERED QUESTIONS:**
- Questions that weren't fully addressed
- Topics that need more explanation
- Suggestions for follow-up content

**ACTIONABLE INSIGHTS:**
- Practical advice that can be implemented
- Resources or next steps recommended
- Common mistakes to avoid

**EXPERT INSIGHTS:**
- Unique perspectives shared
- Industry knowledge revealed
- Professional tips or secrets""",
                "tags": ["qa", "questions", "answers", "insights"]
            }
        }
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID"""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """Get all available templates"""
        return self.templates
    
    def list_templates(self) -> List[Dict]:
        """Get list of templates with basic info"""
        template_list = []
        for template_id, template in self.templates.items():
            template_list.append({
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "tags": template["tags"]
            })
        return template_list
    
    def search_templates(self, query: str = "", tag: str = "") -> List[Dict]:
        """Search templates by name, description, or tags"""
        results = []
        query_lower = query.lower() if query else ""
        
        for template_id, template in self.templates.items():
            # Text search
            if query_lower:
                name_match = query_lower in template["name"].lower()
                desc_match = query_lower in template["description"].lower()
                tag_match = any(query_lower in t.lower() for t in template["tags"])
                
                if not (name_match or desc_match or tag_match):
                    continue
            
            # Tag filter
            if tag and tag.lower() not in [t.lower() for t in template["tags"]]:
                continue
            
            results.append({
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "tags": template["tags"]
            })
        
        return results
    
    def get_template_by_content_type(self, video_title: str = "", video_description: str = "") -> Optional[str]:
        """
        Suggest best template based on video content
        
        Returns:
            Template ID or None if no good match
        """
        content = (video_title + " " + video_description).lower()
        
        # Interview detection
        if any(word in content for word in ['interview', 'conversation', 'discussion', 'talk with']):
            return "interview_insights"
        
        # Tutorial detection  
        elif any(word in content for word in ['how to', 'tutorial', 'guide', 'step by step', 'walkthrough']):
            return "tutorial_breakdown"
        
        # YouTube creator content
        elif any(word in content for word in ['youtube', 'creator', 'content creation', 'channel', 'subscriber']):
            return "youtube_creator"
        
        # Meeting/Business
        elif any(word in content for word in ['meeting', 'agenda', 'business', 'project', 'team']):
            return "meeting_notes"
        
        # Podcast
        elif any(word in content for word in ['podcast', 'episode', 'show', 'host']):
            return "podcast_highlights"
        
        # Product review
        elif any(word in content for word in ['review', 'unboxing', 'test', 'comparison', 'vs']):
            return "product_review"
        
        # News/Analysis
        elif any(word in content for word in ['news', 'analysis', 'report', 'breaking', 'update']):
            return "news_analysis"
        
        # Lecture/Educational
        elif any(word in content for word in ['lecture', 'lesson', 'course', 'class', 'professor']):
            return "lecture_notes"
        
        # Q&A
        elif any(word in content for word in ['q&a', 'questions', 'answers', 'ask me anything']):
            return "qa_session"
        
        return None
    
    def create_custom_template(self, name: str, description: str, prompt: str, tags: List[str] = None) -> str:
        """
        Create a custom template (for future enhancement)
        
        Returns:
            Template ID
        """
        template_id = name.lower().replace(' ', '_').replace('-', '_')
        template_id = ''.join(c for c in template_id if c.isalnum() or c == '_')
        
        self.templates[template_id] = {
            "name": name,
            "description": description,
            "prompt": prompt,
            "tags": tags or [],
            "custom": True
        }
        
        return template_id