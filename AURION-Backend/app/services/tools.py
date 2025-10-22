
# app/services/tools.py
# This file handles all real-world "tools"
# like web search, video search, and reminders.

import httpx
import dateparser # For parsing time strings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    _FASTAPI_MAIL_AVAILABLE = True
except Exception as e:
    print(f"⚠️ fastapi-mail import failed, email features will be disabled. Reason: {e}")
    FastMail = None  # type: ignore
    MessageSchema = None  # type: ignore
    ConnectionConfig = None  # type: ignore
    _FASTAPI_MAIL_AVAILABLE = False
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel
import uuid  # For generating unique task IDs
import re  # For regex pattern matching in scraping
import json  # For JSON parsing in autonomous agent
import pytz  # For timezone handling

from app.core.config import settings
from app.core.strategy import get_strategy
from app.models.schemas import YouTubeVideo, Confirmation # Import our response models

# --- NEW SCRAPER FUNCTION ---
from bs4 import BeautifulSoup
import httpx # We already have this
import asyncio # We'll need this soon

# --- NEW: Autonomous Agent Imports ---
import google.generativeai as genai  # For sync Gemini calls in background tasks

# --- 1. Web Search Tool (Google Search API) ---
# We'll use httpx to make the API call ourselves, it's simpler
# than the full Google client library for just one endpoint.
async def search_web(query: str) -> list[dict]:
    """
    Searches the web using the Google Custom Search API.
    Returns a list of search result snippets.
    """
    strat = get_strategy()
    providers = strat.external.web_search
    results: list[dict] | None = None
    last_error = None
    for provider in providers:
        if provider in ("google_cse", "google_search", "google"):
            if not (settings.GOOGLE_API_KEY and settings.GOOGLE_SEARCH_CX_ID):
                continue
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": settings.GOOGLE_API_KEY,
                "cx": settings.GOOGLE_SEARCH_CX_ID,
                "q": query,
                "num": 3
            }
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                items = response.json().get("items", [])
                results = [
                    {"snippet": item.get("snippet"), "source": item.get("link"), "title": item.get("title")}
                    for item in items
                ]
                if results:
                    return results
            except Exception as e:
                last_error = e
                continue
        elif provider == "serpapi":
            if not settings.SERPAPI_KEY:
                continue
            try:
                url = "https://serpapi.com/search.json"
                params = {"q": query, "engine": "google", "api_key": settings.SERPAPI_KEY, "num": 3}
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                data = response.json()
                organic = data.get("organic_results", [])
                results = [
                    {"snippet": item.get("snippet"), "source": item.get("link"), "title": item.get("title")}
                    for item in organic[:3]
                ]
                if results:
                    return results
            except Exception as e:
                last_error = e
                continue
        elif provider == "zenserp":
            if not settings.ZENSERP_API_KEY:
                continue
            try:
                url = "https://app.zenserp.com/api/v2/search"
                params = {"q": query, "num": 3}
                headers = {"apikey": settings.ZENSERP_API_KEY}
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                data = response.json()
                organic = data.get("organic", []) or data.get("organic_results", [])
                results = [
                    {"snippet": item.get("description") or item.get("snippet"),
                     "source": item.get("url") or item.get("link"),
                     "title": item.get("title")}
                    for item in organic[:3]
                ]
                if results:
                    return results
            except Exception as e:
                last_error = e
                continue
    
    # If nothing worked
    print(f"Error searching web: {last_error}")
    return [{"snippet": f"Error searching web: {last_error}", "source": None}]


# --- 2. YouTube Search Tool ---
async def search_youtube(query: str) -> YouTubeVideo | None:
    """
    Searches YouTube for a video and returns our Pydantic model.
    """
    # Pick API key based on strategy (friend key as backup)
    api_key = settings.YOUTUBE_API_KEY or settings.GOOGLE_API_KEY or settings.FRIEND_YOUTUBE_KEY
    if not api_key:
        print("YouTube API key not configured")
        return None
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 1
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
        results = response.json().get("items", [])
        
        if not results:
            return None
            
        video = results[0]
        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        thumbnail = video["snippet"]["thumbnails"]["default"]["url"]
        
        # Return a clean Pydantic model
        return YouTubeVideo(
            videoId=video_id,
            title=title,
            thumbnail_url=thumbnail
        )
        
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return None

# --- 3. Task Manager (Scheduler & Email) ---

# Configure fastapi-mail with our SendGrid settings (if available)
mail_conf = None
_MAIL_CONFIGURED = False
if _FASTAPI_MAIL_AVAILABLE and settings.SENDGRID_API_KEY and (settings.SENDER_EMAIL or settings.MAIL_FROM):
    try:
        mail_conf = ConnectionConfig(
            MAIL_USERNAME="apikey", # This is always "apikey" for SendGrid
            MAIL_PASSWORD=settings.SENDGRID_API_KEY,
            MAIL_FROM=(settings.SENDER_EMAIL or settings.MAIL_FROM),
            MAIL_PORT=587,
            MAIL_SERVER="smtp.sendgrid.net",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False
        )
        _MAIL_CONFIGURED = True
    except Exception as e:
        print(f"⚠️ Failed to configure email (SendGrid): {e}")
        mail_conf = None
        _MAIL_CONFIGURED = False

# Create the scheduler
scheduler = AsyncIOScheduler()

async def send_reminder_email(email_to: str, task: str, task_id: str, user_id: str = "test-user-123", scheduled_time_str: str = None):
    """
    Sends an interactive HTML email with action buttons.
    Uses bulletproof email sender with automatic SMTP fallback.
    This runs as a BACKGROUND TASK to not block the scheduler.
    
    Args:
        email_to: Recipient email address
        task: Task description
        task_id: Unique task identifier
        user_id: User identifier
        scheduled_time_str: Human-readable scheduled time (e.g., "09:00 AM, October 22, 2025")
    """
    print(f"🔔 Sending reminder email for task: {task_id}")
    
    try:
        # Import bulletproof email sender
        from app.services.bulletproof_email import send_reminder_email_bulletproof
        
        # Send with automatic fallback (FastAPI-Mail → SMTP)
        success = await send_reminder_email_bulletproof(
            to_email=email_to,
            task_description=task,
            task_id=task_id,
            user_id=user_id,
            scheduled_time=scheduled_time_str
        )
        
        if success:
            print(f"✅ Reminder email sent successfully to {email_to}")
        else:
            print(f"❌ Failed to send reminder email to {email_to}")
            # Log to database or alert admin
            logger.error(f"CRITICAL: Email delivery failed for task {task_id} to {email_to}")
    
    except Exception as e:
        print(f"❌ Unexpected error sending reminder: {e}")
        logger.error(f"CRITICAL: Exception in send_reminder_email: {e}", exc_info=True)

def schedule_reminder(task: str, time_string: str, user_email: str, user_id: str = "test-user-123") -> Confirmation:
    """
    Parses a natural language time string and schedules an email reminder.
    Now with interactive email buttons!
    """
    # Use dateparser to understand "tomorrow at 5pm", "in 2 hours", etc.
    # We set PREFER_DATES_FROM to 'future' so "5pm" means *today* at 5pm,
    # not 5pm in the past.
    run_date = dateparser.parse(time_string, settings={'PREFER_DATES_FROM': 'future'})
    
    if not run_date:
        print(f"Error parsing time string: {time_string}")
        return Confirmation(message=f"Sorry, I couldn't understand the time '{time_string}'.")
    
    # Check if the user's email is set (we'll hardcode it for now)
    # In a real app, you'd get this from their user profile
    if not user_email:
         return Confirmation(message="I can't set a reminder, I don't know your email.")
    
    # Generate a unique task ID for tracking
    task_id = str(uuid.uuid4())
    print(f"Generated task ID: {task_id}")
         
    try:
        # Add the job to the scheduler with task_id!
        scheduler.add_job(
            send_reminder_email,
            'date', # Run on a specific date and time
            run_date=run_date,
            args=[user_email, task, task_id, user_id] # Pass task_id and user_id
        )
        print(f"Job scheduled: {task} at {run_date} with task_id: {task_id}")
        
        # Return a nice confirmation message
        return Confirmation(
            message=f"✅ Reminder set! I will email you at {run_date.strftime('%B %d at %I:%M %p')} about:\n\n{task}\n\n💡 You'll be able to mark it complete or snooze it directly from the email!"
        )
    except Exception as e:
        print(f"Error scheduling job: {e}")
        return Confirmation(message=f"Sorry, I had an error scheduling that reminder.")


async def schedule_reminder_with_datetime(
    description: str, 
    scheduled_time: datetime, 
    user_email: str, 
    user_id: str
) -> bool:
    """
    NEW: Schedule a reminder with a datetime object (from universal task parser)
    
    Args:
        description: Task description
        scheduled_time: datetime object (timezone-aware)
        user_email: User's registered email address
        user_id: User's conversation ID
        
    Returns:
        True if scheduled successfully, False otherwise
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Make sure scheduled_time is timezone-aware
        if scheduled_time.tzinfo is None:
            import pytz
            scheduled_time = pytz.UTC.localize(scheduled_time)
        
        # Format scheduled time for email display
        # Convert to local timezone for better readability
        local_time = scheduled_time.astimezone(pytz.timezone('Asia/Kolkata'))
        scheduled_time_str = local_time.strftime("%I:%M %p, %B %d, %Y")
        
        # Add job to scheduler
        scheduler.add_job(
            send_reminder_email,
            'date',
            run_date=scheduled_time,
            args=[user_email, description, task_id, user_id, scheduled_time_str],
            id=task_id  # Use task_id as job ID for easy tracking
        )
        
        print(f"✅ Job scheduled: '{description}' at {local_time.strftime('%Y-%m-%d %I:%M %p %Z')} for {user_email}")
        print(f"   Task ID: {task_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scheduling reminder: {e}")
        import traceback
        print(traceback.format_exc())
        return False


# --- NEW: Email a Friend Tool ---
async def send_email_to_recipient(recipient_email: str, subject: str, body: str) -> Confirmation:
    """
    Sends a standard email to any recipient.
    This enables the "Email a Friend" feature.
    
    Args:
        recipient_email: The email address to send to
        subject: The email subject line
        body: The email body content
        
    Returns:
        Confirmation message indicating success or failure
    """
    print(f"--- Sending email to {recipient_email} ---")
    
    if not (_FASTAPI_MAIL_AVAILABLE and _MAIL_CONFIGURED and FastMail and MessageSchema and mail_conf):
        print(f"--- Email disabled (fastapi-mail not available). Would send to {recipient_email} ---")
        return Confirmation(message=f"Email disabled in this environment. (Would send to {recipient_email})")

    message = MessageSchema(
        subject=subject,
        recipients=[recipient_email],  # The recipient is now dynamic
        body=body,
        subtype="plain"  # Plain text email
    )
    
    fm = FastMail(mail_conf)
    try:
        await fm.send_message(message)
        print("--- Email sent successfully! ---")
        return Confirmation(message=f"✅ Email successfully sent to {recipient_email}!")
    except Exception as e:
        print(f"--- Error sending email: {e} ---")
        return Confirmation(message=f"❌ Sorry, I failed to send the email: {str(e)}")
    

async def scrape_page_content(url: str) -> str:
    """
    Fetches a URL and uses BeautifulSoup to selectively
    extract clean text, focusing on main content.
    
    UPGRADED: Now uses selective content extraction:
    - Removes navigation, ads, scripts, styles
    - Targets <main>, <article>, or <body>
    - Extracts first 15 paragraphs
    - Cleans up whitespace
    """
    # Some websites block default user-agents, so we'll pretend to be a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Set a timeout so we don't wait forever for a slow page
            response = await client.get(url, headers=headers, timeout=5.0)
            response.raise_for_status() # Check for HTTP errors

        # Use BeautifulSoup and lxml to parse the HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Remove script, style, nav, footer, and ad elements
        # This dramatically improves content quality
        for element in soup(["script", "style", "nav", "footer", "aside", "form", "header"]):
            element.decompose()
        
        # Also remove common ad classes
        for ad_class in soup.find_all(class_=re.compile("ad|advertisement|promo|sidebar", re.I)):
            ad_class.decompose()
            
        # Smart content targeting: try to find <main> or <article> first
        # This focuses on the actual content, not boilerplate
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if not main_content:
            # Fallback to body if nothing found
            main_content = soup
        
        # Get text from all <p> tags within the main content
        # Limit to first 15 paragraphs to avoid overwhelming context
        paragraphs = main_content.find_all('p', limit=15)
        
        if not paragraphs:
            # Fallback if no <p> tags are found
            text = ' '.join(t.strip() for t in main_content.stripped_strings)
        else:
            text = ' '.join(p.get_text().strip() for p in paragraphs)

        # Clean up excessive whitespace (multiple spaces/newlines → single space)
        text = re.sub(r'\s+', ' ', text)
        
        # Return the first 3000 characters (optimal for LLM context)
        return text[:3000] if text else "No content could be extracted from this page."
        
    except httpx.TimeoutException:
        print(f"Timeout scraping {url}")
        return f"Error: Page took too long to load: {url}"
    except httpx.HTTPStatusError as e:
        print(f"HTTP error scraping {url}: {e}")
        return f"Error: Could not access page (HTTP {e.response.status_code}): {url}"
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return f"Error: Could not scrape content from {url}."


# --- 6. Weather Tool (OpenWeatherMap API) ---
async def get_weather(city: str) -> str:
    """
    Fetches the current weather for a city from OpenWeatherMap.
    Returns a formatted string with weather information.
    """
    if not settings.WEATHER_API_KEY:
        return "Weather API not configured."
        
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric" # For Celsius
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        data = response.json()
        
        return (
            f"Weather in {city}:\n"
            f"- Main: {data['weather'][0]['description']}\n"
            f"- Temperature: {data['main']['temp']}°C\n"
            f"- Feels Like: {data['main']['feels_like']}°C\n"
            f"- Humidity: {data['main']['humidity']}%"
        )
    except Exception as e:
        print(f"Error getting weather: {e}")
        return f"Sorry, I couldn't get the weather for {city}."

async def get_weather_data(city: str) -> dict:
    """
    Fetches weather data and returns structured dict for rich UI.
    Returns WeatherInfo compatible dict or None on error.
    """
    if not settings.WEATHER_API_KEY:
        return None
        
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        data = response.json()
        
        return {
            "city": city,
            "temperature": round(data['main']['temp'], 1),
            "description": data['weather'][0]['description'],
            "feels_like": round(data['main']['feels_like'], 1),
            "humidity": data['main']['humidity']
        }
    except Exception as e:
        print(f"Error getting weather: {e}")
        return None


# --- 7. Daily Briefing Job (Proactive Assistant) ---
async def run_daily_briefing(user_id: str, user_email: str):
    """
    The main job for the proactive daily briefing.
    This runs every day at a scheduled time.
    """
    print(f"--- Running daily briefing for {user_id} ---")
    
    # Import here to avoid circular imports
    from app.services.memory import get_facts_from_graph
    import google.generativeai as genai
    import json
    
    # 1. Get User's City from Neo4j
    facts = await get_facts_from_graph(user_id)
    city = "Hyderabad" # Default
    for fact in facts:
        if "LIVES_IN" in fact:
            city = fact.split(" ")[-1]
            break
    
    print(f"Daily Briefing: User lives in {city}")
            
    # 2. Fetch all data in parallel
    tasks = [
        get_weather(city),
        search_web(f"top news headlines today"),
        # You could also add a function to get today's reminders from your DB
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    weather = results[0] if not isinstance(results[0], Exception) else "Weather unavailable"
    news = results[1] if not isinstance(results[1], Exception) else []
    
    # 3. Use Gemini to synthesize the email
    prompt = f"""
    You are AURION, a personal assistant. Write a concise daily briefing email.
    Use the following information. Be friendly and professional.
    
    Weather: {weather}
    News Snippets: {json.dumps(news, indent=2)}
    
    Start with "Good morning! Here is your daily briefing for {city}:"
    Keep it brief (under 200 words).
    """
    
    try:
        # Configure and use Gemini
        genai.configure(api_key=(settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY))
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        email_body = gemini_model.generate_content(prompt).text
    except Exception as e:
        print(f"Error generating briefing with Gemini: {e}")
        email_body = f"Good morning! Here is your daily briefing for {city}:\n\n{weather}\n\nNews: {news}"
    
    # 4. Send the email
    try:
        message = MessageSchema(
            subject=f"AURION Daily Briefing - {city}",
            recipients=[user_email],
            body=email_body,
            subtype="plain"
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
        print(f"--- Daily briefing for {user_id} sent to {user_email}! ---")
    except Exception as e:
        print(f"Error sending daily briefing email: {e}")


# --- 8. Weekly Memory Consolidation (Proactive Learning) ---
# UPGRADED: Now analyzes both main chat AND mini-threads!
async def run_memory_consolidation(user_id: str):
    """
    Runs weekly to find new patterns in *both* main chat and mini-threads.
    This is AURION's "sleep cycle" - it reviews:
    1. Your main conversations
    2. Your focused questions (mini-threads)
    
    This dual-loop learning discovers what you're curious about!
    """
    print(f"--- 🧠 Running UPGRADED memory consolidation for {user_id} ---")
    
    # Import here to avoid circular imports
    from app.services import memory
    import google.generativeai as genai
    
    # 1. Get transcript of main chats
    main_transcript = await memory.get_recent_conversations(user_id, days=7)
    
    # 2. Get transcript of mini-thread "doubts" (NEW!)
    mini_thread_transcript = await memory.get_recent_mini_threads(user_id)
    
    if not main_transcript and not mini_thread_transcript:
        print("No transcripts to consolidate.")
        return
    
    if not main_transcript:
        main_transcript = ""
    if not mini_thread_transcript:
        mini_thread_transcript = ""

    print(f"Retrieved main transcript: {len(main_transcript)} characters")
    print(f"Retrieved mini-thread transcript: {len(mini_thread_transcript)} characters")
    
    # 3. Ask Gemini to find new facts from BOTH sources
    prompt = f"""
You are a data analyst and psychologist. I am giving you two sets of
data for a user:
1.  Their main chat history.
2.  A list of "mini-threads" which are their focused doubts and 
    questions about specific text snippets.

Your job is to find high-level, *inferred* facts, interests, or
*areas of confusion* for this user.

Respond *only* in Cypher queries to add these facts to a graph.

Examples:
- If user main chat is about Python, but mini-threads are all 
  "explain this" about Python Decorators:
  MERGE (u:User {{id: '{user_id}'}})-[:IS_LEARNING]->(t:Topic {{name: 'Python Decorators'}})
  
- If user keeps asking "what is..." about "React Hooks":
  MERGE (u:User {{id: '{user_id}'}})-[:IS_CURIOUS_ABOUT]->(t:Topic {{name: 'React Hooks'}})
  
- If user discusses "Project Apollo" in main chat:
  MERGE (u:User {{id: '{user_id}'}})-[:IS_WORKING_ON]->(p:Project {{name: 'Project Apollo'}})
  
- If user frequently uses TypeScript (from main chat):
  MERGE (u:User {{id: '{user_id}'}})-[:USES_SKILL]->(s:Skill {{name: 'TypeScript'}})
  
- If no new patterns:
  NO_FACTS

Important: Each Cypher query must be on its own line.

--- MAIN CHAT TRANSCRIPT ---
{main_transcript[:30000]}

--- MINI-THREADS (DOUBTS) TRANSCRIPT ---
{mini_thread_transcript[:30000]}
"""
    
    # 3. Use Gemini to analyze patterns
    try:
        genai.configure(api_key=(settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY))
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        cypher_queries_str = gemini_model.generate_content(prompt).text
        
        print(f"Gemini consolidation response:\n{cypher_queries_str}")
        
    except Exception as e:
        print(f"Error generating consolidation with Gemini: {e}")
        return
    
    # 4. Save to Neo4j
    if "NO_FACTS" not in cypher_queries_str and "no new patterns" not in cypher_queries_str.lower():
        print(f"✨ Found new consolidated facts!")
        
        # Split by lines and filter out empty lines and markdown code blocks
        queries = [
            q.strip() 
            for q in cypher_queries_str.split('\n') 
            if q.strip() and not q.strip().startswith('```') and 'MERGE' in q.upper()
        ]
        
        for query in queries:
            try:
                print(f"Executing: {query[:100]}...")
                await memory.add_relationships_to_graph(query)
                print(f"✅ Saved pattern to Neo4j")
            except Exception as e:
                print(f"Error executing Cypher query: {e}")
        
    else:
        print("✨ No new patterns detected in this consolidation cycle")


# ============================================================================
# AUTONOMOUS AGENT SYSTEM
# ============================================================================

def _get_gemini_response_sync(prompt: str) -> str:
    """
    A helper function to run Gemini synchronously for background tasks.
    This is needed because background tasks can't use async/await.
    
    Args:
        prompt: The prompt to send to Gemini
        
    Returns:
        The generated text response
    """
    try:
        # Re-configure the sync client in the background task
        genai.configure(api_key=(settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY))
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Sync Gemini call failed: {e}")
        return f"Error in generation: {e}"


async def run_autonomous_plan(user_id: str, user_email: str, goal: str):
    """
    This is the core of the autonomous agent.
    It runs in the background, creates a plan, executes it step-by-step,
    and emails the user with the final report.
    
    This is a "Tier 3" feature - complex, multi-step goal execution.
    
    Args:
        user_id: The user's conversation ID
        user_email: Email address to send the final report
        goal: The user's high-level goal
        
    Example goals:
        - "Research my competitor, MegaCorp, and summarize their latest news"
        - "Plan a trip to Goa for next weekend from Hyderabad"
        - "Find the best Python courses and create a study plan"
    """
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🤖 AUTONOMOUS AGENT ACTIVATED for {user_id}")
    print(f"🎯 GOAL: {goal}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # --- STEP 1: CREATE A PLAN ---
    print("\n📋 Step 1: Creating execution plan...")
    
    plan_prompt = f"""
You are an AI planner. A user has given you a high-level goal.
Break this goal down into a JSON list of simple, executable tool-call strings.

Available Tools:
- "search_and_scrape(query)": Searches the web and scrapes content from top 3 results.
- "check_calendar()": Checks the user's Google Calendar for upcoming events.
- "summarize(context_key)": Summarizes previously gathered data.

IMPORTANT: 
- Each tool call must be a string that can be parsed.
- For search_and_scrape, put the query in single quotes.
- For check_calendar, no parameters needed.
- For summarize, reference data gathered from previous steps.

Goal: "{goal}"

Example 1:
Goal: "Research my competitor, 'MegaCorp', and summarize their latest news."
Response:
[
    "search_and_scrape('MegaCorp latest news 2025')",
    "search_and_scrape('MegaCorp products and services')",
    "summarize('all_search_results')"
]

Example 2:
Goal: "Plan a trip to Goa for next weekend from Hyderabad."
Response:
[
    "check_calendar()",
    "search_and_scrape('flights from Hyderabad to Goa next weekend')",
    "search_and_scrape('best 4-star hotels in Goa near beaches')",
    "search_and_scrape('top tourist attractions in Goa')",
    "summarize('all_search_results')"
]

Example 3:
Goal: "Find the best Python courses and create a study plan."
Response:
[
    "search_and_scrape('best Python courses 2025 for beginners')",
    "search_and_scrape('Python learning roadmap 2025')",
    "summarize('all_search_results')"
]

Example 4:
Goal: "Plan my week considering my calendar and suggest time for gym."
Response:
[
    "check_calendar()",
    "summarize('calendar_and_recommendations')"
]

Now create a plan for the goal above. Respond ONLY with the JSON list, nothing else.
"""
    
    plan_str = _get_gemini_response_sync(plan_prompt)
    
    # Try to extract JSON from the response
    try:
        # Remove markdown code blocks if present
        plan_str = plan_str.replace('```json', '').replace('```', '').strip()
        plan = json.loads(plan_str)
        print(f"✅ Plan created: {len(plan)} steps")
        for i, step in enumerate(plan, 1):
            print(f"   {i}. {step}")
    except Exception as e:
        print(f"❌ Agent failed to create a valid plan: {e}")
        print(f"Raw response: {plan_str}")
        await send_email_to_recipient(
            recipient_email=user_email,
            subject="AURION Task Failed ❌",
            body=f"Sorry, I failed to create a plan for your goal: {goal}\n\nError: {e}"
        )
        return

    # --- STEP 2: EXECUTE THE PLAN ---
    print("\n⚙️ Step 2: Executing plan...")
    
    # This context dictionary will hold the results from each step
    execution_context = {
        "goal": goal,
        "plan": plan,
        "search_results": [],
        "summary": ""
    }
    
    for step_num, step in enumerate(plan, 1):
        try:
            print(f"\n🔧 Executing Step {step_num}/{len(plan)}: {step}")
            
            # --- Tool: search_and_scrape ---
            if step.startswith("search_and_scrape"):
                # Extract the query from the tool call
                # Format: search_and_scrape('query here')
                query_match = re.search(r"search_and_scrape\(['\"](.+?)['\"]\)", step)
                if not query_match:
                    print(f"⚠️ Could not extract query from: {step}")
                    continue
                
                query = query_match.group(1)
                print(f"   📡 Searching for: {query}")
                
                # Execute search
                search_links = await search_web(query)
                
                if search_links:
                    print(f"   📄 Found {len(search_links)} results, scraping...")
                    
                    # Scrape all results
                    tasks = [
                        scrape_page_content(item["source"]) 
                        for item in search_links 
                        if item.get("source")
                    ]
                    scraped_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Add successful scrapes to context
                    for i, result in enumerate(scraped_results):
                        if not isinstance(result, Exception) and result:
                            execution_context["search_results"].append({
                                "query": query,
                                "source": search_links[i]["source"],
                                "content": result[:2000]  # Limit to 2000 chars per result
                            })
                    
                    print(f"   ✅ Scraped {len(execution_context['search_results'])} pages successfully")
                else:
                    print(f"   ⚠️ No search results found")

            # --- Tool: check_calendar ---
            elif step.startswith("check_calendar"):
                print(f"   📅 Checking user's calendar...")
                
                # Import the calendar function from auth_flow.py
                from app.auth_flow import get_calendar_service_for_user
                import datetime
                
                try:
                    service = await get_calendar_service_for_user(user_id)
                    
                    if service:
                        # Fetch calendar events (run in thread pool since Google API is sync)
                        def fetch_events():
                            now = datetime.datetime.utcnow().isoformat() + 'Z'
                            events_result = service.events().list(
                                calendarId='primary', 
                                timeMin=now,
                                maxResults=10, 
                                singleEvents=True,
                                orderBy='startTime'
                            ).execute()
                            return events_result.get('items', [])
                        
                        # Run sync Google API call in thread pool
                        loop = asyncio.get_event_loop()
                        events = await loop.run_in_executor(None, fetch_events)
                        
                        formatted_events = []
                        for event in events:
                            start = event['start'].get('dateTime', event['start'].get('date'))
                            formatted_events.append({
                                "summary": event.get('summary', 'No title'),
                                "start": start
                            })
                        
                        execution_context["calendar_events"] = formatted_events
                        print(f"   ✅ Retrieved {len(formatted_events)} calendar events")
                    else:
                        execution_context["calendar_events"] = []
                        execution_context["calendar_error"] = "AUTH_REQUIRED"
                        print(f"   ⚠️ Calendar not connected for user {user_id}")
                        print(f"      User can connect at /api/v1/auth/google/login?user_id={user_id}")
                        
                except Exception as e:
                    print(f"   ⚠️ Calendar check failed: {e}")
                    execution_context["calendar_events"] = []
                    execution_context["calendar_error"] = str(e)

            # --- Tool: summarize ---
            elif step.startswith("summarize"):
                print(f"   🎯 Summarizing all gathered data...")
                
                # Get all previous data including calendar events
                full_context_parts = []
                
                if execution_context.get("search_results"):
                    full_context_parts.append("SEARCH RESULTS:\n" + json.dumps(execution_context["search_results"], indent=2))
                
                if execution_context.get("calendar_events"):
                    full_context_parts.append("\nCALENDAR EVENTS:\n" + json.dumps(execution_context["calendar_events"], indent=2))
                
                full_context = "\n\n".join(full_context_parts)
                
                summary_prompt = f"""
You are AURION, an AI assistant. A user asked you to work on this goal:

GOAL: "{goal}"

You have gathered the following information:

{full_context[:15000]}

Please create a comprehensive, well-structured report that directly addresses the user's goal.
Be specific, actionable, and include relevant details, links, and recommendations.

If calendar events were provided, consider them when making suggestions (e.g., avoid times with conflicts).

Format your response in a clear, readable way with sections and bullet points.
"""
                
                print(f"   🤖 Generating summary with Gemini...")
                summary = _get_gemini_response_sync(summary_prompt)
                execution_context["summary"] = summary
                print(f"   ✅ Summary generated ({len(summary)} chars)")
            
            else:
                print(f"   ⚠️ Unknown tool: {step}")
                
        except Exception as e:
            print(f"   ❌ Step failed: {e}")
            execution_context[f"error_step_{step_num}"] = str(e)

    # --- STEP 3: REPORT BACK TO USER ---
    print("\n📧 Step 3: Sending final report...")
    
    # Use the summary if available, otherwise dump the raw context
    final_report = execution_context.get("summary")
    
    if not final_report:
        # Fallback to formatted JSON if no summary was generated
        final_report = f"Data gathered:\n\n{json.dumps(execution_context['search_results'], indent=2)}"
    
    # Format the email
    email_subject = f"✅ Your AURION plan for '{goal}' is complete!"
    email_body = f"""Hi there,

I've finished working on your goal: "{goal}"

Here is my comprehensive report:

{final_report}

---

This report was generated by your AURION autonomous agent.
If you need more information, just ask!

Best regards,
AURION 🤖
"""
    
    try:
        await send_email_to_recipient(
            recipient_email=user_email,
            subject=email_subject,
            body=email_body
        )
        print(f"✅ Report emailed to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🎉 AUTONOMOUS AGENT FINISHED for {user_id}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
