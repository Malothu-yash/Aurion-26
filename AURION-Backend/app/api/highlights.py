from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional
from app.models.schemas import (
    HighlightAddRequest,
    HighlightsDoc,
)
import app.auth_db as auth_db

router = APIRouter()


@router.post("/api/highlights/{messageId}", response_model=HighlightsDoc)
async def add_highlight(messageId: str, req: HighlightAddRequest):
    if not messageId:
        raise HTTPException(status_code=400, detail="messageId is required")
    if req.start is None or req.end is None or req.start < 0 or req.end <= req.start:
        raise HTTPException(status_code=400, detail="Invalid highlight range")
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    now = datetime.utcnow()
    try:
        existing = await db.message_highlights.find_one({"messageId": messageId})
        if not existing:
            doc = {
                "messageId": messageId,
                "sessionId": req.sessionId,
                "ranges": [{"start": req.start, "end": req.end, "text": req.text}],
                "createdAt": now,
                "updatedAt": now,
            }
            await db.message_highlights.insert_one(doc)
            doc.pop("_id", None)
            return HighlightsDoc.model_validate(doc)
        else:
            await db.message_highlights.update_one(
                {"messageId": messageId},
                {
                    "$set": {"sessionId": req.sessionId, "updatedAt": now},
                    "$push": {"ranges": {"start": req.start, "end": req.end, "text": req.text}},
                },
            )
            updated = await db.message_highlights.find_one({"messageId": messageId}, {"_id": 0})
            return HighlightsDoc.model_validate(updated)
    except Exception:
        raise HTTPException(status_code=503, detail="Database error")


@router.get("/api/highlights/{messageId}", response_model=HighlightsDoc)
async def get_highlights(messageId: str):
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        doc = await db.message_highlights.find_one({"messageId": messageId})
    except Exception:
        raise HTTPException(status_code=503, detail="Database error")
    if not doc:
        raise HTTPException(status_code=404, detail="Highlights not found")
    doc.pop("_id", None)
    return HighlightsDoc.model_validate(doc)


@router.delete("/api/highlights/{messageId}")
async def delete_highlights(messageId: str):
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = await db.message_highlights.delete_one({"messageId": messageId})
    except Exception:
        raise HTTPException(status_code=503, detail="Database error")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Highlights not found")
    return {"success": True}


@router.get("/api/highlights/exists/{messageId}")
async def highlights_exists(messageId: str):
    """Return 200 with {exists: bool} to avoid 404 when probing for highlights."""
    db = getattr(auth_db, 'db', None)
    if db is None:
        return {"exists": False}
    try:
        doc = await db.message_highlights.find_one({"messageId": messageId}, {"_id": 1})
        return {"exists": bool(doc)}
    except Exception:
        return {"exists": False}
