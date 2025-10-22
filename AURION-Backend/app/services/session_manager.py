# app/services/session_manager.py
"""
Session History Management System
- Each session is a fresh conversation
- Save/load session history from MongoDB
- Pin, delete, rename, share sessions
- Fetch recent sessions for user
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4

from app.auth_db import db

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages chat sessions with full CRUD operations"""
    
    def __init__(self):
        # MongoDB collections will be initialized lazily
        self._sessions_collection = None
        self._messages_collection = None
        logger.info("✅ SessionManager initialized")
    
    @property
    def sessions_collection(self):
        """Lazy initialization of sessions collection"""
        if self._sessions_collection is None and db is not None:
            self._sessions_collection = db["chat_sessions"]
        return self._sessions_collection
    
    @property
    def messages_collection(self):
        """Lazy initialization of messages collection"""
        if self._messages_collection is None and db is not None:
            self._messages_collection = db["chat_messages"]
        return self._messages_collection
    
    def _ensure_db(self):
        """Ensure database is initialized"""
        if db is None:
            logger.warning("⚠️ Database not yet initialized, session operations will be skipped")
            return False
        if self.sessions_collection is None:
            self._sessions_collection = db["chat_sessions"]
        if self.messages_collection is None:
            self._messages_collection = db["chat_messages"]
        return True
    
    async def create_session(
        self,
        user_id: str,
        title: str = "New Chat",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new chat session
        
        Args:
            user_id: User identifier (email)
            title: Session title (default: "New Chat")
            metadata: Optional metadata (tags, notes, etc.)
            
        Returns:
            session_id: Unique session identifier
        """
        if not self._ensure_db():
            return str(uuid4())  # Return temp ID if db not ready
        
        session_id = str(uuid4())
        
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_pinned": False,
            "is_deleted": False,
            "message_count": 0,
            "metadata": metadata or {}
        }
        
        try:
            await self.sessions_collection.insert_one(session_doc)
            logger.info(f"✅ Created new session: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get session details
        
        Args:
            session_id: Session identifier
            user_id: User identifier (for security)
            
        Returns:
            Session document or None
        """
        if not self._ensure_db():
            return None
        
        try:
            session = await self.sessions_collection.find_one({
                "session_id": session_id,
                "user_id": user_id,
                "is_deleted": False
            })
            return session
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def get_recent_sessions(
        self,
        user_id: str,
        limit: int = 20,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recent sessions for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            include_deleted: Include deleted sessions
            
        Returns:
            List of session documents
        """
        if not self._ensure_db():
            return []
        
        try:
            query = {"user_id": user_id}
            if not include_deleted:
                query["is_deleted"] = False
            
            # Sort: Pinned first, then by updated_at descending
            cursor = self.sessions_collection.find(query).sort([
                ("is_pinned", -1),
                ("updated_at", -1)
            ]).limit(limit)
            
            sessions = await cursor.to_list(length=limit)
            
            # Convert datetime to ISO string for JSON serialization
            for session in sessions:
                if "_id" in session:
                    session["_id"] = str(session["_id"])
                if "created_at" in session:
                    session["created_at"] = session["created_at"].isoformat()
                if "updated_at" in session:
                    session["updated_at"] = session["updated_at"].isoformat()
            
            logger.info(f"✅ Retrieved {len(sessions)} sessions for user {user_id}")
            return sessions
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            return []
    
    async def update_session_title(
        self,
        session_id: str,
        user_id: str,
        new_title: str
    ) -> bool:
        """
        Rename a session
        
        Args:
            session_id: Session identifier
            user_id: User identifier (for security)
            new_title: New session title
            
        Returns:
            True if successful
        """
        if not self._ensure_db():
            return False
        
        try:
            result = await self.sessions_collection.update_one(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "is_deleted": False
                },
                {
                    "$set": {
                        "title": new_title,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Renamed session {session_id} to '{new_title}'")
            return success
        except Exception as e:
            logger.error(f"Error renaming session: {e}")
            return False
    
    async def toggle_pin_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Pin/unpin a session
        
        Args:
            session_id: Session identifier
            user_id: User identifier (for security)
            
        Returns:
            True if pinned, False if unpinned, None if error
        """
        if not self._ensure_db():
            return None
        
        try:
            # Get current pin status
            session = await self.get_session(session_id, user_id)
            if not session:
                return None
            
            new_pin_status = not session.get("is_pinned", False)
            
            result = await self.sessions_collection.update_one(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "is_deleted": False
                },
                {
                    "$set": {
                        "is_pinned": new_pin_status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                action = "pinned" if new_pin_status else "unpinned"
                logger.info(f"✅ Session {session_id} {action}")
                return new_pin_status
            return None
        except Exception as e:
            logger.error(f"Error toggling pin: {e}")
            return None
    
    async def delete_session(
        self,
        session_id: str,
        user_id: str,
        permanent: bool = False
    ) -> bool:
        """
        Delete a session (soft delete by default)
        
        Args:
            session_id: Session identifier
            user_id: User identifier (for security)
            permanent: If True, permanently delete. If False, soft delete.
            
        Returns:
            True if successful
        """
        if not self._ensure_db():
            return False
        
        try:
            if permanent:
                # Permanent deletion - remove from database
                result = await self.sessions_collection.delete_one({
                    "session_id": session_id,
                    "user_id": user_id
                })
                
                # Also delete all messages
                await self.messages_collection.delete_many({
                    "session_id": session_id
                })
                
                success = result.deleted_count > 0
                if success:
                    logger.info(f"✅ Permanently deleted session {session_id}")
            else:
                # Soft deletion - mark as deleted
                result = await self.sessions_collection.update_one(
                    {
                        "session_id": session_id,
                        "user_id": user_id
                    },
                    {
                        "$set": {
                            "is_deleted": True,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                success = result.modified_count > 0
                if success:
                    logger.info(f"✅ Soft deleted session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def share_session(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Generate a shareable link for a session
        
        Args:
            session_id: Session identifier
            user_id: User identifier (for security)
            
        Returns:
            Shareable link or None
        """
        if not self._ensure_db():
            return None
        
        try:
            session = await self.get_session(session_id, user_id)
            if not session:
                return None
            
            # Generate share token
            share_token = str(uuid4())
            
            # Update session with share token
            await self.sessions_collection.update_one(
                {
                    "session_id": session_id,
                    "user_id": user_id
                },
                {
                    "$set": {
                        "share_token": share_token,
                        "shared_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Generate shareable URL
            from app.core.config import settings
            share_url = f"{settings.BASE_URL}/shared/{share_token}"
            
            logger.info(f"✅ Generated share link for session {session_id}")
            return share_url
        except Exception as e:
            logger.error(f"Error sharing session: {e}")
            return None
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to a session
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (intent, confidence, etc.)
            
        Returns:
            True if successful
        """
        if not self._ensure_db():
            return False  # Silently skip if db not ready
        
        try:
            message_doc = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc),
                "metadata": metadata or {}
            }
            
            await self.messages_collection.insert_one(message_doc)
            
            # Update session's message count and updated_at
            await self.sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            
            logger.debug(f"✅ Added {role} message to session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message documents
        """
        if not self._ensure_db():
            return []
        
        try:
            cursor = self.messages_collection.find({
                "session_id": session_id
            }).sort("timestamp", 1).limit(limit)
            
            messages = await cursor.to_list(length=limit)
            
            # Convert datetime to ISO string
            for message in messages:
                if "_id" in message:
                    message["_id"] = str(message["_id"])
                if "timestamp" in message:
                    message["timestamp"] = message["timestamp"].isoformat()
            
            return messages
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    async def auto_generate_title(
        self,
        session_id: str,
        user_id: str,
        first_message: str
    ) -> bool:
        """
        Auto-generate a session title based on the first message
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            first_message: First user message
            
        Returns:
            True if successful
        """
        if not self._ensure_db():
            return False
        
        try:
            # Simple title generation: take first 50 chars or first sentence
            title = first_message.strip()
            
            # If message is long, take first sentence
            if len(title) > 50:
                # Try to find first sentence
                for delimiter in ['.', '!', '?']:
                    idx = title.find(delimiter)
                    if idx > 0 and idx < 50:
                        title = title[:idx]
                        break
                else:
                    # No sentence delimiter found, just truncate
                    title = title[:47] + "..."
            
            # Update session title
            return await self.update_session_title(session_id, user_id, title)
        except Exception as e:
            logger.error(f"Error auto-generating title: {e}")
            return False


# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get or create SessionManager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
