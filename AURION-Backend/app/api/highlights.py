from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from typing import Optional
from app.models.schemas import (
    HighlightAddRequest,
    HighlightsDoc,
)
import app.auth_db as auth_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/highlights/{messageId}", response_model=HighlightsDoc)
async def add_highlight(messageId: str, req: HighlightAddRequest, request: Request):
    # Debugging: log incoming payload to help diagnose 400 errors
    try:
        body = await request.json()
    except Exception:
        body = None
    logger.info("/api/highlights called. messageId=%s, body=%s", messageId, body)

    if not messageId:
        logger.warning("add_highlight: missing messageId")
        raise HTTPException(status_code=400, detail="messageId is required")
    if req.start is None or req.end is None or req.start < 0 or req.end <= req.start:
        logger.warning("add_highlight: invalid range start=%s end=%s", getattr(req, 'start', None), getattr(req, 'end', None))
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
                "ranges": [{"start": req.start, "end": req.end, "text": req.text, "color": getattr(req, 'color', None)}],
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
                    "$push": {"ranges": {"start": req.start, "end": req.end, "text": req.text, "color": getattr(req, 'color', None)}},
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


@router.delete("/api/highlights/{messageId}/range", response_model=HighlightsDoc)
async def delete_highlight_range(messageId: str, request: Request):
    """Remove a single highlight range matching start/end (and optional text/color) from a message's ranges array.

    Expects JSON body with start and end (and optional sessionId/text/color). Returns the updated HighlightsDoc.
    """
    # Log incoming for debugging
    try:
        body = await request.json()
    except Exception:
        body = None
    logger.info("/api/highlights/{messageId}/range DELETE called. messageId=%s, body=%s", messageId, body)

    if not messageId:
        raise HTTPException(status_code=400, detail="messageId is required")
    # Parse JSON body and validate fields
    try:
        payload = await request.json()
    except Exception:
        payload = None
    if not payload:
        raise HTTPException(status_code=400, detail="Missing JSON body")
    start = payload.get('start')
    end = payload.get('end')
    text = payload.get('text')
    color = payload.get('color')
    if start is None or end is None or not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
        raise HTTPException(status_code=400, detail="Invalid highlight range")
    db = getattr(auth_db, 'db', None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        # First, try to apply a "split/shrink" behavior on any overlapping ranges.
        # This allows unhighlighting a subrange inside an existing highlight by
        # splitting it into kept pieces.
        doc = await db.message_highlights.find_one({"messageId": messageId})
        if not doc:
            raise HTTPException(status_code=404, detail="Highlights not found")
        orig_ranges = doc.get('ranges', []) or []
        new_ranges = []
        removed_any = False

        for r in orig_ranges:
            rs = int(r.get('start', 0))
            re = int(r.get('end', 0))
            # No overlap
            if re <= start or rs >= end:
                new_ranges.append(r)
                continue

            # Overlap exists -> we'll remove the overlapping segment and keep the rest
            removed_any = True
            # Case: selection is strictly inside existing range -> split into two
            if rs < start and re > end:
                left = r.copy()
                left['start'] = rs
                left['end'] = start
                right = r.copy()
                right['start'] = end
                right['end'] = re
                new_ranges.append(left)
                new_ranges.append(right)
                continue

            # Case: overlap on the right side of existing range: keep left portion
            if rs < start < re <= end:
                left = r.copy()
                left['start'] = rs
                left['end'] = start
                new_ranges.append(left)
                continue

            # Case: overlap on the left side of existing range: keep right portion
            if start <= rs < end < re:
                right = r.copy()
                right['start'] = end
                right['end'] = re
                new_ranges.append(right)
                continue

            # Case: existing range fully inside selection -> remove it (do not add)
            # (nothing to do)

        if removed_any:
            # persist the modified ranges array
            await db.message_highlights.update_one(
                {"messageId": messageId},
                {"$set": {"ranges": new_ranges, "updatedAt": datetime.utcnow()}}
            )
            updated = await db.message_highlights.find_one({"messageId": messageId}, {"_id": 0})
            return HighlightsDoc.model_validate(updated)

        # If we didn't remove anything by splitting (no overlapping stored ranges matched),
        # fall back to a conservative $pull by exact match or by start/end only.
        pull_match = {"start": start, "end": end}
        if text is not None:
            pull_match['text'] = text
        if color is not None:
            pull_match['color'] = color

        res = await db.message_highlights.update_one(
            {"messageId": messageId},
            {"$pull": {"ranges": pull_match}, "$set": {"updatedAt": datetime.utcnow()}}
        )
        if res.modified_count == 0:
            # fallback by start/end only
            await db.message_highlights.update_one(
                {"messageId": messageId},
                {"$pull": {"ranges": {"start": start, "end": end}}, "$set": {"updatedAt": datetime.utcnow()}}
            )
        updated = await db.message_highlights.find_one({"messageId": messageId}, {"_id": 0})
        if not updated:
            raise HTTPException(status_code=404, detail="Highlights not found")
        return HighlightsDoc.model_validate(updated)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Database error")


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
