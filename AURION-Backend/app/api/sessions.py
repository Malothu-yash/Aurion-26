# app/api/sessions.py
"""
API endpoints for session management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.session_manager import get_session_manager

session_router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


# ==================== REQUEST/RESPONSE MODELS ====================

class CreateSessionRequest(BaseModel):
    user_id: str
    title: Optional[str] = "New Chat"
    metadata: Optional[Dict[str, Any]] = None


class UpdateSessionRequest(BaseModel):
    user_id: str
    title: str


class SessionActionRequest(BaseModel):
    user_id: str


class SessionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# ==================== ENDPOINTS ====================

@session_router.post("/create")
async def create_session(request: CreateSessionRequest):
    """Create a new chat session"""
    try:
        session_manager = get_session_manager()
        session_id = await session_manager.create_session(
            user_id=request.user_id,
            title=request.title,
            metadata=request.metadata
        )
        
        return SessionResponse(
            success=True,
            message="Session created successfully",
            data={"session_id": session_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/recent/{user_id}")
async def get_recent_sessions(user_id: str, limit: int = 20):
    """Get recent sessions for a user"""
    try:
        session_manager = get_session_manager()
        sessions = await session_manager.get_recent_sessions(
            user_id=user_id,
            limit=limit
        )
        
        return SessionResponse(
            success=True,
            message=f"Retrieved {len(sessions)} sessions",
            data={"sessions": sessions}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/{session_id}")
async def get_session(session_id: str, user_id: str):
    """Get session details"""
    try:
        session_manager = get_session_manager()
        session = await session_manager.get_session(session_id, user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            success=True,
            message="Session retrieved",
            data={"session": session}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.get("/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 100):
    """Get all messages in a session"""
    try:
        session_manager = get_session_manager()
        messages = await session_manager.get_session_messages(
            session_id=session_id,
            limit=limit
        )
        
        return SessionResponse(
            success=True,
            message=f"Retrieved {len(messages)} messages",
            data={"messages": messages}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.put("/{session_id}/rename")
async def rename_session(session_id: str, request: UpdateSessionRequest):
    """Rename a session"""
    try:
        session_manager = get_session_manager()
        success = await session_manager.update_session_title(
            session_id=session_id,
            user_id=request.user_id,
            new_title=request.title
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or update failed")
        
        return SessionResponse(
            success=True,
            message="Session renamed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.post("/{session_id}/pin")
async def toggle_pin_session(session_id: str, request: SessionActionRequest):
    """Pin/unpin a session"""
    try:
        session_manager = get_session_manager()
        is_pinned = await session_manager.toggle_pin_session(
            session_id=session_id,
            user_id=request.user_id
        )
        
        if is_pinned is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        action = "pinned" if is_pinned else "unpinned"
        return SessionResponse(
            success=True,
            message=f"Session {action} successfully",
            data={"is_pinned": is_pinned}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str,
    permanent: bool = False
):
    """Delete a session (soft delete by default)"""
    try:
        session_manager = get_session_manager()
        success = await session_manager.delete_session(
            session_id=session_id,
            user_id=user_id,
            permanent=permanent
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or delete failed")
        
        delete_type = "permanently" if permanent else "temporarily"
        return SessionResponse(
            success=True,
            message=f"Session deleted {delete_type}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@session_router.post("/{session_id}/share")
async def share_session(session_id: str, request: SessionActionRequest):
    """Generate a shareable link for a session"""
    try:
        session_manager = get_session_manager()
        share_url = await session_manager.share_session(
            session_id=session_id,
            user_id=request.user_id
        )
        
        if not share_url:
            raise HTTPException(status_code=404, detail="Session not found or share failed")
        
        return SessionResponse(
            success=True,
            message="Share link generated successfully",
            data={"share_url": share_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
