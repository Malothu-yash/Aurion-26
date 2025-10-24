from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.models.schemas import (
    MiniAgentChatRequest,
    MiniAgentChatResponse,
    MiniAgentConversation,
    MiniAgentMessage,
)
from app.services.ai_clients import generate_response
import app.auth_db as auth_db

router = APIRouter()

SYSTEM_PROMPT = (
    "You are AURION's Mini Agent. Be concise, helpful, and use the provided selected snippet as context when relevant. "
    "If the selected text is empty or irrelevant, just answer the user's question clearly."
)

@router.post("/api/mini-agent/chat", response_model=MiniAgentChatResponse)
async def mini_agent_chat(req: MiniAgentChatRequest):
    # Build a prompt that includes the selected text for better grounding
    if req.selectedText:
        prompt = (
            f"Selected snippet:\n{req.selectedText}\n\n"
            f"User message: {req.userMessage}"
        )
    else:
        prompt = req.userMessage

    # Persist conversation in MongoDB (two-phase: save user, then assistant)
    try:
        db = getattr(auth_db, 'db', None)
        if db is None:
            raise RuntimeError("Database not initialized")
        # Ensure doc exists
        existing = await db.mini_agent_conversations.find_one({"messageId": req.messageId})
        now = datetime.utcnow()
        if not existing:
            base_doc = MiniAgentConversation(
                messageId=req.messageId,
                sessionId=req.sessionId,
                selectedText=req.selectedText,
                conversations=[],
                createdAt=now,
                updatedAt=now
            ).model_dump()
            await db.mini_agent_conversations.insert_one(base_doc)
        # Push user message and update timestamps/fields
        await db.mini_agent_conversations.update_one(
            {"messageId": req.messageId},
            {
                "$set": {"sessionId": req.sessionId, "selectedText": req.selectedText, "updatedAt": now},
                "$push": {"conversations": {"role": "user", "content": req.userMessage}}
            }
        )
    except Exception as e:
        # Don't fail the chat if DB write fails
        print(f"MiniAgent DB write error: {e}")

    reply_text = await generate_response(query=prompt, system_prompt=SYSTEM_PROMPT)

    # Save assistant reply
    try:
        db = getattr(auth_db, 'db', None)
        if db is not None:
            await db.mini_agent_conversations.update_one(
                {"messageId": req.messageId},
                {
                    "$set": {"updatedAt": datetime.utcnow()},
                    "$push": {"conversations": {"role": "assistant", "content": reply_text}}
                }
            )
    except Exception as e:
        print(f"MiniAgent DB write (assistant) error: {e}")

    return MiniAgentChatResponse(reply=reply_text)


@router.get("/api/mini-agent/{messageId}", response_model=MiniAgentConversation)
async def get_mini_agent_conversation(messageId: str):
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        doc = await db.mini_agent_conversations.find_one({"messageId": messageId})
    except Exception as e:
        # Surface a controlled error to avoid raw 500s without CORS
        raise HTTPException(status_code=503, detail="Database error")
    if not doc:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Convert Mongo _id to str or remove
    doc.pop("_id", None)
    return MiniAgentConversation.model_validate(doc)


@router.delete("/api/mini-agent/{messageId}")
async def delete_mini_agent_conversation(messageId: str):
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = await db.mini_agent_conversations.delete_one({"messageId": messageId})
    except Exception:
        raise HTTPException(status_code=503, detail="Database error")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@router.get("/api/mini-agent/session/{sessionId}")
async def get_session_mini_agent_overview(sessionId: str):
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    cursor = db.mini_agent_conversations.find(
        {"sessionId": sessionId},
        {"_id": 0, "messageId": 1, "updatedAt": 1}
    )
    items = await cursor.to_list(length=1000)
    return {
        "messageIds": [it["messageId"] for it in items],
        "count": len(items)
    }


@router.get("/api/mini-agent/exists/{messageId}")
async def mini_agent_exists(messageId: str):
    """Return 200 with {exists: bool} instead of 404 to avoid console noise in UIs."""
    db = getattr(auth_db, 'db', None)
    if db is None:
        # Return non-throwing answer; client treats this as 'false' but service unavailable
        return {"exists": False}
    try:
        doc = await db.mini_agent_conversations.find_one({"messageId": messageId}, {"_id": 1})
        return {"exists": bool(doc)}
    except Exception:
        return {"exists": False}
