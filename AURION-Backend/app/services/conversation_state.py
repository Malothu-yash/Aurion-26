"""
Conversation State Manager - Tracks ongoing conversation topics for natural flow

This module enables AURION to:
- Remember the last conversation topic
- Detect follow-up questions
- Maintain context across multiple turns
- Handle incomplete queries naturally

Example:
    User: "Who founded Google?"
    AI: "Larry Page and Sergey Brin founded Google."
    User: "What about Microsoft?"
    AI: (Knows this is a follow-up about founders) "Bill Gates and Paul Allen founded Microsoft."
"""

import redis.asyncio as redis
from typing import Optional, Dict, List
import json
import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationStateManager:
    """Manages conversation state for natural context flow"""
    
    def __init__(self, redis_pool):
        """
        Initialize with Redis connection pool
        Args:
            redis_pool: Redis ConnectionPool object
        """
        self.redis_pool = redis_pool
        logger.info("✅ ConversationStateManager initialized")
    
    async def save_last_topic(
        self, 
        conversation_id: str, 
        topic: str, 
        entities: Dict = None,
        query: str = None,
        response_preview: str = None
    ):
        """
        Save the current conversation topic and context
        
        Args:
            conversation_id: Unique conversation identifier
            topic: Main topic being discussed (e.g., "company founders", "distance calculation")
            entities: Key entities mentioned (e.g., {"company": "Google", "founders": ["Larry", "Sergey"]})
            query: Original user query
            response_preview: First 200 chars of response for context
        """
        state = {
            "topic": topic,
            "entities": entities or {},
            "query": query,
            "response_preview": response_preview[:200] if response_preview else None,
            "timestamp": datetime.datetime.now().isoformat()
        }
        key = f"conversation_state:{conversation_id}"
        
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.set(key, json.dumps(state), ex=3600)  # 1 hour TTL
            logger.info(f"✅ Saved conversation state: {topic}")
        except Exception as e:
            logger.error(f"Error saving conversation state: {e}")
    
    async def get_last_topic(self, conversation_id: str) -> Optional[Dict]:
        """
        Get the last conversation topic and context
        
        Returns:
            Dict with topic, entities, query, response_preview, timestamp
            None if no previous state exists
        """
        key = f"conversation_state:{conversation_id}"
        
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                data = await r.get(key)
            if data:
                state = json.loads(data)
                logger.info(f"📖 Retrieved conversation state: {state.get('topic')}")
                return state
            return None
        except Exception as e:
            logger.error(f"Error getting conversation state: {e}")
            return None
    
    async def detect_follow_up(self, query: str, last_topic: Dict = None) -> Dict:
        """
        Detect if query is a follow-up to previous conversation
        
        Returns:
            Dict with:
                - is_follow_up: bool
                - confidence: float (0.0-1.0)
                - reason: str (why it's considered a follow-up)
        """
        query_lower = query.lower().strip()
        
        # Strong follow-up indicators
        strong_follow_up_patterns = [
            r"^what about\s+",
            r"^how about\s+",
            r"^and\s+\w+",
            r"^also\s+",
            r"^can\s+i\s+",
            r"^should\s+i\s+",
            r"^will\s+it\s+",
            r"^does\s+it\s+",
            r"^is\s+it\s+",
        ]
        
        # Medium follow-up indicators
        medium_follow_up_patterns = [
            r"^yes\b",
            r"^no\b",
            r"^ok\b",
            r"^okay\b",
            r"^sure\b",
            r"^thanks\b",
            r"^got\s+it\b",
            r"^more\b",
            r"^another\b",
            r"^different\b",
            r"^similar\b",
            r"^same\b",
        ]
        
        # Weak indicators
        weak_indicators = [
            "that",
            "this",
            "it",
            "there",
        ]
        
        # Check strong patterns
        import re
        for pattern in strong_follow_up_patterns:
            if re.match(pattern, query_lower):
                return {
                    "is_follow_up": True,
                    "confidence": 0.95,
                    "reason": f"Strong follow-up pattern: {pattern}"
                }
        
        # Check medium patterns
        for pattern in medium_follow_up_patterns:
            if re.match(pattern, query_lower):
                return {
                    "is_follow_up": True,
                    "confidence": 0.75,
                    "reason": f"Medium follow-up pattern: {pattern}"
                }
        
        # Check if query is very short (likely continuation)
        word_count = len(query.split())
        if word_count <= 3 and last_topic:
            # Check if it contains weak indicators
            if any(indicator in query_lower for indicator in weak_indicators):
                return {
                    "is_follow_up": True,
                    "confidence": 0.60,
                    "reason": "Short query with contextual words"
                }
            
            # Just short query
            return {
                "is_follow_up": True,
                "confidence": 0.50,
                "reason": "Very short query (likely incomplete)"
            }
        
        # Check if query references entities from last topic
        if last_topic and last_topic.get("entities"):
            entities = last_topic["entities"]
            for key, value in entities.items():
                if isinstance(value, str) and value.lower() in query_lower:
                    return {
                        "is_follow_up": True,
                        "confidence": 0.70,
                        "reason": f"References entity from last topic: {value}"
                    }
        
        # Not a follow-up
        return {
            "is_follow_up": False,
            "confidence": 0.0,
            "reason": "Complete standalone query"
        }
    
    async def expand_follow_up_query(
        self, 
        query: str, 
        last_topic: Dict
    ) -> str:
        """
        Expand incomplete follow-up query with context from last topic
        
        Example:
            Last topic: "Google founders"
            Query: "What about Microsoft?"
            Expanded: "Who founded Microsoft?" (maintaining the pattern)
        """
        query_lower = query.lower()
        
        # Pattern: "What about X?"
        if query_lower.startswith("what about"):
            topic = last_topic.get("topic", "")
            new_entity = query.replace("what about", "").replace("?", "").strip()
            
            # If last topic was about founders, maintain that pattern
            if "founder" in topic.lower():
                return f"Who founded {new_entity}?"
            elif "distance" in topic.lower():
                return f"What is the distance to {new_entity}?"
            else:
                return f"Tell me about {new_entity}"
        
        # Pattern: "How about X?"
        elif query_lower.startswith("how about"):
            new_entity = query.replace("how about", "").replace("?", "").strip()
            return f"How about {new_entity}? {last_topic.get('topic', '')}"
        
        # Pattern: Single word or phrase (likely a choice)
        elif len(query.split()) <= 2:
            last_query = last_topic.get("query", "")
            # If last query asked for a choice, this is likely the answer
            if "?" in last_query and any(word in last_query.lower() for word in ["or", "want", "prefer", "choose"]):
                return f"{query} (continuing from: {last_query})"
            return f"{query} related to {last_topic.get('topic', '')}"
        
        # Pattern: Affirmative/Negative responses
        elif query_lower in ["yes", "no", "ok", "okay", "sure", "nope"]:
            last_query = last_topic.get("query", "")
            return f"{query} to: {last_query}"
        
        # Default: append context
        return f"{query} (context: {last_topic.get('topic', '')})"
    
    async def clear_state(self, conversation_id: str):
        """Clear conversation state (useful for 'start fresh' commands)"""
        key = f"conversation_state:{conversation_id}"
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.delete(key)
            logger.info(f"✅ Cleared conversation state for {conversation_id}")
        except Exception as e:
            logger.error(f"Error clearing conversation state: {e}")
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get recent conversation history with state markers
        
        Returns list of messages with state transitions marked
        """
        # This could integrate with existing Redis chat history
        # For now, returns the current state
        state = await self.get_last_topic(conversation_id)
        if state:
            return [{
                "role": "system",
                "content": f"Current topic: {state.get('topic')}",
                "state": state
            }]
        return []
    
    async def save_confirmed_context(self, conversation_id: str, context: Dict):
        """
        Save confirmed user intent with all required parameters
        
        This tracks information the user has explicitly provided across multiple turns.
        Example: origin="Mumbai", destination="Delhi", transport_mode="bus"
        
        Args:
            conversation_id: Unique conversation identifier
            context: Dict of confirmed parameters (e.g., {"origin": "Mumbai", "destination": "Delhi"})
        """
        key = f"confirmed_context:{conversation_id}"
        try:
            context["last_updated"] = datetime.datetime.now().isoformat()
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.set(key, json.dumps(context), ex=1800)  # 30 min TTL
            logger.info(f"✅ Saved confirmed context: {context}")
        except Exception as e:
            logger.error(f"Error saving confirmed context: {e}")
    
    async def get_confirmed_context(self, conversation_id: str) -> Optional[Dict]:
        """
        Get confirmed user context from previous turns
        
        Returns:
            Dict of confirmed parameters or None
        """
        key = f"confirmed_context:{conversation_id}"
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                data = await r.get(key)
            if data:
                context = json.loads(data)
                logger.info(f"📋 Retrieved confirmed context: {list(context.keys())}")
                return context
            return None
        except Exception as e:
            logger.error(f"Error getting confirmed context: {e}")
            return None
    
    async def update_confirmed_context(self, conversation_id: str, updates: Dict):
        """
        Update specific fields in confirmed context without replacing everything
        
        Args:
            conversation_id: Unique conversation identifier
            updates: Dict of fields to update/add
        """
        existing = await self.get_confirmed_context(conversation_id)
        if existing:
            existing.update(updates)
            await self.save_confirmed_context(conversation_id, existing)
            logger.info(f"🔄 Updated context with: {list(updates.keys())}")
        else:
            # No existing context, save as new
            await self.save_confirmed_context(conversation_id, updates)
    
    async def is_context_complete(self, conversation_id: str, required_fields: List[str]) -> bool:
        """
        Check if all required context fields have been gathered
        
        Args:
            conversation_id: Unique conversation identifier
            required_fields: List of required field names
            
        Returns:
            True if all required fields are present and non-empty
        """
        context = await self.get_confirmed_context(conversation_id)
        if not context:
            return False
        
        # Check each required field
        for field in required_fields:
            if field not in context or not context[field]:
                logger.info(f"❌ Missing required field: {field}")
                return False
        
        logger.info(f"✅ Context complete: {required_fields}")
        return True
    
    async def clear_confirmed_context(self, conversation_id: str):
        """Clear confirmed context (useful when starting a new topic)"""
        key = f"confirmed_context:{conversation_id}"
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.delete(key)
            logger.info(f"🗑️ Cleared confirmed context")
        except Exception as e:
            logger.error(f"Error clearing confirmed context: {e}")
    
    # ==================== TASK CONFIRMATION METHODS ====================
    
    async def save_pending_task(self, conversation_id: str, task_details: Dict):
        """Save a task that's waiting for user confirmation"""
        key = f"pending_task:{conversation_id}"
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.set(key, json.dumps(task_details), ex=300)  # 5 min TTL
            logger.info(f"✅ Saved pending task: {task_details.get('description', 'Unknown')[:50]}")
        except Exception as e:
            logger.error(f"Error saving pending task: {e}")
    
    async def get_pending_task(self, conversation_id: str) -> Optional[Dict]:
        """Get a task waiting for confirmation"""
        key = f"pending_task:{conversation_id}"
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                data = await r.get(key)
            if data:
                task = json.loads(data)
                logger.info(f"✅ Found pending task: {task.get('description', 'Unknown')[:50]}")
                return task
            return None
        except Exception as e:
            logger.error(f"Error getting pending task: {e}")
            return None
    
    async def clear_pending_task(self, conversation_id: str):
        """Clear pending task after confirmation or timeout"""
        key = f"pending_task:{conversation_id}"
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                await r.delete(key)
            logger.info(f"✅ Cleared pending task for {conversation_id}")
        except Exception as e:
            logger.error(f"Error clearing pending task: {e}")
    
    def is_confirmation_phrase(self, query: str) -> bool:
        """
        Detect if user is confirming something
        Understands ANY way user might say "yes"
        """
        query_lower = query.lower().strip()
        
        # Direct confirmations
        direct = [
            "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "fine",
            "correct", "right", "exactly", "perfect", "absolutely",
            "go ahead", "proceed", "please", "do it", "yes please"
        ]
        
        # Action confirmations
        actions = [
            "create it", "make it", "set it", "do it", "schedule it",
            "add it", "confirm", "please do", "go for it", "create",
            "make", "set", "schedule", "add", "save it", "book it"
        ]
        
        # Positive phrases
        positive = [
            "sounds good", "looks good", "that's right", "that's correct",
            "all good", "perfect timing", "that works", "works for me",
            "good", "great", "awesome", "nice"
        ]
        
        # Check direct matches (exact or close)
        if query_lower in direct:
            logger.info(f"✅ Detected direct confirmation: '{query_lower}'")
            return True
        
        # Check if query contains action phrases
        for action in actions:
            if action in query_lower:
                logger.info(f"✅ Detected action confirmation: '{action}'")
                return True
        
        # Check if query contains positive phrases
        for phrase in positive:
            if phrase in query_lower:
                logger.info(f"✅ Detected positive confirmation: '{phrase}'")
                return True
        
        return False
    
    def is_rejection_phrase(self, query: str) -> bool:
        """Detect if user is rejecting/canceling"""
        query_lower = query.lower().strip()
        
        rejections = [
            "no", "nope", "nah", "cancel", "stop", "never mind", "nevermind",
            "don't", "not now", "later", "forget it", "skip", "abort",
            "no thanks", "not really", "changed my mind", "not interested"
        ]
        
        result = any(reject in query_lower for reject in rejections)
        if result:
            logger.info(f"❌ Detected rejection: '{query_lower}'")
        return result
