"""
OpenAI-powered analyzer for enhanced summaries and analysis
Falls back to local models if no API key is provided
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIAnalyzer:
    """Enhanced analyzer using OpenAI GPT models when available"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key and self.api_key != 'your_openai_api_key_here':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                print("✅ OpenAI API initialized for enhanced analysis")
            except ImportError:
                print("⚠️  OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {e}")
        else:
            print("ℹ️  No OpenAI API key found. Using local models.")
    
    def summarize(self, text: str, max_length: int = 150) -> str:
        """
        Generate summary using OpenAI GPT-4 if available, else local model
        """
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Fast and cheap model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                        {"role": "user", "content": f"Summarize this text in {max_length} words or less:\n\n{text[:4000]}"}
                    ],
                    max_tokens=max_length * 2,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI API error: {e}")
        
        # Fallback to local analyzer
        from analyzer import TextAnalyzer
        local_analyzer = TextAnalyzer()
        return local_analyzer.summarize(text, max_length)
    
    def extract_themes(self, text: str, num_themes: int = 5) -> List[Dict]:
        """
        Extract themes using OpenAI GPT-4 if available
        """
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying key themes and topics in text."},
                        {"role": "user", "content": f"""Extract {num_themes} key themes from this text. 
For each theme provide:
1. A title
2. A brief description
3. 3-5 relevant keywords

Text: {text[:4000]}

Format your response as a numbered list with clear sections."""}
                    ],
                    temperature=0.5
                )
                
                # Parse response into structured format
                themes = []
                content = response.choices[0].message.content
                theme_blocks = content.split('\n\n')
                
                for block in theme_blocks[:num_themes]:
                    if block.strip():
                        lines = block.strip().split('\n')
                        title = lines[0].replace('**', '').strip() if lines else "Theme"
                        description = lines[1] if len(lines) > 1 else "No description"
                        keywords = []
                        
                        for line in lines:
                            if 'keyword' in line.lower():
                                # Extract keywords from the line
                                keywords_text = line.split(':')[-1] if ':' in line else line
                                keywords = [k.strip() for k in keywords_text.split(',')]
                                break
                        
                        themes.append({
                            "title": title,
                            "description": description,
                            "keywords": keywords[:5]
                        })
                
                return themes[:num_themes]
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
        
        # Fallback to local analyzer
        from analyzer import TextAnalyzer
        local_analyzer = TextAnalyzer()
        return local_analyzer.extract_themes(text, num_themes)
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment using OpenAI if available
        """
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a sentiment analysis expert."},
                        {"role": "user", "content": f"""Analyze the sentiment of this text.
Provide:
1. Overall sentiment (POSITIVE, NEGATIVE, or NEUTRAL)
2. Confidence score (0-1)
3. Primary emotion (joy, sadness, anger, fear, surprise, trust, anticipation, or neutral)

Text: {text[:2000]}

Respond in this exact format:
Sentiment: [POSITIVE/NEGATIVE/NEUTRAL]
Confidence: [0.0-1.0]
Emotion: [emotion]"""}
                    ],
                    temperature=0.1
                )
                
                # Parse response
                content = response.choices[0].message.content
                lines = content.strip().split('\n')
                
                sentiment = "NEUTRAL"
                confidence = 0.5
                emotion = "neutral"
                
                for line in lines:
                    if 'Sentiment:' in line:
                        sentiment = line.split(':')[-1].strip().upper()
                    elif 'Confidence:' in line:
                        try:
                            confidence = float(line.split(':')[-1].strip())
                        except:
                            confidence = 0.5
                    elif 'Emotion:' in line:
                        emotion = line.split(':')[-1].strip().lower()
                
                return {
                    'label': sentiment,
                    'score': confidence,
                    'confidence': confidence,
                    'emotion': emotion
                }
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
        
        # Fallback to local analyzer
        from analyzer import TextAnalyzer
        local_analyzer = TextAnalyzer()
        return local_analyzer.analyze_sentiment(text)
    
    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """
        Extract key points from text using OpenAI
        """
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying key points and insights."},
                        {"role": "user", "content": f"""Extract {num_points} key points from this text.
Focus on:
- Important decisions
- Action items
- Key questions raised
- Main conclusions

Text: {text[:3000]}

List each point as a clear, concise bullet point."""}
                    ],
                    temperature=0.3
                )
                
                content = response.choices[0].message.content
                points = []
                
                for line in content.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                        point = line.lstrip('-•* ').strip()
                        if point:
                            points.append(point)
                
                return points[:num_points]
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                return []
        
        return []
    
    def generate_action_items(self, text: str) -> List[Dict]:
        """
        Extract action items from meeting/discussion text
        """
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying action items from discussions."},
                        {"role": "user", "content": f"""Extract all action items from this text.
For each action item identify:
1. The task
2. Who is responsible (if mentioned)
3. Deadline (if mentioned)
4. Priority (high/medium/low based on context)

Text: {text[:3000]}

Format as a numbered list with clear sections."""}
                    ],
                    temperature=0.2
                )
                
                content = response.choices[0].message.content
                action_items = []
                
                # Simple parsing of response
                items = content.split('\n\n')
                for item in items:
                    if item.strip():
                        action_items.append({
                            'task': item.strip(),
                            'priority': 'medium'  # Default
                        })
                
                return action_items
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
        
        return []
    
    def check_api_status(self) -> bool:
        """Check if OpenAI API is configured and working"""
        if not self.client:
            return False
        
        try:
            # Try a simple API call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True
        except:
            return False


# Convenience function to get the best available analyzer
def get_best_analyzer():
    """
    Returns OpenAI analyzer if API key is available, otherwise local analyzer
    """
    analyzer = OpenAIAnalyzer()
    
    if analyzer.client:
        return analyzer
    else:
        # Return local analyzer
        from analyzer import TextAnalyzer
        return TextAnalyzer()