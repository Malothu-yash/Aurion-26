"""
Smart Task Resolver - Intelligent task/reminder creation system

This module handles:
1. Understanding tasks in ANY natural language format
2. Extracting time, description, and details intelligently
3. Detecting missing information (AM/PM, date, etc.)
4. Validating and normalizing time formats
5. Creating confirmation messages

Examples:
- "Remind me to sleep in 3 min" ✅
- "Remind me to go to college at 23:09" ✅
- "Set alarm for 5pm tomorrow" ✅
- "Wake me up in 2 hours" ✅
- "Meeting with client at 3" → Asks AM or PM ✅
"""

import re
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import dateparser

logger = logging.getLogger(__name__)

class TaskResolver:
    """Resolves task/reminder requests with intelligent parsing"""
    
    def __init__(self):
        """Initialize the task resolver"""
        logger.info("✅ TaskResolver initialized")
        
        # Task action keywords
        self.task_keywords = [
            "remind", "reminder", "remember", "alert", "notify",
            "wake", "alarm", "schedule", "task", "todo"
        ]
        
        # Time indicators
        self.relative_time_patterns = [
            r"in\s+(\d+)\s*(min|minute|minutes|mins|m)",
            r"in\s+(\d+)\s*(hour|hours|hrs|h)",
            r"in\s+(\d+)\s*(day|days|d)",
            r"after\s+(\d+)\s*(min|minute|minutes|mins|m)",
            r"after\s+(\d+)\s*(hour|hours|hrs|h)",
        ]
        
        # Absolute time patterns
        self.absolute_time_patterns = [
            r"at\s+(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?",  # "at 3:00 pm" or "at 3:00"
            r"at\s+(\d{1,2})\s*(am|pm|AM|PM)?(?:\s|$)",   # "at 3 pm" or "at 3"
            r"(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?",       # "3:00 pm" or "3:00"
            r"(\d{1,2})\s*(am|pm|AM|PM)(?:\s|$)",        # "6am" or "5 pm"
        ]
        
        # Date keywords
        self.date_keywords = {
            "today": 0,
            "tomorrow": 1,
            "day after tomorrow": 2,
            "next week": 7,
        }
    
    async def resolve_task(
        self,
        query: str,
        conversation_id: str,
        confirmed_context: Optional[Dict] = None
    ) -> Tuple[str, Dict, bool]:
        """
        Resolve task/reminder request
        
        Args:
            query: User's query
            conversation_id: Unique conversation ID
            confirmed_context: Previously confirmed details
            
        Returns:
            (action, task_details, is_complete)
            - action: "confirm" | "clarify"
            - task_details: Extracted task information
            - is_complete: True if ready to create task
        """
        
        logger.info(f"🔍 Resolving task request: '{query}'")
        
        # Merge context
        task_details = confirmed_context.copy() if confirmed_context else {}
        
        # Extract task description
        if not task_details.get("description"):
            description = self._extract_task_description(query)
            if description:
                task_details["description"] = description
                logger.info(f"📝 Extracted description: '{description}'")
        
        # Extract time
        if not task_details.get("time_string") and not task_details.get("parsed_time"):
            time_info = self._extract_time(query)
            if time_info:
                task_details.update(time_info)
                logger.info(f"⏰ Extracted time: {time_info}")
        
        # Validate and check completeness
        is_complete, missing_fields = self._validate_task(task_details)
        
        if is_complete:
            # All info present - ready to confirm
            logger.info(f"✅ Task complete: {task_details}")
            return "confirm", task_details, True
        else:
            # Missing information - need clarification
            logger.info(f"❓ Missing: {missing_fields}")
            task_details["missing_fields"] = missing_fields
            return "clarify", task_details, False
    
    def _extract_task_description(self, query: str) -> Optional[str]:
        """
        Extract task description from query
        
        Examples:
        - "Remind me to sleep" → "sleep"
        - "Wake me up" → "wake up"
        - "Meeting with client" → "meeting with client"
        """
        
        query_lower = query.lower()
        
        # Special case 1: "wake me up" standalone
        if re.match(r"wake\s+(?:me\s+)?up(?:\s+in|\s+at|\s|$)", query_lower):
            # Extract time part and remove it
            time_part = re.sub(r"wake\s+(?:me\s+)?up\s*", "", query_lower).strip()
            # If there's meaningful text after, use it; otherwise "wake up"
            if time_part and not re.match(r"^(in|at)\s+\d", time_part):
                return time_part.capitalize()
            return "Wake up"
        
        # Pattern 1: "remind me to X"
        patterns = [
            # Special: "remind me [when] to [task]" - captures task at the end
            r"remind\s+(?:me\s+)?(?:tomorrow|today|tonight|in\s+\d+|at\s+\d+).*?\s+to\s+(.+?)$",
            # Standard: "remind me to [task] [when]"
            r"remind\s+(?:me\s+)?to\s+(.+?)(?:\s+in\s+\d|\s+at\s+\d|\s+\d+\s*(?:am|pm)|\s+tomorrow|\s+today|\s+on|$)",
            r"reminder\s+(?:me\s+)?to\s+(.+?)(?:\s+in\s+\d|\s+at\s+\d|\s+\d+\s*(?:am|pm)|\s+tomorrow|\s+today|\s+on|$)",
            r"alarm\s+(?:for\s+)?(.+?)(?:\s+in\s+\d|\s+at\s+\d|\s+\d+\s*(?:am|pm)|\s+tomorrow|\s+today|\s+on|$)",
            r"schedule\s+(.+?)(?:\s+in\s+\d|\s+at\s+\d|\s+\d+\s*(?:am|pm)|\s+tomorrow|\s+today|\s+on|$)",
            r"task:\s+(.+?)(?:\s+in\s+\d|\s+at\s+\d|\s+\d+\s*(?:am|pm)|\s+tomorrow|\s+today|\s+on|$)",
            # NEW: Handle standalone task descriptions
            r"^(.+?)\s+(?:at|in)\s+\d",  # "Meeting at 5", "Call mom at 3"
            r"^(.+?)\s+(?:tomorrow|today)",  # "Meeting tomorrow"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                
                # Special case: "wake me up" without additional description
                if pattern.startswith(r"wake") and not description:
                    description = "wake up"
                
                # Clean up common words
                description = re.sub(r'\b(at|in|on|for)\s+\d', '', description).strip()
                
                # Filter out time-only matches
                if description and not re.match(r'^\d+\s*(min|hour|day)', description):
                    return description.capitalize()
        
        # Pattern 2: Simple task without keywords
        # If query doesn't have time indicators, treat whole thing as description
        time_indicators = ["in ", "at ", "tomorrow", "today", "after", "am", "pm"]
        has_time = any(ind in query_lower for ind in time_indicators)
        
        if not has_time and len(query.split()) <= 10:
            # Likely a simple task description
            return query.strip().capitalize()
        
        return None
    
    def _extract_time(self, query: str) -> Optional[Dict]:
        """
        Extract time information from query
        
        Returns dict with:
        - time_string: Original time string
        - parsed_time: datetime object
        - time_type: "relative" | "absolute"
        - needs_ampm: True if time needs AM/PM clarification
        """
        
        query_lower = query.lower()
        
        # Try relative time first ("in 3 minutes")
        for pattern in self.relative_time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                # Calculate time
                now = datetime.now()
                if unit.startswith('min') or unit == 'm':
                    target_time = now + timedelta(minutes=value)
                elif unit.startswith('hour') or unit == 'h':
                    target_time = now + timedelta(hours=value)
                elif unit.startswith('day') or unit == 'd':
                    target_time = now + timedelta(days=value)
                else:
                    continue
                
                return {
                    "time_string": f"in {value} {unit}",
                    "parsed_time": target_time.isoformat(),
                    "time_type": "relative",
                    "needs_ampm": False,
                    "display_time": target_time.strftime("%I:%M %p on %B %d, %Y")
                }
        
        # Try absolute time ("at 5pm", "at 23:09", "at 3")
        for pattern in self.absolute_time_patterns:
            match = re.search(pattern, query_lower)
            if match:
                groups = [g for g in match.groups() if g is not None]  # Filter out None values
                
                # Parse based on number of groups
                if len(groups) == 3:  # HH:MM format with optional AM/PM
                    hour = int(groups[0])
                    minute = int(groups[1])
                    ampm = groups[2] if groups[2] else None
                elif len(groups) == 2:
                    # Could be "H AM/PM" or "HH:MM"
                    if groups[1] and groups[1].lower() in ['am', 'pm']:
                        # H AM/PM format
                        hour = int(groups[0])
                        minute = 0
                        ampm = groups[1]
                    else:
                        # HH:MM without AM/PM
                        hour = int(groups[0])
                        minute = int(groups[1])
                        ampm = None
                elif len(groups) == 1:
                    # Just hour, no AM/PM
                    hour = int(groups[0])
                    minute = 0
                    ampm = None
                else:
                    continue
                
                # Check if 24-hour format
                is_24_hour = hour > 12 or (hour == 0)
                
                if is_24_hour:
                    # 24-hour format (23:09)
                    needs_ampm = False
                    final_hour = hour
                elif ampm:
                    # Has AM/PM specified
                    needs_ampm = False
                    if ampm.lower() == "pm" and hour != 12:
                        final_hour = hour + 12
                    elif ampm.lower() == "am" and hour == 12:
                        final_hour = 0
                    else:
                        final_hour = hour
                else:
                    # Ambiguous time (need AM/PM)
                    needs_ampm = True
                    final_hour = hour
                
                # Determine date (today or tomorrow)
                now = datetime.now()
                target_date = now.date()
                
                # Check for date keywords
                if "tomorrow" in query_lower:
                    target_date = (now + timedelta(days=1)).date()
                elif "today" in query_lower:
                    target_date = now.date()
                else:
                    # If time has passed today, assume tomorrow
                    test_time = datetime.combine(target_date, datetime.min.time().replace(hour=final_hour, minute=minute))
                    if not needs_ampm and test_time <= now:
                        target_date = (now + timedelta(days=1)).date()
                
                if needs_ampm:
                    return {
                        "time_string": match.group(0),
                        "hour": final_hour,
                        "minute": minute,
                        "date": target_date.isoformat(),
                        "time_type": "absolute",
                        "needs_ampm": True
                    }
                else:
                    target_time = datetime.combine(target_date, datetime.min.time().replace(hour=final_hour, minute=minute))
                    return {
                        "time_string": match.group(0),
                        "parsed_time": target_time.isoformat(),
                        "time_type": "absolute",
                        "needs_ampm": False,
                        "display_time": target_time.strftime("%I:%M %p on %B %d, %Y")
                    }
        
        # Try dateparser as fallback
        try:
            parsed = dateparser.parse(query, settings={'PREFER_DATES_FROM': 'future'})
            if parsed:
                return {
                    "time_string": query,
                    "parsed_time": parsed.isoformat(),
                    "time_type": "parsed",
                    "needs_ampm": False,
                    "display_time": parsed.strftime("%I:%M %p on %B %d, %Y")
                }
        except:
            pass
        
        return None
    
    def _validate_task(self, task_details: Dict) -> Tuple[bool, list]:
        """
        Validate if task has all required information
        
        Returns:
            (is_complete, missing_fields)
        """
        
        missing = []
        
        # Check description
        if not task_details.get("description"):
            missing.append("description")
        
        # Check time
        if not task_details.get("parsed_time"):
            if task_details.get("needs_ampm"):
                missing.append("ampm")
            else:
                missing.append("time")
        
        is_complete = len(missing) == 0
        return is_complete, missing
    
    def apply_ampm(self, task_details: Dict, ampm: str) -> Dict:
        """
        Apply AM/PM to ambiguous time
        
        Args:
            task_details: Task with hour, minute, date
            ampm: "am" or "pm"
            
        Returns:
            Updated task_details with parsed_time
        """
        
        hour = task_details.get("hour", 0)
        minute = task_details.get("minute", 0)
        date_str = task_details.get("date")
        
        # Convert to 24-hour
        if ampm.lower() == "pm" and hour != 12:
            hour = hour + 12
        elif ampm.lower() == "am" and hour == 12:
            hour = 0
        
        # Create datetime
        date = datetime.fromisoformat(date_str).date()
        target_time = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
        
        task_details["parsed_time"] = target_time.isoformat()
        task_details["needs_ampm"] = False
        task_details["display_time"] = target_time.strftime("%I:%M %p on %B %d, %Y")
        
        return task_details
    
    def create_confirmation_message(self, task_details: Dict) -> str:
        """
        Create confirmation message before creating task
        
        Returns natural language confirmation
        """
        
        description = task_details.get("description", "task")
        display_time = task_details.get("display_time", "the specified time")
        
        message = f"📋 I'll create a reminder:\n\n"
        message += f"**Task:** {description}\n"
        message += f"**Time:** {display_time}\n\n"
        message += f"Shall I create this reminder?"
        
        return message
    
    def get_clarification_message(self, task_details: Dict) -> str:
        """
        Generate specific clarification question
        
        Returns question for missing info
        """
        
        missing = task_details.get("missing_fields", [])
        
        if "description" in missing:
            return "What should I remind you about?"
        
        if "ampm" in missing:
            hour = task_details.get("hour", 0)
            return f"Is that {hour} AM or PM?"
        
        if "time" in missing:
            if task_details.get("description"):
                return f"When should I remind you to {task_details['description']}?"
            else:
                return "When should I set this reminder?"
        
        return "Could you provide more details?"
