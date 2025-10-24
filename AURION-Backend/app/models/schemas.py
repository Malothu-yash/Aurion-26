
# app/models/schemas.py
# This file defines the data structures (the "shape" of our data)
# using Pydantic. This ensures our app gets the data it expects.

from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime

# --- Chat Request ---
# This is the JSON we expect from the React Frontend
class ChatRequest(BaseModel):
    query: str
    conversation_id: str
    hint: Optional[str] = None # The optional hint from the frontend

# --- UPGRADED Intent Classification with 3-Tier AI Throttling ---
# This is based on the "Intent-Based Search Decision" system
# Now with smarter, more specific intent types and cost-efficient AI routing
class Intent(BaseModel):
    intent: Literal[
        "clarify",          # The AI needs more information from the user
        "factual",          # A simple chat or known fact (no search needed)
        "live_search",      # Real-time data (e.g., cricket scores, stocks, weather)
        "local_search",     # Location-based (e.g., restaurants, movies nearby)
        "informational_search", # General web search (e.g., "who won the election")
        "set_reminder",     # Task management
        "play_video",       # YouTube video search
        "get_weather",      # Weather information (legacy - now part of live_search)
        "send_email",       # Send email to any recipient
        "autonomous_plan",  # NEW: Multi-step goals (Tier 3 - Gemini)
        "escalate_medium",  # NEW: Medium complexity (Tier 2 - Groq 70B)
        "escalate_powerful" # NEW: High complexity (Tier 3 - Gemini)
    ]
    parameters: Optional[Dict[str, Any]] = None
    # Example parameters:
    # {"question": "Sure! From where to where?"} # For clarify
    # {"query": "live cricket score"} # For live_search
    # {"query": "best pizza near me", "location": "Mumbai"} # For local_search
    # {"query": "who won the 2024 election"} # For informational_search
    # {"task": "call mom", "time_string": "tomorrow at 5pm"} # For set_reminder
    # {"video_query": "new trailer for dune"} # For play_video
    # {"recipient_email": "user@example.com", "subject": "Hello", "body": "Test email"} # For send_email

# --- Rich Content Responses ---
# This defines the special JSON our frontend can render
class YouTubeVideo(BaseModel):
    type: Literal["youtube"] = "youtube"
    videoId: str
    title: str
    thumbnail_url: str

class Confirmation(BaseModel):
    type: Literal["confirmation"] = "confirmation"
    message: str

class WeatherInfo(BaseModel):
    type: Literal["weather"] = "weather"
    city: str
    temperature: float
    description: str
    feels_like: float
    humidity: int


# --- NEW: Search Response Structure (UX Focused) ---
# This defines how search results are returned to the frontend
class SearchResultLink(BaseModel):
    """Individual search result with title and link"""
    title: str
    link: str
    snippet: Optional[str] = None  # Optional snippet/description

class SearchResponse(BaseModel):
    """Structured search response with AI summary and source links"""
    type: Literal["searchResults"] = "searchResults"
    summary: str  # AI-generated summary of the search results
    links: list[SearchResultLink]  # List of source links
    timestamp: str  # When the search was performed
    query: Optional[str] = None  # The original search query





# --- User Schema for Authentication ---
class User(BaseModel):
    """User model for authentication and authorization"""
    email: str
    display_name: Optional[str] = None
    role: Optional[str] = None
    hobbies: Optional[list[str]] = None

# --- Mini Agent Chat ---
class MiniAgentChatRequest(BaseModel):
    messageId: str
    selectedText: Optional[str] = None
    userMessage: str
    sessionId: str

class MiniAgentChatResponse(BaseModel):
    reply: str
    model_used: Optional[str] = None
    tier_used: Optional[str] = None

class MiniAgentMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str

class MiniAgentConversation(BaseModel):
    messageId: str
    sessionId: str
    selectedText: Optional[str] = None
    conversations: List[MiniAgentMessage]
    createdAt: datetime
    updatedAt: Optional[datetime] = None

# --- Highlights ---
class HighlightRange(BaseModel):
    start: int
    end: int
    text: Optional[str] = None

class HighlightAddRequest(BaseModel):
    sessionId: str
    start: int
    end: int
    text: Optional[str] = None

class HighlightsDoc(BaseModel):
    messageId: str
    sessionId: str
    ranges: List[HighlightRange]
    createdAt: datetime
    updatedAt: Optional[datetime] = None