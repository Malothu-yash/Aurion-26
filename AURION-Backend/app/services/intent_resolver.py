"""
Smart Intent Resolution - Decides when to answer vs. ask for clarification

This module analyzes:
1. What information we already have (confirmed context)
2. What the user just said (new parameters)
3. Whether they're confirming something ("yes", "correct")
4. If we have enough info to answer

Key Features:
- Merges context across multiple conversation turns
- Detects confirmation words ("yes", "ok", "correct")
- Determines if we have enough info to answer
- Provides specific clarifications when info is missing

Example Flow:
    User: "Find distance"
    → resolve_intent() → action="clarify", should_answer=False
    
    User: "From Mumbai to Delhi"
    → resolve_intent() → action="answer", should_answer=True (has both locations!)
"""

import logging
from typing import Dict, Optional, Tuple, List
import re

logger = logging.getLogger(__name__)

class IntentResolver:
    """Resolves user intents and determines if we have enough info to answer"""
    
    def __init__(self, state_manager):
        """
        Initialize the intent resolver
        
        Args:
            state_manager: ConversationStateManager instance for context tracking
        """
        self.state_manager = state_manager
        logger.info("✅ IntentResolver initialized")
    
    async def resolve_intent(
        self, 
        query: str, 
        intent: str, 
        parameters: Dict,
        conversation_id: str
    ) -> Tuple[str, Dict, bool]:
        """
        Resolve intent and determine action
        
        This is the main decision function that decides:
        - Should we answer now?
        - Do we need to ask for clarification?
        - What information do we have?
        
        Args:
            query: User's current query
            intent: Classified intent (e.g., "informational_search", "travel")
            parameters: Parameters extracted from current query
            conversation_id: Unique conversation identifier
            
        Returns:
            Tuple of (action, complete_params, should_answer_now)
            - action: "answer" | "clarify" | "search"
            - complete_params: All gathered parameters (old + new)
            - should_answer_now: True if we have enough info to answer
        """
        
        # Get existing confirmed context
        confirmed = await self.state_manager.get_confirmed_context(conversation_id)
        
        # Check if this is a confirmation word
        is_confirmation = self._is_confirmation(query)
        
        logger.info(f"🔍 Resolving: intent={intent}, confirmed={confirmed}, is_confirmation={is_confirmation}")
        
        # Route to specific intent resolver
        if intent == "informational_search" or "distance" in query.lower():
            return await self._resolve_search_intent(
                query, parameters, confirmed, is_confirmation, conversation_id
            )
        
        elif intent == "travel":
            return await self._resolve_travel_intent(
                query, parameters, confirmed, is_confirmation, conversation_id
            )
        
        elif intent == "question":
            return await self._resolve_question_intent(
                query, parameters, confirmed, is_confirmation, conversation_id
            )
        
        # Default: answer if we have parameters or confirmed context
        if confirmed or parameters:
            return "answer", parameters or confirmed, True
        else:
            return "clarify", {}, False
    
    async def _resolve_search_intent(
        self, query, parameters, confirmed, is_confirmation, conversation_id
    ):
        """
        Resolve search/distance/location queries
        
        For distance queries we need: origin, destination
        Optional: transport_mode
        """
        
        # Required fields for distance queries
        required = ["origin", "destination"]
        
        # Merge confirmed context with new parameters
        complete_params = {**(confirmed or {}), **parameters}
        
        # Extract locations from query if present
        complete_params = self._extract_locations_from_query(query, complete_params)
        
        # Extract transport mode if mentioned
        complete_params = self._extract_transport_mode(query, complete_params)
        
        # Save updated context
        if complete_params != confirmed:
            await self.state_manager.update_confirmed_context(conversation_id, complete_params)
        
        # Check if we have all required info
        has_complete_info = all(complete_params.get(field) for field in required)
        
        if has_complete_info:
            logger.info(f"✅ Complete info for search: {complete_params}")
            return "answer", complete_params, True
        
        # If user confirmed but info incomplete, be specific about what's missing
        if is_confirmation and confirmed:
            missing = [f for f in required if not complete_params.get(f)]
            complete_params["missing_fields"] = missing
            logger.info(f"❌ User confirmed but missing: {missing}")
            return "clarify", complete_params, False
        
        # First time asking or still gathering info
        logger.info(f"📝 Need more info. Current: {complete_params}")
        return "clarify", complete_params, False
    
    async def _resolve_travel_intent(
        self, query, parameters, confirmed, is_confirmation, conversation_id
    ):
        """
        Resolve travel-related queries
        
        For travel we typically need: origin, destination, transport_mode
        """
        
        # Merge contexts
        complete_params = {**(confirmed or {}), **parameters}
        
        # Extract locations
        complete_params = self._extract_locations_from_query(query, complete_params)
        
        # Extract transport mode
        complete_params = self._extract_transport_mode(query, complete_params)
        
        # Save context
        if complete_params != confirmed:
            await self.state_manager.update_confirmed_context(conversation_id, complete_params)
        
        # If we have origin, destination, and mode - answer!
        required = ["origin", "destination"]
        has_complete_info = all(complete_params.get(f) for f in required)
        
        if has_complete_info:
            logger.info(f"✅ Complete travel info: {complete_params}")
            return "answer", complete_params, True
        
        # Need more info
        logger.info(f"📝 Incomplete travel info: {complete_params}")
        return "clarify", complete_params, False
    
    async def _resolve_question_intent(
        self, query, parameters, confirmed, is_confirmation, conversation_id
    ):
        """
        Resolve general questions
        
        Most questions can be answered immediately unless they need context
        """
        
        # Merge contexts
        complete_params = {**(confirmed or {}), **parameters}
        
        # Questions usually don't need context gathering
        # But if there's confirmed context, use it
        if confirmed:
            await self.state_manager.update_confirmed_context(conversation_id, complete_params)
            return "answer", complete_params, True
        
        # New question - answer directly
        return "answer", complete_params, True
    
    def _extract_locations_from_query(self, query: str, params: Dict) -> Dict:
        """
        Extract origin and destination from query text
        
        Patterns:
        - "from X to Y"
        - "X to Y"
        - "between X and Y"
        """
        
        query_lower = query.lower()
        
        # Pattern 1: "from X to Y"
        from_to_pattern = r'from\s+([^to]+?)\s+to\s+(.+?)(?:\s+by|\s+in|\s+via|$)'
        match = re.search(from_to_pattern, query_lower, re.IGNORECASE)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            params["origin"] = origin.title()
            params["destination"] = destination.title()
            logger.info(f"📍 Extracted: {origin} → {destination}")
            return params
        
        # Pattern 2: "X to Y" (without "from")
        to_pattern = r'([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+by|\s+in|\s+via|distance|$)'
        match = re.search(to_pattern, query_lower, re.IGNORECASE)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            # Filter out common words
            if origin not in ['want', 'need', 'like', 'going', 'travel', 'distance']:
                params["origin"] = origin.title()
                params["destination"] = destination.title()
                logger.info(f"📍 Extracted: {origin} → {destination}")
                return params
        
        # Pattern 3: "between X and Y"
        between_pattern = r'between\s+([^and]+?)\s+and\s+(.+?)(?:\s+by|\s+in|$)'
        match = re.search(between_pattern, query_lower, re.IGNORECASE)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            params["origin"] = origin.title()
            params["destination"] = destination.title()
            logger.info(f"📍 Extracted: {origin} → {destination}")
        
        return params
    
    def _extract_transport_mode(self, query: str, params: Dict) -> Dict:
        """
        Extract transport mode from query
        
        Supported modes: bus, train, flight, car, driving, walking
        """
        
        query_lower = query.lower()
        
        transport_keywords = {
            "bus": ["bus", "buses"],
            "train": ["train", "railway", "rail"],
            "flight": ["flight", "fly", "flying", "plane", "air"],
            "car": ["car", "drive", "driving"],
            "walking": ["walk", "walking", "foot"]
        }
        
        for mode, keywords in transport_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    params["transport_mode"] = mode
                    logger.info(f"🚌 Detected transport mode: {mode}")
                    return params
        
        # Default to driving if not specified
        if "transport_mode" not in params and params.get("origin") and params.get("destination"):
            params["transport_mode"] = "driving"
        
        return params
    
    def _is_confirmation(self, query: str) -> bool:
        """
        Check if query is a confirmation word
        
        Confirmation words: yes, yeah, ok, sure, correct, right, etc.
        """
        
        confirmations = [
            "yes", "yeah", "yep", "yup", "sure", "correct", "right",
            "ok", "okay", "fine", "go ahead", "please", "exactly",
            "that's right", "absolutely", "definitely", "affirmative"
        ]
        
        query_lower = query.lower().strip()
        
        # Exact match
        if query_lower in confirmations:
            logger.info(f"✅ Confirmation detected: '{query}'")
            return True
        
        # Starts with confirmation
        for conf in confirmations:
            if query_lower.startswith(conf):
                logger.info(f"✅ Confirmation detected: '{query}'")
                return True
        
        return False
    
    async def get_missing_fields_message(
        self, 
        conversation_id: str, 
        required_fields: List[str]
    ) -> str:
        """
        Generate a specific clarification message for missing fields
        
        Args:
            conversation_id: Unique conversation identifier
            required_fields: List of required field names
            
        Returns:
            A natural clarification question
        """
        
        context = await self.state_manager.get_confirmed_context(conversation_id)
        missing = [f for f in required_fields if not (context and context.get(f))]
        
        if not missing:
            return ""
        
        # Generate specific questions for missing fields
        if "origin" in missing and "destination" in missing:
            return "From where to where?"
        elif "origin" in missing:
            return "Where are you starting from?"
        elif "destination" in missing:
            return "Where do you want to go?"
        elif "transport_mode" in missing:
            return "How do you plan to travel? (bus, train, flight, or car?)"
        elif "date" in missing:
            return "When are you planning to travel?"
        else:
            return f"Could you provide the {missing[0]}?"
