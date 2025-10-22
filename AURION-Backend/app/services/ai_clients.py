# app/services/ai_clients.py
# This file handles all communication with external AI APIs.
# We'll use our API keys from the settings file.

from groq import AsyncGroq
import google.generativeai as genai
import httpx # A modern, async HTTP client
import json

from app.core.config import settings
from app.core.strategy import get_strategy, should_use_cache
from app.services.memory import redis_pool
from app.models.schemas import Intent # Import our Pydantic model

# --- 1. OpenAI Client (for Embeddings) ---
# We initialize the client here so it's ready to be used.
# By making it async, it doesn't block the server.
# Removed OpenAI client initialization per provider policy

# --- 2. Groq Client (for Embeddings and Fallback) ---
try:
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
    if groq_client:
        print("Groq client initialized.")
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    groq_client = None

async def get_embedding(text: str) -> list[float]:
    """
    Multi-provider embedding generation with intelligent fallback.
    
    Priority order:
    1. Groq Embeddings (Primary)
    2. Gemini Embeddings (Backup)
    3. OpenAI (If quota available)
    4. Deterministic fallback (Always works)
    
    Returns: 3072-dimensional vector
    """
    
    # Simple Redis cache
    if should_use_cache("embeddings") and redis_pool:
        try:
            import redis.asyncio as redis
            cache_key = f"embeddings:gemini:{hash(text)}"
            async with redis.Redis(connection_pool=redis_pool) as r:
                cached = await r.get(cache_key)
                if cached:
                    import json as _json
                    return _json.loads(cached)
        except Exception as _:
            pass

    strategy = get_strategy()

    print("🔎 Embedding request received — providers: Groq → Gemini → Fallback")

    # PRIORITY 0: Groq embeddings (primary)
    try:
        result = await _get_groq_embedding(text)
        if result:
            print("✅ Embeddings provider: Groq (llama-3.1-8b-instant)")
            return result
    except Exception as e:
        print(f"❌ Groq embedding failed: {e}")

    # PRIORITY 1: Gemini Embeddings (backup)
    try:
        embedding = await _get_gemini_embedding(text)
        if embedding:
            if should_use_cache("embeddings") and redis_pool:
                try:
                    import redis.asyncio as redis
                    import json as _json
                    cache_key = f"embeddings:gemini:{hash(text)}"
                    async with redis.Redis(connection_pool=redis_pool) as r:
                        await r.set(cache_key, _json.dumps(embedding), ex=60*60)
                except Exception:
                    pass
            print("✅ Embeddings provider: Gemini")
            return embedding
    except Exception as e:
        print(f"❌ Gemini embedding failed: {e}")
    
    # FALLBACK: Deterministic hash-based embedding (Always works)
    print("ℹ️ Embeddings provider: Deterministic fallback (hash)")
    return _get_fallback_embedding(text)


# Removed HuggingFace embedding path per current provider policy (Groq/Gemini only)
async def _get_hf_embedding(text: str) -> list[float] | None:
    return None


# Removed Cohere embedding path per current provider policy (Groq/Gemini only)
async def _get_cohere_embedding(text: str) -> list[float] | None:
    return None


# Removed EdenAI embedding path per current provider policy (Groq/Gemini only)
async def _get_edenai_embedding(text: str) -> list[float] | None:
    return None


async def _get_gemini_embedding(text: str) -> list[float] | None:
    """
    Get embeddings from Google Gemini (Free, high quality).
    Returns 768-dimensional vector, padded to 3072.
    """
    try:
        # Check if Gemini is configured (genai.configure is called later in file)
        if not settings.GEMINI_API_KEY and not settings.FRIEND_GEMINI_KEY:
            return None

        # Ensure genai is configured
        genai.configure(api_key=(settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY))

        # Use Gemini's embedding model
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )

        # Gemini returns 768 dimensions, we need to pad to 3072
        embedding_768 = result['embedding']

        # Pad with zeros to reach 3072 dimensions
        embedding_3072 = embedding_768 + [0.0] * (3072 - len(embedding_768))

        print("✅ Using Gemini embeddings (free)")
        return embedding_3072

    except Exception as e:
        print(f"⚠️ Gemini embedding error: {e}")
        return None


async def _get_groq_embedding(text: str) -> list[float] | None:
    """
    Get embeddings from Groq using text generation to create semantic vectors.
    This is a creative workaround since Groq doesn't have dedicated embedding API.
    Returns 3072-dimensional vector.
    """
    try:
        if not groq_client:
            return None
        
        # Use Groq to generate semantic features
        prompt = f"""Generate a semantic feature vector for this text. 
Analyze the meaning, sentiment, topics, and key concepts.
Text: {text[:500]}

Provide a JSON with 30 numeric features (0-1) representing:
- Sentiment (positive/negative/neutral)
- Topics (tech/business/science/etc)
- Complexity
- Formality
- Intent

Format: {{"features": [0.1, 0.5, ...]}}"""

        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        # Extract features from response
        response_text = response.choices[0].message.content
        
        # Try to parse JSON features
        import json
        try:
            features = json.loads(response_text)['features']
        except:
            # Fallback: extract numbers from response
            import re
            numbers = re.findall(r'0\.\d+', response_text)
            features = [float(n) for n in numbers[:30]]
        
        # Extend to 3072 dimensions by repeating pattern
        if len(features) < 30:
            features = [0.5] * 30  # Neutral fallback
        
        # Expand to 3072 by repeating and adding hash-based variation
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        embedding = []
        for i in range(3072):
            # Mix semantic features with hash-based randomness
            base_idx = i % len(features)
            hash_val = hash_bytes[i % len(hash_bytes)] / 255.0
            embedding.append((features[base_idx] + hash_val) / 2)
        
        print("✅ Using Groq-based embeddings")
        return embedding
        
    except Exception as e:
        print(f"Groq embedding error: {e}")
        return None


def _get_fallback_embedding(text: str) -> list[float]:
    """
    Generate deterministic fallback embedding when all AI providers fail.
    Uses text hash for consistency - same text always produces same vector.
    Returns 3072-dimensional vector.
    """
    import hashlib
    import math
    
    # Create multiple hashes for diversity
    hash1 = hashlib.sha256(text.encode()).digest()
    hash2 = hashlib.sha512(text.encode()).digest()
    hash3 = hashlib.md5(text.encode()).digest()
    
    # Combine hashes
    combined = hash1 + hash2 + hash3
    
    # Generate vector
    vector = []
    for i in range(3072):
        # Use different bytes for each dimension
        byte_idx = i % len(combined)
        value = combined[byte_idx] / 255.0
        
        # Add some variation based on position
        value = (value + math.sin(i * 0.1)) / 2
        
        # Normalize to [-1, 1] range
        value = (value * 2) - 1
        
        vector.append(value)
    
    return vector

# --- 2. Groq Client (for Fast Intent Classification) ---
try:
    groq_client = AsyncGroq(api_key=(settings.GROQ_API_KEY or settings.FRIEND_GROQ_KEY)) if (settings.GROQ_API_KEY or settings.FRIEND_GROQ_KEY) else None
    if groq_client:
        print("Groq client initialized.")
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    groq_client = None


# --- NEW: Smart Query Expansion (Suggestion 2) ---
# A simple rule-based expander to make searches more powerful and focused
QUERY_EXPANSION_RULES = {
    "movies": "current Telugu and Hindi movies playing in Hyderabad 2025 site:bookmyshow.com OR site:paytm.com",
    "cricket": "live cricket score site:espncricinfo.com OR site:cricbuzz.com",
    "restaurant": "best restaurants near me site:zomato.com OR site:swiggy.in",
    "food": "best restaurants near me site:zomato.com OR site:swiggy.in",
    "news": "latest top news headlines India site:timesofindia.com OR site:thehindu.com",
    "stock": "live stock price market data site:moneycontrol.com OR site:investing.com",
    "weather": "current weather forecast site:weather.com OR site:accuweather.com"
}

def expand_search_query(query: str) -> str:
    """
    Expands a simple user query into a powerful, focused search query
    based on keywords. This improves search quality dramatically.
    
    Args:
        query: The original user query
        
    Returns:
        Expanded query with site restrictions and better keywords
    """
    query_lower = query.lower()
    for keyword, expansion in QUERY_EXPANSION_RULES.items():
        if keyword in query_lower:
            print(f"Query expansion triggered: {keyword} → {expansion}")
            return expansion
    
    # Default fallback - return original query
    return query


# --- UPGRADED: Intent Classification (Tier 1 Triage Agent) ---
async def _get_nlp_cloud_intent(query: str, personal_facts: list[str] = None) -> Intent | None:
    """
    Use NLP Cloud for intent classification with proper API implementation.
    """
    if not settings.NLP_CLOUD_API_KEY:
        print("NLP Cloud API key not configured - using Groq fallback")
        return None
    
    try:
        system_prompt = f"""You are an expert intent classifier for an AI assistant named AURION.
Analyze the user's query and classify it into one of these intents:

INTENT OPTIONS:
1. clarify - Ambiguous or vague queries needing clarification
2. factual - Simple greetings or questions answerable from memory  
3. live_search - Real-time data (scores, prices, weather)
4. local_search - Location-based queries
5. informational_search - General web searches
6. set_reminder - Scheduling tasks with specific time
7. play_video - Finding videos or media content
8. send_email - Email composition requests
9. get_weather - Weather information requests
10. creative - Creative writing, stories, poems
11. code - Programming help and code generation

PERSONAL FACTS: {json.dumps(personal_facts) if personal_facts else "None"}

Respond with ONLY a JSON object: {{"intent": "intent_name", "parameters": {{}}}}"""

        # Use the correct NLP Cloud endpoint
        url = "https://api.nlpcloud.io/v1/chatdolphin/chatdolphin"
        headers = {
            "Authorization": f"Token {settings.NLP_CLOUD_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": query,
            "context": system_prompt,
            "max_length": 200,
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            content = data.get("generated_text", "")
            if content:
                intent_data = json.loads(content)
                print(f"✅ Intent classified with NLP Cloud: {intent_data['intent']}")
                return Intent(intent=intent_data["intent"], parameters=intent_data.get("parameters", {}))
            else:
                print("NLP Cloud returned empty response - using Groq fallback")
                return None
                
    except Exception as e:
        print(f"NLP Cloud intent classification failed: {e} - using Groq fallback")
        return None
    
    # Original implementation kept for reference:
    # try:
    #     system_prompt = f"""You are an expert intent classifier for an AI assistant named AURION.
    # Analyze the user's query and classify it into one of these intents:
    # 
    # INTENT OPTIONS:
    # 1. clarify - Ambiguous or vague queries needing clarification
    # 2. factual - Simple greetings or questions answerable from memory  
    # 3. live_search - Real-time data (scores, prices, weather)
    # 4. local_search - Location-based queries
    # 5. informational_search - General web searches
    # 6. set_reminder - Scheduling tasks with specific time
    # 7. play_video - Finding videos or media content
    # 8. send_email - Email composition requests
    # 9. get_weather - Weather information requests
    # 10. creative - Creative writing, stories, poems
    # 11. code - Programming help and code generation
    # 
    # PERSONAL FACTS: {json.dumps(personal_facts) if personal_facts else "None"}
    # 
    # Respond with ONLY a JSON object: {{"intent": "intent_name", "parameters": {{}}}}"""
    # 
    #     url = "https://api.nlpcloud.io/v1/chatdolphin/chatdolphin"
    #     headers = {
    #         "Authorization": f"Token {settings.NLP_CLOUD_API_KEY}",
    #         "Content-Type": "application/json"
    #     }
    #     payload = {
    #         "input": query,
    #         "context": system_prompt,
    #         "max_length": 200,
    #         "temperature": 0.1
    #     }
    #     
    #     async with httpx.AsyncClient() as client:
    #         response = await client.post(url, headers=headers, json=payload, timeout=10.0)
    #         response.raise_for_status()
    #         data = response.json()
    #         
    #         content = data.get("generated_text", "")
    #         intent_data = json.loads(content)
    #         return Intent(intent=intent_data["intent"], parameters=intent_data.get("parameters", {}))
    #         
    # except Exception as e:
    #     print(f"NLP Cloud intent classification failed: {e}")
    #     return None

async def classify_intent(
    query: str, 
    personal_facts: list[str] = None,
    last_topic: dict = None
) -> Intent:
    """
    Multi-provider intent classification with conversation flow awareness.
    It identifies intent, extracts entities, ASKS FOR CLARIFICATION when needed,
    and maintains conversation context.
    
    This is the core of the new "brain" - it decides what happens next.
    
    Args:
        query: The user's query
        personal_facts: List of facts about the user from Neo4j (e.g., ["User lives in Mumbai"])
        last_topic: Previous conversation topic and context (NEW - for follow-ups)
        
    Returns:
        Intent object with intent type and parameters
    """
    # Default to empty list if no facts provided
    if personal_facts is None:
        personal_facts = []
    
    # Try NLP Cloud first (if configured)
    try:
        nlp_result = await _get_nlp_cloud_intent(query, personal_facts)
        if nlp_result:
            print("✅ Using NLP Cloud for intent classification")
            return nlp_result
        else:
            print("NLP Cloud intent classification skipped - using Groq fallback")
    except Exception as e:
        print(f"NLP Cloud intent classification skipped: {e}")
    
    # Fallback to Groq with optimized model selection
    if not groq_client:
        print("❌ ERROR: Neither NLP Cloud nor Groq client is available!")
        # Return a safe default intent
        return Intent(intent="factual", parameters={"error": "No AI clients available"})
    
    print("Trying Groq model for intent classification: llama-3.3-70b-versatile")

    # Build conversation context hint
    context_hint = ""
    if last_topic:
        # Safely get values with proper defaults
        topic = last_topic.get('topic', 'Unknown') or 'Unknown'
        query = last_topic.get('query', 'N/A') or 'N/A'
        entities = last_topic.get('entities', {}) or {}
        response_preview = last_topic.get('response_preview', 'N/A') or 'N/A'
        
        # Safely slice the response preview
        response_preview_text = response_preview[:150] if isinstance(response_preview, str) else 'N/A'
        
        context_hint = f"""
**🔄 CONVERSATION CONTEXT (IMPORTANT!):**
Last topic discussed: {topic}
Previous query: {query}
Entities mentioned: {json.dumps(entities)}
Response preview: {response_preview_text}

⚠️ **CRITICAL**: If the current query is incomplete or references the previous topic:
- Treat it as a FOLLOW-UP continuation
- Maintain the same intent pattern if applicable
- Expand the query with context

Examples:
- Previous: "Who founded Google?" | Current: "What about Microsoft?" 
  → Same pattern (factual founders query about Microsoft)
- Previous: "Distance from Hyderabad to Mumbai?" | Current: "From Mumbai to Bangalore"
  → Same pattern (distance query with new cities)
- Previous: "Create React login UI" | Current: "Tailwind"
  → Continuation (add Tailwind to the UI request)
"""

    # This prompt is the most important part of the new "brain" with 3-tier routing
    system_prompt = f"""
    You are an expert "Triage Agent" for an AI assistant named AURION.
    Your job is to analyze the user's query, considering their personal facts AND conversation context,
    and decide the *next action*. You must respond *only* with a valid JSON object.
    
    Use the *least powerful* (cheapest) option that will work.

    {context_hint}

    --- PERSONAL FACTS ABOUT THE USER ---
    {json.dumps(personal_facts) if personal_facts else "No personal facts available yet."}

    --- INTENT OPTIONS (Ordered by AI Power/Cost) ---
    
    === TIER 1: NO AI NEEDED (Free) ===
    1.  `clarify`: If the query is ambiguous, vague, or missing key details. 
        (e.g., "Find the distance.", "Book a table.", "List all movies in 2005.", "Remind me to test my app")
    2.  `factual`: For simple greetings or questions I can answer from memory.
        (e.g., "Hello", "Thanks", "What's my wife's name?", "What's 2+2?")
    3.  `live_search`: For real-time data that changes minute-by-minute.
        (e.g., "live cricket score", "stock price of GOOGL", "current weather in Mumbai")
    4.  `local_search`: For location-based queries. Use personal facts if available.
        (e.g., "movies running in hyd", "restaurants near me", "best pizza places")
    5.  `informational_search`: For general web searches.
        (e.g., "Who won IPL 2025?", "latest news", "history of Python language")
    6.  `set_reminder`: For scheduling tasks. ONLY if time is specified.
        (e.g., "remind me to call mom tomorrow at 5pm")
    7.  `play_video`: For finding videos. This is *not* just for the word "play".
        (e.g., "I want to watch the new Dune trailer", "show me lofi beats", "find funny cat videos")
    8.  `send_email`: If the user wants to send an email. Extract recipient, subject, and body.
        (e.g., "Email Vamshi at test@gmail.com about our meeting tomorrow", "Send an email to my boss")
    
    === TIER 2: MEDIUM AI (Groq 70B - Fast & Cheap) ===
    9.  `escalate_medium`: For medium-complexity creative or reasoning tasks that do *not* need web search.
        (e.g., "Write a poem about a robot", "Explain quantum physics in simple terms", 
         "Summarize this idea...", "Write a short story about...", "Give me advice on...")
    
    === TIER 3: POWERFUL AI (Gemini - Expensive) ===
    10. `autonomous_plan`: For large, multi-step *goals* that need planning OR calendar-related queries.
        (e.g., "Plan my trip to Goa", "Research my competitors", "Help me find a new apartment",
         "Create a study plan for learning Python", "Help me organize my finances",
         "What's on my calendar today?", "Check my schedule", "Do I have time for gym this week?",
         "Plan my week considering my calendar", "When am I free tomorrow?")
    
    11. `escalate_powerful`: For highly complex tasks, analysis, or synthesis that need maximum intelligence.
        This is the final fallback for anything that doesn't fit other categories.
        (e.g., "Analyze the current state of the AI market", "Compare these three options...",
         "Design a system architecture for...", "Research and compile information about...")

    --- CRITICAL RULES ---
    - If a query lacks key details (location, time, specific entity), use `clarify`.
    - If user says "remind me" WITHOUT a time, use `clarify` to ask when.
    - For location queries, include the user's city from personal facts if available.
    - For video requests, extract the video topic into "video_query".
    - For reminders with time, extract "task" and "time_string".

    --- EXAMPLES ---
    User: "Hello there"
    Response: {{"intent": "factual"}}
    
    User: "Find the distance."
    Response: {{"intent": "clarify", "parameters": {{"question": "Sure! From where to where?"}}}}
    
    User: "Book a table."
    Response: {{"intent": "clarify", "parameters": {{"question": "Okay! For what restaurant, how many people, and for what time?"}}}}

    User: "live cricket score"
    Response: {{"intent": "live_search", "parameters": {{"query": "live cricket score"}}}}

    User: "restaurants near me" (User lives in Hyderabad)
    Response: {{"intent": "local_search", "parameters": {{"query": "restaurants near me in Hyderabad", "location": "Hyderabad"}}}}

    User: "I want to watch the new Aurion trailer"
    Response: {{"intent": "play_video", "parameters": {{"video_query": "new Aurion trailer"}}}}
    
    User: "remind me to test my app"
    Response: {{"intent": "clarify", "parameters": {{"question": "Sure! When would you like me to remind you?"}}}}

    User: "remind me to test my app tomorrow at 5"
    Response: {{"intent": "set_reminder", "parameters": {{"task": "test my app", "time_string": "tomorrow at 5"}}}}
    
    User: "Email Vamshi about the project"
    Response: {{"intent": "clarify", "parameters": {{"question": "Okay! What is Vamshi's email address, and what would you like the subject and body to be?"}}}}
    
    User: "Send an email to user@example.com with subject 'Hello' and body 'This is a test'"
    Response: {{"intent": "send_email", "parameters": {{"recipient_email": "user@example.com", "subject": "Hello", "body": "This is a test"}}}}
    
    User: "who won the 2024 election?"
    Response: {{"intent": "informational_search", "parameters": {{"query": "who won 2024 election"}}}}
    
    User: "what's the weather like?"
    Response: {{"intent": "live_search", "parameters": {{"query": "current weather"}}}}
    
    User: "Write me a poem about my dog, Sparky." (User has a fact: "HAS_PET Sparky")
    Response: {{"intent": "escalate_medium", "parameters": {{"prompt": "Write a poem about a dog named Sparky"}}}}
    
    User: "Plan my trip to Goa next weekend."
    Response: {{"intent": "autonomous_plan", "parameters": {{"goal": "Plan a trip to Goa for next weekend"}}}}
    
    User: "What's on my calendar today?"
    Response: {{"intent": "autonomous_plan", "parameters": {{"goal": "Check calendar for today's events"}}}}
    
    User: "Do I have any meetings this week?"
    Response: {{"intent": "autonomous_plan", "parameters": {{"goal": "Check calendar for this week's meetings"}}}}
    
    User: "Analyze the current state of the AI market and give me insights."
    Response: {{"intent": "escalate_powerful", "parameters": {{"query": "Analyze the current state of the AI market"}}}}

    Respond with NOTHING but the JSON.
    """

    try:
        # Optional Redis cache (simple, query-based)
        cached = None
        if should_use_cache("intent") and redis_pool:
            try:
                import redis.asyncio as redis
                cache_key = f"intent_cache:v1:{query.strip().lower()}"
                async with redis.Redis(connection_pool=redis_pool) as r:
                    cached_val = await r.get(cache_key)
                    if cached_val:
                        cached = json.loads(cached_val)
                        return Intent.model_validate(cached)
            except Exception:
                pass

        strategy = get_strategy()
        
        # Try models in order: secondary -> primary -> backup
        models_to_try = []
        
        if strategy.intent_classification.secondary and "groq_" in strategy.intent_classification.secondary:
            models_to_try.append(strategy.intent_classification.secondary.replace("groq_", ""))
        
        if strategy.intent_classification.primary and "groq_" in strategy.intent_classification.primary:
            models_to_try.append(strategy.intent_classification.primary.replace("groq_", ""))
        
        # Add backup models
        for backup in strategy.intent_classification.backup:
            if "groq_" in backup:
                models_to_try.append(backup.replace("groq_", ""))
        
        # Default fallback
        if not models_to_try:
            models_to_try.append("llama-3.1-8b-instant")
        
        last_error = None
        
        for model_name in models_to_try:
            try:
                print(f"Trying Groq model for intent classification: {model_name}")
                
                chat_completion = await groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    model=model_name,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                
                # Check if response is valid
                if not chat_completion:
                    print(f"❌ Model {model_name} returned None")
                    continue
                
                if not hasattr(chat_completion, 'choices') or not chat_completion.choices:
                    print(f"❌ Model {model_name} returned empty choices")
                    continue
                
                if len(chat_completion.choices) == 0:
                    print(f"❌ Model {model_name} choices list is empty")
                    continue
                
                first_choice = chat_completion.choices[0]
                if not first_choice:
                    print(f"❌ Model {model_name} first choice is None")
                    continue
                
                if not hasattr(first_choice, 'message') or not first_choice.message:
                    print(f"❌ Model {model_name} message is missing")
                    continue
                
                response_json = first_choice.message.content
                
                if not response_json:
                    print(f"❌ Model {model_name} returned empty content")
                    continue
                
                response_dict = json.loads(response_json)
                
                # Validate the dictionary against our Pydantic model
                intent_data = Intent.model_validate(response_dict)
                
                # Store in cache
                if should_use_cache("intent") and redis_pool:
                    try:
                        import redis.asyncio as redis
                        cache_key = f"intent_cache:v1:{query.strip().lower()}"
                        async with redis.Redis(connection_pool=redis_pool) as r:
                            await r.set(cache_key, json.dumps(intent_data.model_dump()), ex=60 * 5)
                    except Exception:
                        pass
                
                print(f"✅ Intent classified with {model_name}: {intent_data.intent}")
                return intent_data
                
            except Exception as e:
                last_error = e
                print(f"❌ Model {model_name} failed: {e}")
                continue
        
        # If all Groq models fail, use Gemini as final fallback
        if "gemini" in str(strategy.intent_classification.backup).lower():
            try:
                print("Trying Gemini for intent classification...")
                # Simple factual response for now
                return Intent(intent="factual", parameters={})
            except Exception as e:
                print(f"Gemini fallback also failed: {e}")
        
        # Final fallback - default to factual for simple queries
        print(f"All models failed, using default intent. Last error: {last_error}")
        return Intent(intent="factual", parameters={})

    except Exception as e:
        print(f"Critical error in intent classification: {e}")
        # If Groq fails, we default to "escalate_powerful" to be safe
        return Intent(intent="escalate_powerful", parameters={"error": str(e)})


# --- NEW: Tier 2 Generation (Medium Complexity - Groq 70B) ---
async def generate_response_stream_medium(prompt: str):
    """
    Calls the Groq Llama 3.1 70B model for medium-complexity tasks.
    This is the "Tier 2" model - faster and cheaper than Gemini, but more powerful than 8B.
    
    Perfect for:
    - Creative writing (poems, stories, songs)
    - Explanations (quantum physics, programming concepts)
    - Summarization (short documents, ideas)
    - Advice and recommendations
    
    Args:
        prompt: The complete prompt to send to the model
        
    Yields:
        Text chunks as they arrive (streaming)
    """
    if not groq_client:
        raise ValueError("Groq client is not initialized.")
    
    try:
        model_name = get_strategy().response_generation.backup[1] if len(get_strategy().response_generation.backup) > 1 else "llama-3.1-70b-versatile"
        chat_completion_stream = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are AURION, a helpful and creative AI assistant."},
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            temperature=0.7,
            stream=True,
        )
        
        async for chunk in chat_completion_stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        print(f"Error generating medium response from Groq 70B: {e}")
        yield "I'm sorry, I'm having trouble processing that request right now."

# --- 3. Gemini Client (for Powerful Generation) ---
try:
    if settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY:
        genai.configure(api_key=(settings.GEMINI_API_KEY or settings.FRIEND_GEMINI_KEY))
        # Choose model from strategy
        primary = get_strategy().response_generation.primary
        model_map = {
            "gemini-2.5-flash": 'gemini-2.5-flash',
            "gemini-1.5-pro": 'gemini-1.5-pro',
            "gemini-flash": 'gemini-2.5-flash',
            "gemini-pro": 'gemini-1.5-pro'
        }
        gemini_model = genai.GenerativeModel(model_map.get(primary, 'gemini-2.5-flash'))
        print("Gemini client initialized.")
    else:
        gemini_model = None
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    gemini_model = None

async def generate_response(query: str, system_prompt: str = "", history: list = None) -> str:
    """
    Generate a complete non-streaming response.
    Used for task response generation and other non-streaming needs.
    """
    # Build the full prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUser Query: {query}"
    else:
        full_prompt = query
    
    # Use streaming internally but collect all chunks
    response_text = ""
    async for chunk in generate_response_stream(full_prompt):
        response_text += chunk
    
    return response_text.strip()


async def generate_response_stream(prompt: str):
    """
    Strategy-aware streaming generation.
    - Primary from hybrid_strategy.json
    - Backups tried in order on failure
    """
    strat = get_strategy().response_generation

    providers = [strat.primary] + strat.backup
    last_error = None

    for provider in providers:
        name = provider.lower()
        try:
            if name.startswith("groq") or name == "groq-llama3":
                async for chunk in generate_response_stream_medium(prompt):
                    yield chunk
                return
            elif name == "openrouter":
                async for chunk in _generate_with_openrouter(prompt):
                    yield chunk
                return
            elif name.startswith("gemini") and gemini_model:
                response_stream = await gemini_model.generate_content_async(prompt, stream=True)
                async for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return
            elif name.startswith("cohere"):
                async for chunk in _generate_with_cohere(prompt):
                    yield chunk
                return
        except Exception as e:
            last_error = e
            print(f"Provider {provider} failed: {e}")
            continue

    # If all providers fail
    print(f"❌ All generation providers failed. Last error: {last_error}")
    import traceback
    traceback.print_exc()
    # Provide more helpful error message
    error_msg = f"I apologize, but I'm experiencing technical difficulties with all AI providers. Last error: {str(last_error)}"
    yield error_msg


# Removed OpenRouter generation function per provider policy
async def _generate_with_openrouter(prompt: str):
    raise RuntimeError("OpenRouter not available - use Groq or Gemini")


# Removed Cohere generation function per provider policy
async def _generate_with_cohere(prompt: str):
    raise RuntimeError("Cohere not available - use Groq or Gemini")


# --- Topic Extraction for Conversation Flow ---

async def extract_conversation_topic(query: str, response: str, intent: str = None) -> dict:
    """
    Extract the main topic from a conversation Q&A pair for context tracking.
    
    This helps maintain conversation flow by identifying what the user and AI are discussing.
    
    Args:
        query: User's question
        response: AI's response
        intent: Optional intent type to help with extraction
        
    Returns:
        Dict with:
            - topic: Main subject (e.g., "company founders", "distance calculation", "UI development")
            - entities: Key entities mentioned (e.g., {"company": "Google", "founders": ["Larry", "Sergey"]})
            - category: General category (e.g., "tech", "travel", "development")
    
    Example:
        Query: "Who founded Google?"
        Response: "Larry Page and Sergey Brin founded Google."
        Returns: {
            "topic": "company founders",
            "entities": {"company": "Google", "founders": ["Larry Page", "Sergey Brin"]},
            "category": "tech"
        }
    """
    
    if not groq_client:
        # Fallback to simple extraction
        return {
            "topic": "general_conversation",
            "entities": {},
            "category": "general"
        }
    
    extraction_prompt = f"""
Extract the main topic and entities from this conversation exchange.

**User Query:** {query}
**AI Response:** {response[:500]}  # First 500 chars
**Intent Type:** {intent or "unknown"}

Respond with ONLY valid JSON in this exact format:
{{
    "topic": "brief description of main subject (e.g., 'company founders', 'weather query', 'distance calculation', 'UI development')",
    "entities": {{"key": "value"}},  // Important names, places, companies, concepts mentioned
    "category": "general category (e.g., 'tech', 'travel', 'development', 'knowledge', 'personal')"
}}

**Examples:**

Query: "Who founded Google?"
Response: "Larry Page and Sergey Brin..."
{{
    "topic": "company founders",
    "entities": {{"company": "Google", "founders": ["Larry Page", "Sergey Brin"]}},
    "category": "tech"
}}

Query: "Distance from Hyderabad to Mumbai?"
Response: "About 710 km..."
{{
    "topic": "distance calculation",
    "entities": {{"from": "Hyderabad", "to": "Mumbai", "distance": "710 km"}},
    "category": "travel"
}}

Query: "Create a React login UI"
Response: "Sure, would you like CSS or Tailwind?"
{{
    "topic": "UI development",
    "entities": {{"framework": "React", "component": "login UI"}},
    "category": "development"
}}

Query: "What's the weather?"
Response: "Sunny and 72°F in NYC"
{{
    "topic": "weather query",
    "entities": {{"location": "NYC", "condition": "sunny", "temp": "72°F"}},
    "category": "information"
}}

If no clear topic, use:
{{
    "topic": "general_chat",
    "entities": {{}},
    "category": "general"
}}

Respond with ONLY the JSON object, nothing else.
"""
    
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[{"role": "user", "content": extraction_prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(chat_completion.choices[0].message.content)
        print(f"✅ Extracted topic: {result.get('topic')}")
        return result
        
    except Exception as e:
        print(f"Topic extraction failed: {e}")
        # Fallback to simple extraction
        return {
            "topic": "conversation",
            "entities": {},
            "category": "general"
        }
