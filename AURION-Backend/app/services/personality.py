"""
AURION Personality Engine - Makes responses friendly, smart, and natural
"""

import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class PersonalityEngine:
    """Manages AURION's personality traits and response styling"""
    
    def __init__(self):
        self.personality_traits = {
            "friendliness": 0.9,      # Very friendly
            "formality": 0.2,         # Very casual, not formal
            "enthusiasm": 0.7,        # Moderately enthusiastic
            "brevity": 0.9,           # Strongly prefer short responses
            "empathy": 0.85,          # Highly empathetic
            "humor": 0.6,             # Some humor, not overdone
        }
        logger.info("✅ PersonalityEngine initialized with friendly traits")
    
    def create_response_guidelines(self, user_profile: Dict) -> str:
        """Create personality-based response guidelines"""
        
        user_name = user_profile.get("name", "")
        interests = user_profile.get("interests", [])
        communication_style = user_profile.get("communication_style", "casual")
        
        guidelines = f"""**AURION's Personality Guidelines:**

🎭 **Your Character:**
- You're AURION - a warm, intelligent friend who genuinely cares
- You're helpful but never pushy or overly formal
- You remember everything about the user and show it naturally
- You're smart but explain things simply
- You have a subtle sense of humor

💬 **Communication Style (CRITICAL):**
- **KEEP IT SHORT** - 1-2 sentences max unless they ask for details
- **BE WARM** - Use friendly language, not robotic
- **SHOW MEMORY NATURALLY** - Don't say "I've made a note" or "based on what you told me"
- **STAY RELEVANT** - Answer directly, don't over-explain
- **BE NATURAL** - Talk like a helpful friend, not an AI assistant

✅ **DO SAY:**
- "Hey! 😊" not "Hello, how may I assist you today?"
- "You love sci-fi!" not "I have made a note that you are interested in science fiction"
- "NYC! 🗽" not "Based on what you told me, you live in NYC"
- Use: "Yeah!", "Sure!", "Got it!", "Exactly!"

❌ **NEVER SAY:**
- "I have made a note that..."
- "I will remember that for you..."
- "Based on what you told me..."
- "According to the information provided..."
- "It is wonderful to..."
- "I am here to assist you..."
- "Is there anything else I can help you with today?"
- Don't repeat the user's name in every sentence

📏 **Length Rules:**
- Greeting: 1 sentence ("Hey! 😊 How can I help?")
- Simple recall: 1-3 words ("NYC! 🗽" or "Alex! 😊")
- General knowledge: 1-2 sentences
- Complex topics: 2-3 sentences max, then offer more if needed

**User Context:**
- Name: {user_name or "Not yet shared"}
- Interests: {', '.join(interests[:3]) if interests else "Getting to know them"}
- Style: {communication_style}

**Remember:** Be like a smart friend who pays attention - not a formal AI reporting facts!"""

        return guidelines
    
    def optimize_response(self, response: str, query: str) -> str:
        """Optimize response for friendliness and brevity"""
        
        # First, apply friendly touches
        response = self.add_friendly_touches(response)
        
        # Then optimize length based on query type
        query_lower = query.lower()
        
        # Very short queries deserve very short answers
        if len(query.split()) <= 5:
            if any(word in query_lower for word in ["name", "where", "what", "who"]):
                # Extract just the answer for simple recall questions
                response = self._extract_core_answer(response, query_lower)
        
        # Limit length for all responses
        response = self.optimize_length(response, max_sentences=2)
        
        return response.strip()
    
    def _extract_core_answer(self, response: str, query: str) -> str:
        """Extract just the core answer for simple questions"""
        
        # For "what's my name?" type questions
        if "name" in query:
            # Look for "Your name is X" or "You're X" or just "X"
            name_match = re.search(r"(?:your name is|you'?re)\s+([A-Z][a-z]+)", response, re.IGNORECASE)
            if name_match:
                return f"Your name is {name_match.group(1)}! 😊"
            # Fallback: just find a capitalized name
            match = re.search(r"\b([A-Z][a-z]+)\b", response)
            if match:
                return f"{match.group(1)}! 😊"
        
        # For "where do I live?" type questions
        if "where" in query and "live" in query:
            # Look for location in context "you live in X" or "you're in X"
            cities = ["NYC", "New York", "San Francisco", "SF", "Los Angeles", "LA", "Chicago", "Boston", "Seattle", "Austin"]
            for city in cities:
                if city.lower() in response.lower():
                    emoji = "🗽" if "new york" in city.lower() or city == "NYC" else "📍"
                    # Check if "You live in" is already in the response
                    if "you live" in response.lower() or "you're in" in response.lower():
                        # Keep the context but shorten
                        return f"You live in {city}! {emoji}"
                    else:
                        return f"You live in {city}! {emoji}"
        
        # For "what do I like?" type questions
        if "like" in query or "love" in query or "favorite" in query:
            # Look for "you like X" or "you love X" or "your favorite is X"
            if "you like" in response.lower() or "you love" in response.lower():
                # Keep the personal context
                match = re.search(r"you (like|love)\s+([^.!?]+)", response, re.IGNORECASE)
                if match:
                    thing = match.group(2).strip()
                    return f"You {match.group(1)} {thing}! ✨"
            # Fallback: just the thing
            interests_match = re.search(r"(pizza|technology|music|sports|coding|ai|art|books|movies)", response, re.IGNORECASE)
            if interests_match:
                return f"You love {interests_match.group(0)}! ✨"
        
        return response
    
    def optimize_length(self, response: str, max_sentences: int = 2) -> str:
        """Keep responses concise"""
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', response.strip())
        
        # If already short enough, return as is
        if len(sentences) <= max_sentences:
            return response
        
        # Keep the most relevant sentences
        kept_sentences = sentences[:max_sentences]
        optimized = ' '.join(kept_sentences)
        
        # Ensure proper ending
        if not optimized.endswith(('.', '!', '?')):
            optimized += '.'
        
        return optimized
    
    def add_friendly_touches(self, response: str) -> str:
        """Add warmth and remove formal language while keeping personal context"""
        
        # Remove overly formal phrases (case-insensitive, with proper word boundaries)
        formal_replacements = {
            r"Based on what you (?:told me|mentioned|said)(?:,?\s+(?:previously|earlier|before))?,?\s*": "",
            r"Based on (?:our previous conversation|the information (?:you )?provided (?:to me)?),?\s*": "",
            r"According to (?:my records|your profile),?\s*you (?:mentioned that you\s+)?": "You ",
            r"According to (?:my records|your profile),?\s*": "",
            r"I have made a note that\s+you\s+": "You ",
            r"I have made a note that\s+": "",
            r"I will remember that for you\.?\s*": "Got it! ",
            r"I will certainly\s+": "I'll ",
            r"I am here to assist you\.?\s*": "",
            r"How may I assist you today\??\.?\s*": "How can I help? ",
            r"Is there anything else I can help you with (?:today)?\??\.?\s*": "",
            r"It is wonderful to\s+": "Great to ",
            r"Thank you for sharing that (?:information)?\.?\s*": "Thanks! ",
            r"I've made sure to remember that for you\.?\s*": "",
            r"I can (?:confirm|tell you) that\s+you\s+": "You ",
            r"I can (?:confirm|tell you) that\s+": "",
            r"You (?:also )?told me (?:that )?you\s+": "You ",
            r"you mentioned that you\s+": "you ",
            r"You said (?:that )?you\s+": "You ",
        }
        
        for pattern, replacement in formal_replacements.items():
            response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
        
        # Simplify language
        replacements = [
            ("approximately", "about"),
            ("currently", "now"),
            ("however", "but"),
            ("therefore", "so"),
            ("utilize", "use"),
            ("commence", "start"),
            ("in accordance with", "following"),
            ("as per", "per"),
        ]
        
        for old, new in replacements:
            response = response.replace(old, new)
            # Also check capitalized version
            response = response.replace(old.capitalize(), new.capitalize())
        
        # Remove excessive politeness
        response = re.sub(r"(?:please )?(?:don't hesitate to|feel free to)\s+", "", response, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        response = re.sub(r'\s+', ' ', response)
        response = re.sub(r'\s+([.!?,])', r'\1', response)
        response = re.sub(r'^[,\s]+', '', response)  # Remove leading commas/spaces
        
        # Capitalize first letter if not already
        if response and response[0].islower():
            response = response[0].upper() + response[1:]
        
        # Add contextual emojis
        response = self._add_contextual_emoji(response)
        
        return response.strip()
    
    def _add_contextual_emoji(self, response: str) -> str:
        """Add contextual emoji to response if appropriate"""
        
        # Skip if already has emoji
        if any(char in response for char in "😊🎬🗽📍✨🎨🚀💡🎯🎉🍕☀️🌧️⚡"):
            return response
        
        # Location-based emojis
        location_emojis = {
            r"\b(NYC|New York)\b": "🗽",
            r"\bSan Francisco\b": "🌉",
            r"\bLos Angeles\b": "🌴",
            r"\bChicago\b": "🏙️",
            r"\bSeattle\b": "☕",
            r"\bAustin\b": "🎸",
            r"\bBoston\b": "🦞",
        }
        
        for pattern, emoji in location_emojis.items():
            if re.search(pattern, response, re.IGNORECASE):
                # Add emoji to the location
                response = re.sub(pattern, r"\g<0> " + emoji, response, count=1, flags=re.IGNORECASE)
                return response
        
        # Food emojis
        food_emojis = {
            r"\bpizza\b": "🍕",
            r"\bcoffee\b": "☕",
            r"\bburger\b": "🍔",
            r"\bsushi\b": "🍣",
            r"\btaco\b": "🌮",
        }
        
        for pattern, emoji in food_emojis.items():
            if re.search(pattern, response, re.IGNORECASE):
                response = re.sub(pattern, r"\g<0> " + emoji, response, count=1, flags=re.IGNORECASE)
                return response
        
        # Weather emojis
        if "sunny" in response.lower() or "clear" in response.lower():
            response = response.rstrip('.!') + "! ☀️"
        elif "rain" in response.lower():
            response = response.rstrip('.!') + "! 🌧️"
        elif "cloud" in response.lower():
            response = response.rstrip('.!') + "! ☁️"
        
        return response
    
    def should_use_emoji(self, intent: str, response: str) -> bool:
        """Determine if response should include emoji"""
        
        # Already has emoji
        if any(char in response for char in "😊🎬🗽📍✨🎨🚀💡🎯🎉"):
            return False
        
        emoji_friendly = ["greeting", "creative", "casual", "recommendation", "factual"]
        return intent in emoji_friendly
    
    def add_appropriate_emoji(self, response: str, intent: str) -> str:
        """Add appropriate emoji to response if needed"""
        
        if not self.should_use_emoji(intent, response):
            return response
        
        # Add emoji based on content
        response_lower = response.lower()
        
        if intent == "greeting":
            if not any(e in response for e in ["😊", "👋", "✨"]):
                response = response.rstrip('.!?') + "! 😊"
        
        elif "movie" in response_lower or "film" in response_lower:
            response = response.rstrip('.!?') + "! 🎬"
        
        elif "nyc" in response_lower or "new york" in response_lower:
            response = response.replace("NYC", "NYC 🗽").replace("New York", "New York 🗽")
        
        return response


def extract_user_name(facts: List[str]) -> Optional[str]:
    """Extract user name from facts list"""
    for fact in facts:
        if "name" in fact.lower():
            # Try various patterns
            patterns = [
                r"name is (\w+)",
                r"i'm (\w+)",
                r"i am (\w+)",
                r"call me (\w+)",
                r"my name's (\w+)"
            ]
            for pattern in patterns:
                match = re.search(pattern, fact, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    return None


def extract_user_interests(facts: List[str]) -> List[str]:
    """Extract user interests from facts"""
    interests = []
    interest_keywords = ["love", "like", "enjoy", "passion", "interest", "hobby", "into"]
    
    for fact in facts:
        fact_lower = fact.lower()
        for keyword in interest_keywords:
            if keyword in fact_lower:
                # Extract text after keyword
                parts = fact.split(keyword, 1)
                if len(parts) > 1:
                    interest = parts[1].strip().strip('.,!?')
                    # Clean up common suffixes
                    interest = re.sub(r'\s+(movie|film|book|game)s?$', r' \1s', interest, flags=re.IGNORECASE)
                    if interest and len(interest) < 50:  # Reasonable length
                        interests.append(interest)
    
    return list(set(interests))[:5]  # Unique, top 5


def extract_user_location(facts: List[str]) -> Optional[str]:
    """Extract user location from facts"""
    for fact in facts:
        fact_lower = fact.lower()
        
        # Check for common location patterns
        if any(phrase in fact_lower for phrase in ["live in", "from", "based in", "located in"]):
            # Common city names
            cities = {
                "nyc": "NYC",
                "new york": "NYC",
                "san francisco": "San Francisco",
                "los angeles": "Los Angeles",
                "chicago": "Chicago",
                "boston": "Boston",
                "seattle": "Seattle",
                "austin": "Austin",
                "miami": "Miami",
                "denver": "Denver"
            }
            
            for city_pattern, city_name in cities.items():
                if city_pattern in fact_lower:
                    return city_name
            
            # Try to extract capitalized location
            match = re.search(r"(?:live in|from|based in|located in)\s+([A-Z][a-zA-Z\s]+?)(?:[,.]|$)", fact)
            if match:
                return match.group(1).strip()
    
    return None


# Export helper functions
__all__ = ['PersonalityEngine', 'extract_user_name', 'extract_user_interests', 'extract_user_location']
