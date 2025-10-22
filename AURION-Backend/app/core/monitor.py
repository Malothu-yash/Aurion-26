"""
app/core/monitor.py

Lightweight system monitor hooks. When enabled by strategy.system_monitor.log_to,
logs key events to MongoDB.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional, Dict, Any

from app.core.strategy import get_strategy

try:
    # Lazy import Mongo DB handle from auth system
    from app.auth_db import db  # type: ignore
except Exception:  # pragma: no cover
    db = None


async def log_event(event: str, details: Optional[Dict[str, Any]] = None):
    """Insert a log document into MongoDB if configured, else no-op."""
    try:
        strat = get_strategy()
        if strat.system_monitor.log_to != "mongodb_logs":
            return
        if not db:
            return
        doc = {
            "event": event,
            "details": details or {},
            "ts": _dt.datetime.utcnow(),
        }
        await db.logs.insert_one(doc)
    except Exception:
        # Silent fail - monitoring must never break the app
        pass
