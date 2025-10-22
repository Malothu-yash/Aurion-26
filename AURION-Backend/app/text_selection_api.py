# app/text_selection_api.py
# Backend API endpoints for text selection features (highlights and mini agent sessions)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from app.auth_db import get_current_user
from app.models.schemas import User

# Create router for text selection features
text_selection_router = APIRouter()

# Pydantic models for API requests/responses
class HighlightRequest(BaseModel):
    messageId: str
    text: str
    color: str
    note: Optional[str] = None
    rangeStart: int
    rangeEnd: int

class HighlightResponse(BaseModel):
    id: str
    messageId: str
    userId: str
    text: str
    color: str
    note: Optional[str] = None
    rangeStart: int
    rangeEnd: int
    createdAt: str

class MiniAgentMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str

class MiniAgentSessionRequest(BaseModel):
    messageId: str
    snippet: str
    conversation: List[MiniAgentMessage]

class MiniAgentSessionResponse(BaseModel):
    id: str
    messageId: str
    userId: str
    snippet: str
    conversation: List[MiniAgentMessage]
    createdAt: str
    updatedAt: str

# In-memory storage (replace with MongoDB in production)
highlights_storage = {}
mini_agent_sessions_storage = {}

@text_selection_router.post("/highlights", response_model=HighlightResponse)
async def save_highlight(
    request: HighlightRequest,
    current_user: User = Depends(get_current_user)
):
    """Save a highlight for a specific message"""
    try:
        highlight_id = str(uuid.uuid4())
        highlight = {
            "id": highlight_id,
            "messageId": request.messageId,
            "userId": current_user.email,
            "text": request.text,
            "color": request.color,
            "note": request.note,
            "rangeStart": request.rangeStart,
            "rangeEnd": request.rangeEnd,
            "createdAt": datetime.utcnow().isoformat()
        }
        
        # Store in memory (replace with MongoDB)
        highlights_storage[highlight_id] = highlight
        
        return HighlightResponse(**highlight)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save highlight: {str(e)}")

@text_selection_router.get("/highlights", response_model=List[HighlightResponse])
async def get_highlights(
    messageId: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get highlights for a user or specific message"""
    try:
        user_highlights = [
            highlight for highlight in highlights_storage.values()
            if highlight["userId"] == current_user.email
        ]
        
        if messageId:
            user_highlights = [
                highlight for highlight in user_highlights
                if highlight["messageId"] == messageId
            ]
        
        return [HighlightResponse(**highlight) for highlight in user_highlights]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get highlights: {str(e)}")

@text_selection_router.delete("/highlights/{highlight_id}")
async def delete_highlight(
    highlight_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific highlight"""
    try:
        if highlight_id not in highlights_storage:
            raise HTTPException(status_code=404, detail="Highlight not found")
        
        highlight = highlights_storage[highlight_id]
        if highlight["userId"] != current_user.email:
            raise HTTPException(status_code=403, detail="Not authorized to delete this highlight")
        
        del highlights_storage[highlight_id]
        return {"message": "Highlight deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete highlight: {str(e)}")

@text_selection_router.post("/mini-agent-sessions", response_model=MiniAgentSessionResponse)
async def save_mini_agent_session(
    request: MiniAgentSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Save or update a mini agent session"""
    try:
        # Check if session already exists for this message
        existing_session = None
        for session in mini_agent_sessions_storage.values():
            if (session["messageId"] == request.messageId and 
                session["userId"] == current_user.email):
                existing_session = session
                break
        
        if existing_session:
            # Update existing session
            session_id = existing_session["id"]
            session = {
                "id": session_id,
                "messageId": request.messageId,
                "userId": current_user.email,
                "snippet": request.snippet,
                "conversation": [msg.dict() for msg in request.conversation],
                "createdAt": existing_session["createdAt"],
                "updatedAt": datetime.utcnow().isoformat()
            }
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            session = {
                "id": session_id,
                "messageId": request.messageId,
                "userId": current_user.email,
                "snippet": request.snippet,
                "conversation": [msg.dict() for msg in request.conversation],
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        
        mini_agent_sessions_storage[session_id] = session
        return MiniAgentSessionResponse(**session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save mini agent session: {str(e)}")

@text_selection_router.get("/mini-agent-sessions", response_model=List[MiniAgentSessionResponse])
async def get_mini_agent_sessions(
    messageId: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get mini agent sessions for a user or specific message"""
    try:
        user_sessions = [
            session for session in mini_agent_sessions_storage.values()
            if session["userId"] == current_user.email
        ]
        
        if messageId:
            user_sessions = [
                session for session in user_sessions
                if session["messageId"] == messageId
            ]
        
        return [MiniAgentSessionResponse(**session) for session in user_sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mini agent sessions: {str(e)}")

@text_selection_router.delete("/mini-agent-sessions/{session_id}")
async def delete_mini_agent_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific mini agent session"""
    try:
        if session_id not in mini_agent_sessions_storage:
            raise HTTPException(status_code=404, detail="Mini agent session not found")
        
        session = mini_agent_sessions_storage[session_id]
        if session["userId"] != current_user.email:
            raise HTTPException(status_code=403, detail="Not authorized to delete this session")
        
        del mini_agent_sessions_storage[session_id]
        return {"message": "Mini agent session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete mini agent session: {str(e)}")
