"""
Universal Natural Language Task Parser
Understands task requests in ANY way user expresses them
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dateutil import parser as date_parser
import pytz

logger = logging.getLogger(__name__)

class NaturalLanguageTaskParser:
    """Parse task requests from any natural language input"""
    
    def __init__(self):
        # Common task action verbs - ANY way user might say it
        self.task_verbs = [
            "remind", "tell", "notify", "alert", "ping", "wake", "call",
            "text", "message", "email", "alarm", "schedule", "book",
            "remember", "don't forget", "note", "jot down", "set", "create"
        ]
        
        # Time patterns for ANY format
        self.time_patterns = {
            # Relative times
            "in_minutes": r"in\s+(\d+)\s*(?:minute|minutes|min|mins|m)(?:\s|$)",
            "in_hours": r"in\s+(\d+)\s*(?:hour|hours|hr|hrs|h)(?:\s|$)",
            "in_days": r"in\s+(\d+)\s*(?:day|days|d)(?:\s|$)",
            
            # Specific times - 12 hour
            "at_time_12hr": r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)",
            "time_12hr_standalone": r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)(?:\s|$)",
            
            # Specific times - 24 hour
            "at_time_24hr": r"at\s+(\d{1,2}):(\d{2})",
            "time_24hr_standalone": r"(\d{1,2}):(\d{2})",
            
            # Hour only (ambiguous - will ask AM/PM if needed)
            "at_hour_only": r"at\s+(\d{1,2})(?!\:)(?:\s|$)",
            
            # Day references
            "tomorrow": r"tomorrow",
            "today": r"today",
            "tonight": r"tonight",
            "next_week": r"next\s+week",
            "this_evening": r"this\s+evening",
            "this_morning": r"this\s+morning",
            "this_afternoon": r"this\s+afternoon",
            
            # Day of week
            "day_of_week": r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        }
    
    async def parse_task(self, query: str) -> Dict:
        """
        Parse task from natural language query - ANY format
        
        Returns:
            {
                "description": str,
                "scheduled_time_utc": datetime,
                "time_display": str,
                "time_string": str,
                "confidence": float,
                "needs_clarification": bool,
                "clarification_type": str
            }
        """
        
        query_lower = query.lower().strip()
        
        # Extract time information
        time_info = await self._extract_time(query)
        
        # Extract task description
        description = await self._extract_description(query, time_info)
        
        return {
            "description": description,
            "scheduled_time_utc": time_info.get("scheduled_time_utc"),
            "time_display": time_info.get("display"),
            "time_string": time_info.get("original_string"),
            "confidence": time_info.get("confidence", 0.7),
            "needs_clarification": time_info.get("needs_clarification", False),
            "clarification_type": time_info.get("clarification_type")
        }
    
    async def _extract_time(self, query: str) -> Dict:
        """Extract time from query - handles ANY format"""
        
        query_lower = query.lower()
        now = datetime.now(pytz.UTC)
        
        # Try relative times first (most common)
        
        # "in X minutes"
        match = re.search(self.time_patterns["in_minutes"], query_lower)
        if match:
            minutes = int(match.group(1))
            scheduled_time = now + timedelta(minutes=minutes)
            return {
                "scheduled_time_utc": scheduled_time,
                "display": f"in {minutes} minute{'s' if minutes != 1 else ''}",
                "original_string": match.group(0).strip(),
                "confidence": 1.0
            }
        
        # "in X hours"
        match = re.search(self.time_patterns["in_hours"], query_lower)
        if match:
            hours = int(match.group(1))
            scheduled_time = now + timedelta(hours=hours)
            return {
                "scheduled_time_utc": scheduled_time,
                "display": f"in {hours} hour{'s' if hours != 1 else ''}",
                "original_string": match.group(0).strip(),
                "confidence": 1.0
            }
        
        # "in X days"
        match = re.search(self.time_patterns["in_days"], query_lower)
        if match:
            days = int(match.group(1))
            scheduled_time = now + timedelta(days=days)
            return {
                "scheduled_time_utc": scheduled_time,
                "display": f"in {days} day{'s' if days != 1 else ''}",
                "original_string": match.group(0).strip(),
                "confidence": 1.0
            }
        
        # Check for day references (tomorrow, today, tonight)
        day_offset = 0
        hour_override = None
        day_keyword = None
        
        if "tomorrow" in query_lower:
            day_offset = 1
            day_keyword = "tomorrow"
        elif "tonight" in query_lower:
            hour_override = 21  # 9 PM
            day_keyword = "tonight"
        elif "today" in query_lower:
            day_offset = 0
            day_keyword = "today"
        elif "this evening" in query_lower:
            hour_override = 18  # 6 PM
        elif "this morning" in query_lower:
            hour_override = 8  # 8 AM
        elif "this afternoon" in query_lower:
            hour_override = 14  # 2 PM
        
        # "at X:XX AM/PM" - most explicit format
        match = re.search(self.time_patterns["at_time_12hr"], query_lower)
        if not match:
            match = re.search(self.time_patterns["time_12hr_standalone"], query_lower)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3).lower()
            
            # Convert to 24-hour
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            scheduled_time += timedelta(days=day_offset)
            
            # If time has passed today, schedule for tomorrow
            if scheduled_time < now and day_offset == 0:
                scheduled_time += timedelta(days=1)
            
            time_str = f"{match.group(1)}:{minute:02d} {period.upper()}"
            if day_keyword:
                time_str = f"{day_keyword} at {time_str}"
            
            return {
                "scheduled_time_utc": scheduled_time,
                "display": time_str,
                "original_string": match.group(0).strip(),
                "confidence": 1.0
            }
        
        # "at XX:XX" - 24 hour format
        match = re.search(self.time_patterns["at_time_24hr"], query_lower)
        if not match:
            match = re.search(self.time_patterns["time_24hr_standalone"], query_lower)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            scheduled_time += timedelta(days=day_offset)
            
            # If time has passed today, schedule for tomorrow
            if scheduled_time < now and day_offset == 0:
                scheduled_time += timedelta(days=1)
            
            # Convert to 12-hour for display
            display_hour = hour % 12 or 12
            period = "AM" if hour < 12 else "PM"
            time_str = f"{display_hour}:{minute:02d} {period}"
            
            if day_keyword:
                time_str = f"{day_keyword} at {time_str}"
            
            return {
                "scheduled_time_utc": scheduled_time,
                "display": time_str,
                "original_string": match.group(0).strip(),
                "confidence": 0.95
            }
        
        # "at XX" (hour only - might need AM/PM clarification)
        match = re.search(self.time_patterns["at_hour_only"], query_lower)
        if match:
            hour = int(match.group(1))
            
            # Smart AM/PM detection based on hour and context
            if hour >= 1 and hour <= 7:
                # 1-7 could be either, but default to PM unless morning keyword
                if "morning" in query_lower or "am" in query_lower:
                    pass  # Keep as is
                else:
                    hour += 12  # Assume PM
            elif hour >= 8 and hour <= 11:
                # 8-11 likely AM unless PM specified
                if "pm" in query_lower or "evening" in query_lower or "night" in query_lower:
                    hour += 12
            
            scheduled_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            scheduled_time += timedelta(days=day_offset)
            
            if scheduled_time < now and day_offset == 0:
                scheduled_time += timedelta(days=1)
            
            display_hour = hour % 12 or 12
            period = "AM" if hour < 12 else "PM"
            time_str = f"{display_hour}:00 {period}"
            
            if day_keyword:
                time_str = f"{day_keyword} at {time_str}"
            
            return {
                "scheduled_time_utc": scheduled_time,
                "display": time_str,
                "original_string": match.group(0).strip(),
                "confidence": 0.75  # Lower confidence - assumed AM/PM
            }
        
        # If we have hour_override from keywords like "tonight"
        if hour_override is not None:
            scheduled_time = now.replace(hour=hour_override, minute=0, second=0, microsecond=0)
            scheduled_time += timedelta(days=day_offset)
            
            if scheduled_time < now:
                scheduled_time += timedelta(days=1)
            
            display_hour = hour_override % 12 or 12
            period = "AM" if hour_override < 12 else "PM"
            
            return {
                "scheduled_time_utc": scheduled_time,
                "display": f"{day_keyword or 'today'} at {display_hour}:00 {period}",
                "original_string": day_keyword or "tonight",
                "confidence": 0.8
            }
        
        # Try dateutil as last resort (catches many natural formats)
        try:
            # Remove task description words to isolate time
            time_query = query_lower
            for verb in self.task_verbs:
                time_query = time_query.replace(verb, "")
            time_query = re.sub(r"\b(me|to|about)\b", "", time_query)
            
            parsed_date = date_parser.parse(time_query, fuzzy=True)
            
            # Make timezone aware
            if parsed_date.tzinfo is None:
                parsed_date = pytz.UTC.localize(parsed_date)
            else:
                parsed_date = parsed_date.astimezone(pytz.UTC)
            
            # If in past, assume next occurrence
            if parsed_date < now:
                # If just time (not full date), add a day
                if parsed_date.date() == now.date():
                    parsed_date += timedelta(days=1)
            
            return {
                "scheduled_time_utc": parsed_date,
                "display": parsed_date.strftime("%b %d at %I:%M %p"),
                "original_string": time_query.strip(),
                "confidence": 0.6
            }
        except:
            pass
        
        # Default: no time found
        return {
            "scheduled_time_utc": None,
            "display": None,
            "original_string": None,
            "confidence": 0.0,
            "needs_clarification": True,
            "clarification_type": "time"
        }
    
    async def _extract_description(self, query: str, time_info: Dict) -> str:
        """Extract task description from query"""
        
        description = query.strip()
        
        # Remove common task verb phrases at the start
        patterns_to_remove = [
            r"^(?:remind|tell|notify|alert|ping|wake|call|text|message)\s+(?:me\s+)?(?:to\s+)?",
            r"^(?:set\s+)?(?:a\s+)?(?:reminder|alarm|task|notification)\s+(?:to\s+)?(?:for\s+)?",
            r"^(?:don't\s+forget\s+to\s+)",
            r"^(?:remember\s+to\s+)",
            r"^(?:schedule\s+(?:a\s+)?(?:reminder\s+)?(?:to\s+)?)",
            r"^(?:create\s+(?:a\s+)?(?:reminder\s+)?(?:to\s+)?)",
        ]
        
        for pattern in patterns_to_remove:
            description = re.sub(pattern, "", description, flags=re.IGNORECASE)
        
        # Remove time string from description
        if time_info.get("original_string"):
            time_str = time_info["original_string"]
            # Remove time string and surrounding whitespace
            description = description.replace(time_str, " ").strip()
        
        # Remove day keywords
        day_keywords = ["tomorrow", "today", "tonight", "this evening", "this morning", "this afternoon"]
        for keyword in day_keywords:
            description = re.sub(r"\b" + keyword + r"\b", "", description, flags=re.IGNORECASE)
        
        # Remove standalone time prepositions
        description = re.sub(r"\s+(?:at|in|on)(?:\s+|$)", " ", description)
        
        # Clean up multiple spaces
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Remove trailing punctuation
        description = description.strip('.,!?')
        
        # Capitalize first letter
        if description:
            description = description[0].upper() + description[1:]
        
        return description or "Task"
    
    def is_task_query(self, query: str) -> bool:
        """Detect if query is asking to create a task/reminder"""
        
        query_lower = query.lower()
        
        # Check for task verbs
        for verb in self.task_verbs:
            if re.search(r"\b" + verb + r"\b", query_lower):
                return True
        
        # Check for time patterns (if query has time, likely a task)
        for pattern_name, pattern in self.time_patterns.items():
            if re.search(pattern, query_lower):
                # If has time pattern AND action words, it's a task
                action_indicators = ["me", "to", "about", "for"]
                if any(indicator in query_lower for indicator in action_indicators):
                    return True
        
        # Specific phrases that indicate task even without verb
        task_phrases = ["in x minutes", "at x pm", "tomorrow", "tonight"]
        if any(phrase.replace("x", r"\d+") in query_lower for phrase in task_phrases):
            return True
        
        return False
