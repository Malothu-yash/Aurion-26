"""
Advanced Personalization Engine for AURION
Learns user preferences and adapts responses
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PersonalizationEngine:
    """Manages user personalization and preference learning"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        logger.info("✅ PersonalizationEngine initialized")
    
    async def build_user_profile(self, user_id: str) -> Dict:
        """Build comprehensive user profile from Redis"""
        
        profile = {
            "user_id": user_id,
            "preferences": {},
            "interaction_patterns": {},
            "interests": [],
            "communication_style": "casual",
            "active_contexts": [],
            "total_interactions": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            # Get stored profile from Redis
            redis_key = f"user_profile:{user_id}"
            stored_profile = await self.redis.get(redis_key)
            
            if stored_profile:
                stored_data = json.loads(stored_profile)
                profile.update(stored_data)
                logger.info(f"✅ Loaded profile for {user_id}: {len(profile.get('interests', []))} interests")
            else:
                logger.info(f"📝 Creating new profile for {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Profile building error: {str(e)}")
        
        return profile
    
    async def update_profile(
        self,
        user_id: str,
        query: str,
        response: str,
        extracted_facts: List[str] = None
    ):
        """Update user profile based on interaction"""
        
        try:
            profile = await self.build_user_profile(user_id)
            
            # Update interaction count
            profile["total_interactions"] = profile.get("total_interactions", 0) + 1
            
            # Detect and update communication style
            query_length = len(query.split())
            if query_length > 30:
                profile["communication_style"] = "detailed"
            elif any(word in query.lower() for word in ["please", "thank", "appreciate"]):
                profile["communication_style"] = "polite"
            elif query_length < 5:
                profile["communication_style"] = "brief"
            
            # Extract and store interests from facts
            if extracted_facts:
                for fact in extracted_facts:
                    if "likes" in fact.lower() or "love" in fact.lower() or "interest" in fact.lower():
                        # Extract the interest
                        interest = fact.split(":")[-1].strip() if ":" in fact else fact
                        if interest not in profile["interests"]:
                            profile["interests"].append(interest)
            
            # Detect active context/topic
            context = self._detect_context(query)
            if context:
                if context not in profile["active_contexts"]:
                    profile["active_contexts"].insert(0, context)
                # Keep only last 5 contexts
                profile["active_contexts"] = profile["active_contexts"][:5]
            
            # Update timestamp
            profile["last_updated"] = datetime.now().isoformat()
            
            # Save to Redis (30 day expiry)
            redis_key = f"user_profile:{user_id}"
            await self.redis.setex(
                redis_key,
                86400 * 30,  # 30 days
                json.dumps(profile)
            )
            
            logger.info(f"✅ Updated profile for {user_id} - Style: {profile['communication_style']}, Contexts: {profile['active_contexts'][:3]}")
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Profile update error: {str(e)}")
            return None
    
    def _detect_context(self, query: str) -> Optional[str]:
        """Detect current conversation context/topic"""
        query_lower = query.lower()
        
        contexts = {
            "programming": ["code", "python", "javascript", "programming", "debug", "error", "function", "variable"],
            "science": ["physics", "chemistry", "biology", "scientific", "theory", "research"],
            "business": ["business", "startup", "company", "market", "strategy", "entrepreneur"],
            "creative": ["story", "poem", "creative", "art", "design", "write", "create"],
            "personal": ["my", "i feel", "i think", "i need", "help me", "i want"],
            "learning": ["learn", "understand", "explain", "teach", "how to", "what is"],
            "entertainment": ["movie", "music", "game", "video", "watch", "play"],
            "health": ["health", "fitness", "exercise", "diet", "wellness"],
            "travel": ["travel", "trip", "vacation", "visit", "explore"],
            "finance": ["money", "investment", "finance", "savings", "budget"],
        }
        
        for context, keywords in contexts.items():
            if any(keyword in query_lower for keyword in keywords):
                return context
        
        return None
    
    async def get_personalization_hints(self, user_id: str) -> str:
        """Get personalization hints for response generation"""
        
        profile = await self.build_user_profile(user_id)
        
        hints = []
        
        # Communication style hint
        style = profile.get("communication_style", "casual")
        if style == "detailed":
            hints.append("Provide detailed explanations")
        elif style == "brief":
            hints.append("Keep responses concise")
        elif style == "polite":
            hints.append("Maintain formal, polite tone")
        
        # Interest hints
        interests = profile.get("interests", [])
        if interests:
            hints.append(f"User is interested in: {', '.join(interests[:5])}")
        
        # Context hints
        contexts = profile.get("active_contexts", [])
        if contexts:
            hints.append(f"Recent topics: {', '.join(contexts[:3])}")
        
        return " | ".join(hints) if hints else "No personalization data yet"
    
    async def clear_user_profile(self, user_id: str):
        """Clear user profile (for privacy/reset)"""
        try:
            redis_key = f"user_profile:{user_id}"
            await self.redis.delete(redis_key)
            logger.info(f"✅ Cleared profile for {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Profile clear error: {str(e)}")
            return False
