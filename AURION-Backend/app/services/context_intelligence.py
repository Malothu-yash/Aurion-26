# app/services/context_intelligence.py
"""
Context Intelligence - Makes AI understand conversation flow
Handles multi-turn conversations, clarifications, and context retention
Remembers what user said before and merges with current query
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ContextIntelligence:
    """
    Manages conversation context to make AI responses more intelligent
    Tracks: user intent history, clarifications, pending actions, extracted entities
    """
    
    def __init__(self):
        # In-memory context store (can be moved to Redis for production)
        self.context_store: Dict[str, Dict[str, Any]] = {}
        logger.info("✅ ContextIntelligence initialized")
    
    def get_context(self, conv_id: str) -> Dict[str, Any]:
        """Get conversation context"""
        return self.context_store.get(conv_id, {
            'pending_clarification': None,
            'last_intent': None,
            'extracted_entities': {},
            'conversation_topic': None,
            'last_query': None,
            'last_response': None,
            'query_history': [],
            'created_at': datetime.now(timezone.utc).isoformat()
        })
    
    def update_context(self, conv_id: str, updates: Dict[str, Any]):
        """Update conversation context"""
        context = self.get_context(conv_id)
        context.update(updates)
        context['updated_at'] = datetime.now(timezone.utc).isoformat()
        self.context_store[conv_id] = context
        logger.debug(f"📝 Context updated for {conv_id}")
    
    def clear_context(self, conv_id: str):
        """Clear conversation context"""
        if conv_id in self.context_store:
            del self.context_store[conv_id]
            logger.info(f"🗑️ Context cleared for {conv_id}")
    
    def is_followup_query(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Determine if current query is a follow-up to previous conversation
        Examples:
        - User: "weather Mumbai" → Bot: "..." → User: "and temperature?" ✓ Follow-up
        - User: "restaurants" → Bot: "Where?" → User: "Hyderabad" ✓ Follow-up
        """
        
        # If there's a pending clarification, this is definitely a follow-up
        if context.get('pending_clarification'):
            return True
        
        # Check if query is very short (likely answering a question)
        if len(query.split()) <= 2 and context.get('last_query'):
            return True
        
        # Check for follow-up keywords
        followup_patterns = [
            'and ', 'also ', 'what about ', 'how about ',
            'there', 'that', 'it', 'yes', 'no', 'ok', 'sure'
        ]
        
        query_lower = query.lower()
        if any(query_lower.startswith(pattern) for pattern in followup_patterns):
            return True
        
        return False
    
    def extract_entities(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from query using context
        Entities: location, time, person, place, etc.
        Uses previous context to fill in missing information
        """
        entities = {}
        query_lower = query.lower()
        
        # Location extraction
        location = self._extract_location(query_lower, context)
        if location:
            entities['location'] = location
        
        # Time extraction
        time_info = self._extract_time(query_lower)
        if time_info:
            entities['time'] = time_info
        
        # Category extraction (for local search)
        category = self._extract_category(query_lower)
        if category:
            entities['category'] = category
        
        return entities
    
    def merge_with_context(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Merge current query with conversation context
        
        Examples:
        1. User: "restaurants" → Bot: "Where?" → User: "hyd"
           Merged: "restaurants in Hyderabad"
        
        2. User: "weather" → Bot: "Which city?" → User: "Mumbai"
           Merged: "weather in Mumbai"
        
        3. User: "weather Mumbai" → Bot: "..." → User: "what about Delhi?"
           Merged: "weather in Delhi"
        """
        
        # If user is answering a clarification
        if context.get('pending_clarification'):
            clarification = context['pending_clarification']
            clarification_type = clarification.get('type')
            original_query = clarification.get('original_query', '')
            
            if clarification_type == 'location':
                # User provided location
                location = self._extract_location(query.lower(), context)
                if not location:
                    # Treat entire query as location
                    location = query.strip()
                
                # Expand common abbreviations
                location = self._expand_location(location)
                
                # Reconstruct full query
                merged = f"{original_query} in {location}"
                logger.info(f"🔄 Merged clarification: '{query}' + context → '{merged}'")
                return merged
            
            elif clarification_type == 'details':
                # User provided more details
                merged = f"{original_query} {query}"
                logger.info(f"🔄 Merged details: '{query}' + context → '{merged}'")
                return merged
        
        # If query references previous topic
        if self.is_followup_query(query, context):
            last_query = context.get('last_query', '')
            
            # Extract new subject from follow-up
            # Example: "what about Delhi?" → extract "Delhi"
            if 'what about' in query.lower():
                new_subject = query.lower().replace('what about', '').strip().rstrip('?')
                if new_subject and last_query:
                    # Replace old subject with new one
                    # Simple approach: replace location
                    merged = last_query
                    old_location = context.get('extracted_entities', {}).get('location')
                    if old_location:
                        merged = merged.replace(old_location.lower(), new_subject)
                    else:
                        merged = f"{last_query.split()[0]} {new_subject}"
                    
                    logger.info(f"🔄 Merged follow-up: '{query}' + context → '{merged}'")
                    return merged
        
        return query
    
    def _extract_location(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract location from query or context"""
        
        # Check for explicit location markers
        if ' in ' in query:
            parts = query.split(' in ')
            if len(parts) > 1:
                location = parts[1].strip()
                return self._expand_location(location)
        
        if ' at ' in query:
            parts = query.split(' at ')
            if len(parts) > 1:
                location = parts[1].strip()
                return self._expand_location(location)
        
        # Check for city names or abbreviations
        location = self._find_city_in_query(query)
        if location:
            return location
        
        # Check previous context
        prev_location = context.get('extracted_entities', {}).get('location')
        if prev_location:
            logger.debug(f"📍 Using location from context: {prev_location}")
            return prev_location
        
        return None
    
    def _extract_time(self, query: str) -> Optional[str]:
        """Extract time information"""
        time_keywords = {
            'tomorrow': 'tomorrow',
            'today': 'today',
            'tonight': 'tonight',
            'morning': 'morning',
            'evening': 'evening',
            'afternoon': 'afternoon',
            'now': 'now',
            'later': 'later'
        }
        
        for keyword, value in time_keywords.items():
            if keyword in query:
                return value
        
        return None
    
    def _extract_category(self, query: str) -> Optional[str]:
        """Extract category for local search"""
        categories = {
            'restaurant': ['restaurant', 'food', 'eat', 'dining', 'cafe'],
            'hotel': ['hotel', 'stay', 'accommodation'],
            'shopping': ['shop', 'mall', 'store', 'market'],
            'hospital': ['hospital', 'clinic', 'doctor', 'medical'],
            'movie': ['movie', 'cinema', 'theater', 'film'],
            'gym': ['gym', 'fitness', 'workout'],
            'park': ['park', 'garden']
        }
        
        for category, keywords in categories.items():
            if any(keyword in query for keyword in keywords):
                return category
        
        return None
    
    def _expand_location(self, location: str) -> str:
        """Expand location abbreviations to full names"""
        location_lower = location.lower().strip()
        
        # Common abbreviations
        expansions = {
            'hyd': 'Hyderabad',
            'blr': 'Bangalore',
            'blore': 'Bangalore',
            'mum': 'Mumbai',
            'del': 'Delhi',
            'chn': 'Chennai',
            'kol': 'Kolkata',
            'pune': 'Pune',
            'narayanaguda': 'Narayanaguda, Hyderabad',
            'banjara hills': 'Banjara Hills, Hyderabad',
            'hitech city': 'Hitech City, Hyderabad',
            'koramangala': 'Koramangala, Bangalore',
            'whitefield': 'Whitefield, Bangalore'
        }
        
        # Check if it's a known abbreviation
        if location_lower in expansions:
            return expansions[location_lower]
        
        # Capitalize properly
        return location.title()
    
    def _find_city_in_query(self, query: str) -> Optional[str]:
        """Find city names in query"""
        # List of major cities
        cities = {
            'mumbai': 'Mumbai',
            'delhi': 'Delhi',
            'bangalore': 'Bangalore',
            'bengaluru': 'Bangalore',
            'hyderabad': 'Hyderabad',
            'chennai': 'Chennai',
            'kolkata': 'Kolkata',
            'pune': 'Pune',
            'ahmedabad': 'Ahmedabad',
            'jaipur': 'Jaipur',
            'surat': 'Surat',
            'lucknow': 'Lucknow',
            'kanpur': 'Kanpur',
            'nagpur': 'Nagpur',
            'indore': 'Indore',
            'thane': 'Thane',
            'bhopal': 'Bhopal',
            'visakhapatnam': 'Visakhapatnam',
            'pimpri': 'Pimpri-Chinchwad',
            'patna': 'Patna',
            'vadodara': 'Vadodara',
            'ghaziabad': 'Ghaziabad',
            'ludhiana': 'Ludhiana'
        }
        
        # Check for abbreviations first
        abbrev = {
            'hyd': 'Hyderabad',
            'blr': 'Bangalore',
            'blore': 'Bangalore',
            'mum': 'Mumbai',
            'del': 'Delhi',
            'chn': 'Chennai',
            'kol': 'Kolkata'
        }
        
        for abbrev_key, city_name in abbrev.items():
            if abbrev_key in query:
                return city_name
        
        # Check for full city names
        for city_key, city_name in cities.items():
            if city_key in query:
                return city_name
        
        return None
    
    def create_clarification(
        self,
        clarification_type: str,
        original_query: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Create a clarification request
        
        Args:
            clarification_type: 'location', 'details', 'confirmation'
            original_query: Original user query
            question: Question to ask user
        
        Returns:
            Clarification object
        """
        return {
            'type': clarification_type,
            'original_query': original_query,
            'question': question,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    
    def needs_clarification(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Determine if query needs clarification
        
        Returns:
            Clarification object if needed, None otherwise
        """
        
        # Local search needs location
        if intent == 'local_search':
            if not entities.get('location'):
                return self.create_clarification(
                    'location',
                    query,
                    "Sure! To find that near you, could you please tell me your location?"
                )
        
        # Weather needs location
        if intent == 'live_search' and 'weather' in query.lower():
            if not entities.get('location'):
                return self.create_clarification(
                    'location',
                    query,
                    "Which city's weather would you like to know?"
                )
        
        # Very vague queries
        if len(query.split()) < 2 and intent not in ['factual', 'clarify']:
            return self.create_clarification(
                'details',
                query,
                "Could you provide more details about what you're looking for?"
            )
        
        return None


# Create singleton instance
context_intelligence = ContextIntelligence()
