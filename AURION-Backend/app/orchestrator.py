# app/orchestrator.py
"""
AURION Orchestrator - Main intelligence hub
Handles all chat requests with priority-based universal task detection
Now with intelligent search, context awareness, and smart model routing
"""

import logging
from typing import AsyncGenerator, Dict, Any, Optional
import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

# Import performance monitoring utilities
from app.utils.performance_monitor import monitor_performance
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.rate_limiter import RateLimiter

from app.models.schemas import ChatRequest, MiniAgentRequest
from app.services.conversation_state import ConversationStateManager
from app.services import ai_clients
from app.services import tools
from app.services.personality import PersonalityEngine
from app.services import memory
from app.services.natural_language_task_parser import NaturalLanguageTaskParser
from app.services.smart_task_responder import SmartTaskResponder
from app.services.session_manager import get_session_manager
from app.auth_db import get_user_by_email, get_current_user

# Import new intelligent services
from app.services.intelligent_search import intelligent_search
from app.services.context_intelligence import context_intelligence
from app.services.model_router import model_router

logger = logging.getLogger(__name__)

# Create FastAPI router
chat_router = APIRouter()

# Initialize performance monitoring
mini_agent_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
rate_limiter = RateLimiter()

# Initialize services
# Note: state_manager will be initialized lazily when first needed
# because redis_pool is not available until app startup completes
state_manager = None
_state_manager_initialized = False

def get_state_manager():
    """Lazy initialization of state_manager"""
    global state_manager, _state_manager_initialized
    
    if _state_manager_initialized:
        return state_manager
    
    try:
        from app.services.memory import redis_pool
        if redis_pool:
            state_manager = ConversationStateManager(redis_pool)
            logger.info("✅ ConversationStateManager initialized with Redis")
        else:
            logger.warning("⚠️ Redis pool is None, state_manager not initialized")
            state_manager = None
    except Exception as e:
        logger.error(f"❌ Could not initialize state_manager with redis: {e}")
        state_manager = None
    
    _state_manager_initialized = True
    return state_manager

personality_engine = PersonalityEngine()
nl_task_parser = NaturalLanguageTaskParser()
smart_responder = SmartTaskResponder(ai_clients)

# Available tools - commented out for now, not critical for basic functionality
# AVAILABLE_TOOLS = [
#     {
#         "name": "web_search",
#         "description": "Search the web for current information, news, facts",
#         "function": tools.web_search
#     },
#     {
#         "name": "video_search",
#         "description": "Search for videos on a specific topic",
#         "function": tools.video_search
#     },
#     {
#         "name": "schedule_reminder",
#         "description": "Schedule a reminder or task for the user",
#         "function": tools.schedule_reminder
#     }
# ]


# ==================== FASTAPI ENDPOINTS ====================

@chat_router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Main chat endpoint with Server-Sent Events streaming
    """
    print(f"Received request on /chat/stream")
    
    async def event_generator():
        try:
            async for chunk in handle_chat_request(request):
                yield {
                    "event": "message",
                    "data": json.dumps(chunk)
                }
        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


# ==================== CORE LOGIC FUNCTIONS ====================

async def stream_text(text: str) -> AsyncGenerator[str, None]:
    """Stream text in small chunks for better UX"""
    words = text.split()
    for i in range(0, len(words), 3):
        chunk = " ".join(words[i:i+3])
        if i + 3 < len(words):
            chunk += " "
        yield chunk
        await asyncio.sleep(0.01)  # Small delay for streaming effect


async def handle_chat_request(
    request: ChatRequest,
    user_profile: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main orchestrator for handling chat requests
    Priority-based flow:
    0.5 - Universal task detection (BEFORE intent classification)
    0.6 - Pending task confirmation handling
    1.0 - Intent classification and routing
    """
    
    query = request.query
    conv_id = request.conversation_id
    
    logger.info(f"Orchestrator: Handling query for conv_id {conv_id}")
    
    try:
        # =================================================================
        # PRIORITY 0.5: UNIVERSAL TASK DETECTION
        # Check if this is a task-related query BEFORE intent classification
        # This catches ANY natural language format
        # =================================================================
        parsed_task = None
        try:
            if nl_task_parser.is_task_query(query):
                print(f"🎯 Universal task detected! Parsing with NL parser...")
                
                # Parse the task using natural language understanding
                parsed_task = await nl_task_parser.parse_task(query)
                
                print(f"📝 Parsed task: description='{parsed_task['description']}', time='{parsed_task['time_display']}', confidence={parsed_task['confidence']:.2f}")
                
                # Validate we have both description and time
                if parsed_task['description'] and parsed_task['scheduled_time_utc']:
                    # Save as pending task for confirmation
                    pending_task_data = {
                        "description": parsed_task['description'],
                        "scheduled_time_utc": parsed_task['scheduled_time_utc'].isoformat(),
                        "time_display": parsed_task['time_display'],
                        "confidence": parsed_task.get("confidence", 0.8)
                    }
                    
                    # Save pending task if state_manager is available
                    state_mgr = get_state_manager()
                    if state_mgr:
                        try:
                            await state_mgr.save_pending_task(request.conversation_id, pending_task_data)
                            logger.info("✅ Pending task saved successfully")
                        except Exception as e:
                            print(f"Error saving pending task: {e}")
                            logger.error(f"Failed to save pending task: {e}", exc_info=True)
                    else:
                        print("⚠️ State manager not available, cannot save pending task")
                    
                    # Generate AI-driven confirmation message (no robotic templates!)
                    confirmation_msg = await smart_responder.generate_confirmation_message(
                        task_description=parsed_task['description'],
                        scheduled_time=parsed_task['scheduled_time_utc'],
                        user_context=user_profile
                    )
                    
                    async for chunk in stream_text(confirmation_msg):
                        yield {"event": "text_chunk", "data": chunk}
                    return
                    
        except Exception as e:
            print(f"❌ Error in universal task parser: {e}")
            import traceback
            print(traceback.format_exc())
        
        # =================================================================
        # PRIORITY 0.6: PENDING TASK CONFIRMATION HANDLING
        # Check if user has a pending task awaiting confirmation
        # =================================================================
        state_mgr = get_state_manager()
        if state_mgr:
            pending_task = await state_mgr.get_pending_task(conv_id)
        else:
            pending_task = None
            
        if pending_task:
            print(f"⚠️ User has pending task: {pending_task['description']}")
            
            # Check if this is a confirmation
            if state_mgr and state_mgr.is_confirmation_phrase(query):
                print(f"✅ User confirmed! Creating task...")
                
                try:
                    # Get user email from database
                    user_data = await get_user_by_email(conv_id)  # conv_id is email
                    user_email = user_data.get("email") if user_data else conv_id
                    
                    # Convert ISO string back to datetime
                    from dateutil import parser as date_parser
                    scheduled_time = date_parser.isoparse(pending_task['scheduled_time_utc'])
                    
                    # Create the task using the new datetime-based function
                    success = await tools.schedule_reminder_with_datetime(
                        description=pending_task['description'],
                        scheduled_time=scheduled_time,
                        user_email=user_email,
                        user_id=conv_id
                    )
                    
                    # Clear pending task
                    if state_mgr:
                        await state_mgr.clear_pending_task(conv_id)
                    
                    if success:
                        # Generate AI-driven success message (unique every time!)
                        response = await smart_responder.generate_success_message(
                            task_description=pending_task['description'],
                            scheduled_time=scheduled_time,
                            user_email=user_email,
                            user_context=user_profile
                        )
                        
                        async for chunk in stream_text(response):
                            yield {"event": "text_chunk", "data": chunk}
                        return
                    else:
                        error_msg = "Hmm, something went wrong scheduling that. Mind trying again? 🤔"
                        async for chunk in stream_text(error_msg):
                            yield {"event": "text_chunk", "data": chunk}
                        return
                        
                except Exception as e:
                    print(f"❌ Error creating task: {e}")
                    import traceback
                    print(traceback.format_exc())
                    
                    error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                    async for chunk in stream_text(error_msg):
                        yield {"event": "text_chunk", "data": chunk}
                    return
            
            # Check if this is a rejection
            elif state_mgr and state_mgr.is_rejection_phrase(query):
                print(f"❌ User rejected task")
                await state_mgr.clear_pending_task(conv_id)
                
                msg = "No problem! I've cancelled the reminder. 👍"
                msg = personality_engine.add_friendly_touches(msg)
                
                async for chunk in stream_text(msg):
                    yield {"event": "text_chunk", "data": chunk}
                return
            
            # Unclear response - re-ask
            else:
                print(f"⚠️ Unclear response, re-asking confirmation")
                msg = f"I'm not sure if you want me to create this reminder:\n\n"
                msg += f"**Task:** {pending_task['description']}\n"
                msg += f"**Time:** {pending_task['time_display']}\n\n"
                msg += f"Please say **'yes'** to confirm or **'no'** to cancel."
                
                response = personality_engine.add_friendly_touches(msg)
                
                async for chunk in stream_text(response):
                    yield {"event": "text_chunk", "data": chunk}
                return
        
        # =================================================================
        # PRIORITY 1.0: CONTEXT INTELLIGENCE - Merge query with context
        # =================================================================
        
        # Get conversation context
        context = context_intelligence.get_context(conv_id)
        
        # Check if this is a follow-up query
        if context_intelligence.is_followup_query(query, context):
            # Merge with previous context
            original_query = query
            query = context_intelligence.merge_with_context(query, context)
            logger.info(f"🔄 Merged query: '{original_query}' → '{query}'")
        
        # Extract entities (location, time, category) from query
        entities = context_intelligence.extract_entities(query, context)
        logger.info(f"📊 Extracted entities: {entities}")
        
        # =================================================================
        # PRIORITY 1.1: INTENT CLASSIFICATION
        # =================================================================
        
        # Get conversation history from memory module
        try:
            history = await memory.get_chat_history(conv_id, limit=10)
        except Exception as e:
            logger.warning(f"Could not get chat history: {e}")
            history = []
        
        # Extract personal facts from user profile for intent classification
        personal_facts = []
        if user_profile:
            if user_profile.get("name"):
                personal_facts.append(f"Name: {user_profile['name']}")
            if user_profile.get("email"):
                personal_facts.append(f"Email: {user_profile['email']}")
            if user_profile.get("location"):
                personal_facts.append(f"Location: {user_profile['location']}")
            if user_profile.get("preferences"):
                for key, value in user_profile.get("preferences", {}).items():
                    personal_facts.append(f"{key}: {value}")
        
        # Get last topic from conversation state
        last_topic = await state_manager.get_last_topic(conv_id)
        
        # Classify intent using ai_clients module
        intent_data = await ai_clients.classify_intent(
            query=query,
            personal_facts=personal_facts,
            last_topic=last_topic
        )
        
        # Extract intent and parameters from Pydantic model
        intent = intent_data.intent
        confidence = 0.9  # High confidence from AI classification
        parameters = intent_data.parameters or {}
        
        # Merge extracted entities into parameters
        parameters.update(entities)
        
        logger.info(f"Intent classified: {intent} (confidence: {confidence})")
        logger.info(f"Parameters: {parameters}")
        
        # =================================================================
        # PRIORITY 1.2: CHECK IF CLARIFICATION NEEDED
        # =================================================================
        
        clarification = context_intelligence.needs_clarification(
            query=query,
            intent=intent,
            entities=entities
        )
        
        if clarification and not context.get('pending_clarification'):
            # Need to ask for clarification
            question = clarification['question']
            
            # Store clarification in context
            context_intelligence.update_context(conv_id, {
                'pending_clarification': clarification,
                'last_query': query,
                'last_intent': intent
            })
            
            # Send clarification question
            response = question
            response = personality_engine.add_friendly_touches(response)
            
            async for chunk in stream_text(response):
                yield {"event": "text_chunk", "data": chunk}
            return
        
        # Clear pending clarification if we have enough info now
        if context.get('pending_clarification') and entities:
            context_intelligence.update_context(conv_id, {
                'pending_clarification': None
            })
        
        # Update context with current query
        context_intelligence.update_context(conv_id, {
            'last_query': query,
            'last_intent': intent,
            'extracted_entities': entities,
            'query_history': context.get('query_history', []) + [query]
        })
        
        # =================================================================
        # HANDLE INTENTS BASED ON CLASSIFICATION WITH MODEL ROUTING
        # =================================================================
        
        # Get optimal model routing
        route_info = model_router.route(query=query, intent=intent, context=context)
        logger.info(f"🎯 Routing: {route_info['reasoning']}")
        
        # TIER 1: Free/Fast Operations
        if intent == "clarify":
            # Ask for clarification
            clarification_question = parameters.get("question", "Can you provide more details?")
            response = clarification_question
            
        elif intent == "factual":
            # Simple greetings or factual questions
            response = await _handle_greeting(query, user_profile)
            
        elif intent == "live_search":
            # Real-time data (weather, stocks, cricket scores)
            search_query = parameters.get("query", query)
            location = parameters.get("location")
            response = await _handle_live_search(search_query, location)
            
        elif intent == "local_search":
            # Location-based search (restaurants, movies, etc.)
            search_query = parameters.get("query", query)
            location = parameters.get("location")
            response = await _handle_local_search(search_query, location)
            
        elif intent == "informational_search":
            # General web search
            search_query = parameters.get("query", query)
            location = parameters.get("location")
            response = await _handle_web_search(search_query, location)
            
        elif intent == "play_video":
            # Video search
            video_query = parameters.get("video_query", query)
            response = await _handle_video_search(video_query)
            
        elif intent == "send_email":
            # Email sending
            recipient = parameters.get("recipient_email")
            subject = parameters.get("subject")
            body = parameters.get("body")
            
            if not all([recipient, subject, body]):
                response = "I need the recipient's email, subject, and body to send an email. Can you provide those?"
            else:
                response = await _handle_send_email(recipient, subject, body, user_profile)
        
        # TIER 2: Medium AI (Groq)
        elif intent == "escalate_medium":
            # Medium complexity creative tasks
            response = await _handle_general_knowledge(query, user_profile)
            
        # TIER 3: Powerful AI (Gemini)
        elif intent == "autonomous_plan":
            # Multi-step planning or calendar queries
            response = await _handle_autonomous_planning(query, user_profile)
            
        elif intent == "escalate_powerful":
            # Complex analysis and synthesis
            response = await _handle_powerful_analysis(query, user_profile)
            
        # Fallback
        else:
            response = await _handle_general(query, user_profile)
        
        # Apply personality
        response = personality_engine.add_friendly_touches(response)
        
        # =================================================================
        # SAVE TO SESSION HISTORY
        # =================================================================
        session_manager = get_session_manager()
        
        # Save user message
        try:
            await session_manager.add_message(
                session_id=conv_id,
                role="user",
                content=query,
                metadata={
                    "intent": intent,
                    "confidence": confidence,
                    "parameters": parameters
                }
            )
        except Exception as e:
            logger.warning(f"Could not save user message to session: {e}")
        
        # Save to memory module (backward compatibility)
        try:
            await memory.add_to_chat_history(conv_id, "user", query)
            await memory.add_to_chat_history(conv_id, "assistant", response)
        except Exception as e:
            logger.warning(f"Could not save to chat history: {e}")
        
        # Save assistant response (after streaming completes)
        # We'll save it before streaming for now, or use background task
        try:
            await session_manager.add_message(
                session_id=conv_id,
                role="assistant",
                content=response,
                metadata={
                    "intent": intent,
                    "personality_applied": True
                }
            )
        except Exception as e:
            logger.warning(f"Could not save assistant message to session: {e}")
        
        # Auto-generate session title from first message
        try:
            session = await session_manager.get_session(conv_id, conv_id)
            if session and session.get("message_count", 0) == 2:  # First exchange
                await session_manager.auto_generate_title(conv_id, conv_id, query)
        except Exception as e:
            logger.debug(f"Could not auto-generate title: {e}")
        
        # Stream response
        async for chunk in stream_text(response):
            yield {"event": "text_chunk", "data": chunk}
            
    except Exception as e:
        logger.error(f"Error in orchestrator: {e}", exc_info=True)
        error_msg = "I encountered an error processing your request. Please try again."
        async for chunk in stream_text(error_msg):
            yield {"event": "text_chunk", "data": chunk}


async def _handle_greeting(query: str, user_profile: Optional[Dict]) -> str:
    """Handle greeting intents"""
    name = user_profile.get("name", "") if user_profile else ""
    
    if name:
        return f"Hey {name}! 😊 How can I help you today?"
    else:
        return "Hey! 😊 How can I help?"


async def _handle_memory_recall(
    query: str,
    conv_id: str,
    user_profile: Optional[Dict]
) -> str:
    """Handle memory recall intents"""
    
    # Simple memory recall using user profile
    if not user_profile:
        return "I don't have any information about you yet. Tell me about yourself!"
    
    # Simple keyword matching
    query_lower = query.lower()
    
    if "name" in query_lower:
        name = user_profile.get("name") if user_profile else None
        if name:
            return f"Your name is {name}! 😊"
        else:
            return "You haven't told me your name yet."
    
    elif "where" in query_lower and "live" in query_lower:
        location = user_profile.get("location") if user_profile else None
        if location:
            return f"You live in {location}! 📍"
        else:
            return "You haven't told me where you live yet."
    
    elif "like" in query_lower or "love" in query_lower or "interest" in query_lower:
        interests = user_profile.get("interests", []) if user_profile else []
        if interests:
            return f"You love {', '.join(interests[:3])}! ✨"
        else:
            return "You haven't shared your interests yet."
    
    else:
        # Return general profile info
        return "I remember our conversations! What would you like to know?"


async def _handle_general_knowledge(
    query: str,
    user_profile: Optional[Dict]
) -> str:
    """Handle general knowledge questions"""
    
    # Get personality guidelines
    guidelines = personality_engine.create_response_guidelines(user_profile or {})
    
    # Generate response using ai_clients module
    response = await ai_clients.generate_response(
        query=query,
        system_prompt=guidelines,
        history=[]
    )
    
    return response


async def _handle_live_search(query: str, location: Optional[str] = None) -> str:
    """Handle live/real-time data searches (weather, stocks, cricket, etc.)"""
    
    try:
        # Use intelligent search with live data focus
        result = await intelligent_search.search(
            query=query,
            search_type='live',
            location=location
        )
        
        if result.get('success'):
            return result['formatted']
        else:
            error_msg = result.get('message', 'Search failed')
            return f"I couldn't fetch live data: {error_msg} 😕"
            
    except Exception as e:
        logger.error(f"Live search error: {e}")
        return "Sorry, I encountered an error fetching live data. Please try again! 🔄"


async def _handle_local_search(query: str, location: Optional[str] = None) -> str:
    """Handle location-based searches (restaurants, movies, places, etc.)"""
    
    try:
        # Use intelligent search with local focus
        result = await intelligent_search.search(
            query=query,
            search_type='local',
            location=location
        )
        
        if result.get('success'):
            return result['formatted']
        else:
            error_msg = result.get('message', 'Search failed')
            return f"I couldn't find local results: {error_msg} 😕"
            
    except Exception as e:
        logger.error(f"Local search error: {e}")
        return "Sorry, I encountered an error searching local results. Please try again! 🔄"


async def _handle_send_email(
    recipient: str,
    subject: str,
    body: str,
    user_profile: Optional[Dict]
) -> str:
    """Handle email sending"""
    
    try:
        # Use the bulletproof email sender
        from app.services.bulletproof_email import send_reminder_email_bulletproof
        
        # Get sender info from user profile
        sender_email = user_profile.get("email", "noreply@aurion.ai") if user_profile else "noreply@aurion.ai"
        
        # Send email
        success = await send_reminder_email_bulletproof(
            to_email=recipient,
            task_description=body,
            task_id=None,
            user_id=sender_email,
            scheduled_time=None
        )
        
        if success:
            return f"✅ Email sent successfully to {recipient}!"
        else:
            return f"❌ Failed to send email to {recipient}. Please check the email address and try again."
            
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return "Sorry, I encountered an error sending the email. Please try again! 📧"


async def _handle_autonomous_planning(
    query: str,
    user_profile: Optional[Dict]
) -> str:
    """Handle multi-step planning and complex goal-oriented tasks"""
    
    try:
        # Use Gemini for powerful planning capabilities
        planning_prompt = f"""
You are an expert AI planner. Create a detailed, actionable plan for the user's goal.
Break down the goal into clear steps, provide timelines, and include helpful tips.

User's Goal: {query}

Provide a comprehensive plan with:
1. Overview and objectives
2. Step-by-step action items
3. Timeline/milestones
4. Tips and considerations
5. Resources needed
"""
        
        response = await ai_clients.generate_response(
            query=query,
            system_prompt=planning_prompt,
            history=[]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Autonomous planning error: {e}")
        return "Sorry, I encountered an error creating the plan. Please try again! 📋"


async def _handle_powerful_analysis(
    query: str,
    user_profile: Optional[Dict]
) -> str:
    """Handle complex analysis, synthesis, and research tasks"""
    
    try:
        # Use Gemini for maximum intelligence
        analysis_prompt = f"""
You are an expert analyst with deep knowledge across multiple domains.
Provide a thorough, well-researched analysis of the user's question.

User's Question: {query}

Provide:
1. Comprehensive analysis
2. Multiple perspectives
3. Data and evidence
4. Practical insights
5. Clear conclusions
"""
        
        response = await ai_clients.generate_response(
            query=query,
            system_prompt=analysis_prompt,
            history=[]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Powerful analysis error: {e}")
        return "Sorry, I encountered an error performing the analysis. Please try again! 🔍"


async def _handle_web_search(query: str, location: Optional[str] = None) -> str:
    """Handle web search requests"""
    
    try:
        # Use intelligent search for informational queries
        result = await intelligent_search.search(
            query=query,
            search_type='general',
            location=location
        )
        
        if result.get('success'):
            return result['formatted']
        else:
            error_msg = result.get('message', 'Search failed')
            return f"I couldn't find results: {error_msg}"
            
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return "Sorry, I encountered an error performing the search."


async def _handle_video_search(query: str) -> str:
    """Handle video search requests"""
    
    try:
        results = await tools.video_search(query)
        
        if results:
            response = "Here are some videos I found:\n\n"
            for i, video in enumerate(results[:3], 1):
                response += f"{i}. **{video['title']}**\n"
                response += f"   👤 {video['channel']}\n"
                response += f"   🔗 {video['url']}\n\n"
            return response
        else:
            return "I couldn't find any videos for that search."
            
    except Exception as e:
        logger.error(f"Video search error: {e}")
        return "Sorry, I encountered an error searching for videos."


async def _handle_general(
    query: str,
    user_profile: Optional[Dict]
) -> str:
    """Handle general queries"""
    
    # Get personality guidelines
    guidelines = personality_engine.create_response_guidelines(user_profile or {})
    
    # Generate response using ai_clients module
    response = await ai_clients.generate_response(
        query=query,
        system_prompt=guidelines,
        history=[]
    )
    
    return response


# ==================== MINI AGENT HANDLER ====================

@monitor_performance("mini_agent_request")
async def handle_mini_agent_request(request: MiniAgentRequest, background_tasks=None):
    """
    Dedicated handler for Inline Mini Agent requests
    100% isolated from main chat - uses separate Pinecone namespace
    """
    try:
        # Rate limiting check
        client_ip = "default"  # In production, get from request context
        if not await rate_limiter.is_allowed(client_ip, 'mini_agent'):
            yield {
                "event": "error",
                "data": "Rate limit exceeded. Please try again later."
            }
            return
        # Build isolated prompt (NO main chat context)
        prompt = f"""
You are a focused AI expert. Your *only* job is to answer the user's "Query" 
based *only* on the provided "Snippet".
Do not use any other knowledge. Be concise and direct.

--- SNIPPET ---
{request.snippet}

--- QUERY ---
{request.query}

--- YOUR ANSWER ---
"""
        
        # Stream response using ai_clients module with circuit breaker
        full_response = ""
        try:
            async for chunk_text in mini_agent_circuit_breaker.call(ai_clients.generate_response_stream, prompt):
                full_response += chunk_text
                yield {
                    "event": "text_chunk",
                    "data": chunk_text
                }
        except Exception as circuit_error:
            logger.warning(f"Circuit breaker triggered for mini agent: {circuit_error}")
            # Fallback response
            fallback_response = f"I'm having trouble processing your request right now. Here's what I can tell you about your snippet: {request.snippet[:100]}..."
            yield {
                "event": "text_chunk",
                "data": fallback_response
            }
            full_response = fallback_response
        
        # Save to isolated memory (mini-threads namespace)
        if background_tasks:
            from app.services.memory import save_mini_thread
            memory_data = {
                "user_id": request.user_id,
                "snippet": request.snippet,
                "query": request.query,
                "response": full_response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            background_tasks.add_task(save_mini_thread, memory_data)
        
        yield {"event": "stream_complete", "data": None}
        
    except Exception as e:
        logger.error(f"Mini agent error: {e}", exc_info=True)
        yield {
            "event": "error",
            "data": str(e)
        }
