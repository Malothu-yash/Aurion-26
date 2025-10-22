"""
Smart Task Responder - AI-driven contextual responses
No fixed templates, fully dynamic based on context
Creates truly personalized, non-robotic responses
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import pytz
import random

logger = logging.getLogger(__name__)


class SmartTaskResponder:
    """Generate contextually intelligent responses for task operations"""
    
    def __init__(self, ai_clients_module):
        """
        Initialize with ai_clients module (not instance)
        Args:
            ai_clients_module: The app.services.ai_clients module
        """
        self.ai_clients = ai_clients_module
        
    async def generate_confirmation_message(
        self,
        task_description: str,
        scheduled_time: datetime,
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Generate a natural, contextual confirmation message
        Uses AI to create unique responses based on task context
        """
        
        # Calculate time context
        now = datetime.now(pytz.UTC)
        if scheduled_time.tzinfo is None:
            scheduled_time = pytz.UTC.localize(scheduled_time)
        
        time_until = scheduled_time - now
        minutes_until = int(time_until.total_seconds() / 60)
        
        # Determine urgency level
        if minutes_until < 5:
            urgency = "EXTREMELY URGENT"
        elif minutes_until < 15:
            urgency = "URGENT"
        elif minutes_until < 60:
            urgency = "SOON"
        elif minutes_until < 240:
            urgency = "MODERATE"
        else:
            urgency = "RELAXED"
        
        # Determine time of day
        hour = scheduled_time.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Format the exact time with better readability
        local_time = scheduled_time.astimezone(pytz.timezone('Asia/Kolkata'))  # Adjust timezone as needed
        
        if minutes_until < 60:
            time_display = f"{local_time.strftime('%I:%M %p')} (in {minutes_until} minute{'s' if minutes_until != 1 else ''})"
        elif time_until.days == 0:
            time_display = f"today at {local_time.strftime('%I:%M %p')}"
        elif time_until.days == 1:
            time_display = f"tomorrow at {local_time.strftime('%I:%M %p')}"
        else:
            time_display = f"on {local_time.strftime('%B %d at %I:%M %p')}"
        
        # Classify task type
        task_type = self._classify_task_type(task_description.lower())
        
        # Get user's name if available
        user_name = user_context.get("name", "") if user_context else ""
        
        # Build AI prompt for dynamic response generation
        prompt = f"""You are a friendly, creative AI assistant confirming a reminder. Be NATURAL and VARIED.

CONTEXT:
- Task: "{task_description}"
- When: {time_display}
- Task type: {task_type}
- Urgency: {urgency}
- Time of day: {time_of_day}
{f"- User's name: {user_name}" if user_name else ""}

YOUR MISSION:
Generate a SHORT, natural confirmation message that:
1. Sounds like a real person talking (NOT robotic!)
2. Matches the urgency (urgent = energetic, relaxed = chill)
3. Shows the EXACT time clearly (like "{local_time.strftime('%I:%M %p')}")
4. Adds 1-2 relevant emojis naturally
5. Ends with a casual confirmation ("Sound good?", "Cool?", "Ready?", "Alright?")
6. Is CREATIVE and UNIQUE each time
7. MAX 2 short sentences

TONE EXAMPLES by urgency:
- EXTREMELY URGENT (< 5 min): Energetic, exciting, "Quick!", "Hurry!"
- URGENT (< 15 min): Upbeat, direct, "Got it!"
- SOON (< 1 hour): Friendly, clear
- MODERATE: Casual, relaxed
- RELAXED: Chill, conversational

GOOD EXAMPLES (be creative like these):
- Urgent college: "Alright! I'll buzz you at 8:41 AM (that's 4 minutes!) to get to college. Ready? 🎓"
- Meeting: "Got it! I'll ping you at 3:00 PM tomorrow for the meeting. Sound good? 📅"
- Sleep: "Perfect! Wake-up call set for 7:00 AM tomorrow morning. Sleep tight! 😴"
- Workout: "You got it! Gym reminder at 6:30 PM today. Let's crush it! 💪"
- Casual: "Sure thing! I'll remind you at 2:00 PM. Cool? ✨"

BAD EXAMPLES (don't do this):
- "I'll create a reminder for..."
- "Reminder has been set for..."
- "Your task is scheduled..."
- Any formal or robotic phrasing

Now generate YOUR unique, natural confirmation:"""
        
        try:
            # Generate response using AI
            response = await self.ai_clients.generate_response(
                query=prompt,
                system_prompt="You are creative and casual. Write like texting a friend. Be brief, natural, and unique every time.",
                history=[]
            )
            
            # Clean up response
            response = response.strip().strip('"').strip("'")
            
            # Ensure it ends with punctuation
            if not any(response.endswith(p) for p in ["?", "!", "."]):
                response += " ?"
            
            logger.info(f"✨ Generated unique confirmation: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"AI generation failed, using smart fallback: {e}")
            return self._generate_fallback_confirmation(
                task_description, time_display, urgency, task_type
            )
    
    async def generate_success_message(
        self,
        task_description: str,
        scheduled_time: datetime,
        user_email: str,
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Generate a natural, encouraging success message
        Varies based on task completion context
        """
        
        # Calculate time context
        now = datetime.now(pytz.UTC)
        if scheduled_time.tzinfo is None:
            scheduled_time = pytz.UTC.localize(scheduled_time)
        
        time_until = scheduled_time - now
        minutes_until = int(time_until.total_seconds() / 60)
        
        # Format exact time
        local_time = scheduled_time.astimezone(pytz.timezone('Asia/Kolkata'))
        
        if minutes_until < 60:
            exact_time = local_time.strftime('%I:%M %p')
            time_description = f"{exact_time} (in {minutes_until} minute{'s' if minutes_until != 1 else ''})"
        elif time_until.days == 0:
            time_description = f"today at {local_time.strftime('%I:%M %p')}"
        elif time_until.days == 1:
            time_description = f"tomorrow at {local_time.strftime('%I:%M %p')}"
        else:
            time_description = local_time.strftime('%B %d at %I:%M %p')
        
        task_type = self._classify_task_type(task_description.lower())
        user_name = user_context.get("name", "") if user_context else ""
        
        # Mask email for privacy (show only first part)
        email_display = user_email.split('@')[0] + '@...'
        
        # Build AI prompt
        prompt = f"""You are a friendly AI assistant confirming a task was successfully scheduled. Be NATURAL and ENCOURAGING.

CONTEXT:
- Task: "{task_description}"
- Email notification: {time_description}
- User email: {email_display}
- Task type: {task_type}
{f"- User's name: {user_name}" if user_name else ""}

YOUR MISSION:
Generate a SHORT, encouraging success message that:
1. Sounds genuinely excited and supportive (NOT corporate!)
2. Confirms the EXACT time clearly (like "{local_time.strftime('%I:%M %p')}")
3. Mentions email briefly and naturally
4. Adds personality matching the task type
5. Uses 1-2 relevant emojis
6. MAX 2-3 short sentences
7. Is CREATIVE and UNIQUE each time

TONE by task type:
- Urgent tasks: Energetic, "You got this!", "Ready!"
- Meetings: Professional but warm, "All set!"
- Fitness: Motivating, "Let's go!", "Crush it!"
- Sleep: Calming, "Rest well", "Sweet dreams"
- General: Friendly, supportive

GOOD EXAMPLES (be creative like these):
- Urgent: "Done! 🚀 You'll get pinged at 8:41 AM sharp. Don't miss it! 😄"
- Meeting: "All set! 📅 Email reminder coming at 3:00 PM tomorrow. You got this! ✨"
- Workout: "Locked in! 💪 Gym email hitting your inbox at 6:30 PM. Let's do this! 🔥"
- Sleep: "Perfect! 😴 Wake-up email coming at 7:00 AM tomorrow. Sleep well! ✨"
- Casual: "You're all set! ✅ I'll email you at 2:00 PM. Easy! 🎯"

BAD EXAMPLES (don't do this):
- "Reminder has been created successfully"
- "Your task is scheduled"
- "You will receive an email notification"
- Any formal or boring corporate speak

Now generate YOUR unique, encouraging message:"""
        
        try:
            # Generate response using AI
            response = await self.ai_clients.generate_response(
                query=prompt,
                system_prompt="You are enthusiastic and supportive. Write like cheering on a friend. Be brief and natural.",
                history=[]
            )
            
            response = response.strip().strip('"').strip("'")
            logger.info(f"✨ Generated unique success message: {response[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"AI generation failed, using smart fallback: {e}")
            return self._generate_fallback_success(
                task_description, time_description, email_display, task_type
            )
    
    def _classify_task_type(self, task_description: str) -> str:
        """Classify task into categories for better context"""
        
        task_lower = task_description.lower()
        
        if any(word in task_lower for word in ['sleep', 'wake', 'alarm', 'bed', 'nap']):
            return "sleep/wake"
        elif any(word in task_lower for word in ['meeting', 'call', 'zoom', 'conference', 'interview']):
            return "meeting"
        elif any(word in task_lower for word in ['gym', 'workout', 'exercise', 'run', 'fitness', 'yoga']):
            return "fitness"
        elif any(word in task_lower for word in ['college', 'class', 'school', 'lecture', 'study', 'exam']):
            return "education"
        elif any(word in task_lower for word in ['eat', 'lunch', 'dinner', 'breakfast', 'food', 'meal']):
            return "meal"
        elif any(word in task_lower for word in ['medicine', 'pill', 'medication', 'doctor', 'appointment', 'health']):
            return "health"
        elif any(word in task_lower for word in ['birthday', 'anniversary', 'party', 'event', 'celebration']):
            return "celebration"
        else:
            return "general"
    
    def _generate_fallback_confirmation(
        self,
        task_description: str,
        time_display: str,
        urgency: str,
        task_type: str
    ) -> str:
        """Smart fallback if AI generation fails - still varied and natural"""
        
        # Pick varied phrases based on urgency and task type
        if urgency in ["EXTREMELY URGENT", "URGENT"]:
            templates = [
                f"Got it! I'll buzz you at {time_display} for '{task_description}'. Ready? 🚀",
                f"Quick! Reminder set for {time_display} - '{task_description}'. Sound good? ⚡",
                f"On it! You'll get pinged {time_display} about '{task_description}'. Cool? 🎯",
            ]
        elif urgency == "SOON":
            templates = [
                f"Perfect! I'll remind you at {time_display} for '{task_description}'. Good? ✨",
                f"You got it! Reminder at {time_display} - '{task_description}'. Alright? 👍",
                f"Sure thing! I'll ping you {time_display} about '{task_description}'. Ready? 🔔",
            ]
        else:
            templates = [
                f"All set! Reminder scheduled for {time_display} - '{task_description}'. Sound good? 📅",
                f"Perfect! I'll remind you at {time_display} for '{task_description}'. Cool? ✅",
                f"Done! You'll get a reminder {time_display} about '{task_description}'. Alright? 💫",
            ]
        
        return random.choice(templates)
    
    def _generate_fallback_success(
        self,
        task_description: str,
        time_description: str,
        email_display: str,
        task_type: str
    ) -> str:
        """Smart fallback success message - still natural and varied"""
        
        # Task-type specific emojis and phrases
        emoji_map = {
            "sleep/wake": ["😴", "✨", "🌙"],
            "meeting": ["📅", "✅", "🎯"],
            "fitness": ["💪", "🔥", "🏃"],
            "education": ["🎓", "📚", "✏️"],
            "meal": ["🍽️", "🥗", "☕"],
            "health": ["💊", "🏥", "❤️"],
            "celebration": ["🎉", "🎂", "🎈"],
            "general": ["✨", "✅", "🎯"]
        }
        
        emojis = emoji_map.get(task_type, ["✨", "✅"])
        emoji = random.choice(emojis)
        
        templates = [
            f"Done! {emoji} Email coming {time_description}. You're all set! 🎯",
            f"Perfect! {emoji} I'll email you {time_description}. All locked in! ✨",
            f"You got it! {emoji} Reminder email at {time_description}. Ready! 🚀",
            f"All set! {emoji} You'll get an email {time_description}. Easy! ✅",
        ]
        
        return random.choice(templates)
