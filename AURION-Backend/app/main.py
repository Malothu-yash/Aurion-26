from app import email_service
# app/main.py
# This is the main file that runs our FastAPI application.

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging  # Added for debugging CORS

# Import our settings instance from the config file
from app.core.config import settings

# --- IMPORT OUR NEW SERVICE INITIALIZERS ---
from app.services.memory import (
    init_redis_pool, 
    close_redis_pool, 
    init_pinecone,
    init_neo4j,
    close_neo4j
)
from app.services.tools import scheduler, run_daily_briefing, run_memory_consolidation
from app.core.monitor import log_event
from app.admin.realtime import start_background_tasks
from app.orchestrator import chat_router, handle_mini_agent_request
from app.auth_flow import auth_router
from app.auth_endpoints import router as auth_mongo_router
from app.auth_db import init_mongodb, close_mongodb
from app.admin.routes import router as admin_router

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Application Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function runs ONCE when the app starts.
    This is the perfect place to:
      - Connect to databases (Redis, Pinecone)
      - Initialize our AI clients (they already init on import)
      - Start our APScheduler for reminders
    """
    logger.info("--- AURION Backend is starting up... ---")
    try:
        await log_event("startup", {"component": "backend"})
    except Exception:
        logger.error("Failed to log startup event")
    
    # --- CONNECT TO DATABASES ---
    await init_redis_pool()  # Connect to Redis
    init_pinecone()          # Connect to Pinecone
    init_neo4j()             # Connect to Neo4j (Semantic Memory)
    
    # MongoDB with proper error handling
    mongodb_success = await init_mongodb()
    if not mongodb_success:
        logger.warning("⚠️ MongoDB connection failed - session operations will be limited")
    else:
        logger.info("✅ All databases connected successfully")
    
    # --- START SCHEDULER & ADD JOBS ---
    try:
        scheduler.start()
        
        # --- ADD DAILY BRIEFING JOB ---
        scheduler.add_job(
            run_daily_briefing,
            'cron',
            hour=8, minute=0,
            args=["semantic-test-123", "rathodvamshi369@gmail.com"]
        )
        
        # --- ADD WEEKLY MEMORY CONSOLIDATION JOB ---
        scheduler.add_job(
            run_memory_consolidation,
            'cron',
            day_of_week='sun',
            hour=3, minute=0,
            args=["semantic-test-123"]
        )
        
        logger.info("Task scheduler started successfully.")
        logger.info("Daily briefing scheduled for 8:00 AM every day.")
        logger.info("Weekly memory consolidation scheduled for Sundays at 3:00 AM.")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
    
    # --- START REAL-TIME BACKGROUND TASKS ---
    try:
        await start_background_tasks()
        logger.info("Real-time admin monitoring started.")
    except Exception as e:
        logger.error(f"Error starting real-time tasks: {e}")
    
    yield  # The app is now running
    
    # --- Shutdown ---
    logger.info("--- AURION Backend is shutting down... ---")
    try:
        await log_event("shutdown", {"component": "backend"})
    except Exception:
        logger.error("Failed to log shutdown event")
    await close_redis_pool()  # Disconnect from Redis
    await close_neo4j()       # Disconnect from Neo4j
    await close_mongodb()     # Disconnect from MongoDB
    scheduler.shutdown()       # Stop the scheduler
    logger.info("Task scheduler shut down.")

# Create the main FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# --- CORS Configuration ---
# Allow frontend to communicate with backend
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
# Explicitly add frontend origin for debugging
allowed_origins.append("https://aurion-2w2m89dqc-rathods-projects-2f0dc844.vercel.app")
# Remove duplicates and ensure no empty strings
allowed_origins = list(set([origin for origin in allowed_origins if origin]))

logger.info(f"CORS allowed origins: {allowed_origins}")  # Log allowed origins for debugging

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list methods
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],  # Explicitly list headers
)

# --- API Endpoints ---
main_router = APIRouter()

@main_router.get("/")
async def get_root():
    """
    This is the "Hello World" endpoint.
    If you see this, the server is running.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Backend!",
        "status": "ok"
    }

app.include_router(main_router)
app.include_router(chat_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_mongo_router)
app.include_router(admin_router)
from app.api.sessions import session_router
app.include_router(session_router)
from app.text_selection_api import text_selection_router
app.include_router(text_selection_router, prefix="/api/v1")

# Register test email router for SendGrid delivery testing (after app is defined)
app.include_router(email_service.router, prefix="/api/v1")

# --- Mini Agent Router ---
from fastapi import BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from app.models.schemas import MiniAgentRequest

mini_agent_router = APIRouter()

@mini_agent_router.post("/mini_agent/stream")
async def mini_agent_stream_endpoint(
    request: MiniAgentRequest, 
    background_tasks: BackgroundTasks
):
    """
    The dedicated streaming endpoint for the Inline Mini Agent.
    100% isolated from main chat - uses separate Pinecone namespace.
    """
    return EventSourceResponse(
        handle_mini_agent_request(request, background_tasks)
    )

app.include_router(mini_agent_router, prefix="/api/v1")

# --- DEBUG: Calendar Test Endpoint ---
@app.get("/api/v1/test/calendar")
async def test_calendar_endpoint(user_id: str = "test-user-123"):
    """
    Direct test endpoint to check calendar without going through orchestrator.
    """
    from app.auth_flow import get_calendar_service_for_user
    import datetime
    
    try:
        logger.info(f"Testing calendar for user: {user_id}")
        
        # Get calendar service
        service = await get_calendar_service_for_user(user_id)
        
        if not service:
            return {
                "status": "error",
                "message": "Calendar not connected",
                "auth_url": f"/api/v1/auth/google/login?user_id={user_id}"
            }
        
        # Fetch events
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
        
        import asyncio
        loop = asyncio.get_event_loop()
        events = await loop.run_in_executor(None, fetch_events)
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            formatted_events.append({
                "summary": event.get('summary', 'No title'),
                "start": start
            })
        
        return {
            "status": "success",
            "user_id": user_id,
            "event_count": len(formatted_events),
            "events": formatted_events
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Calendar test error: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

# --- Mount Socket.IO for Admin Real-Time ---
from app.admin.realtime import socket_app
app.mount("/socket.io", socket_app)