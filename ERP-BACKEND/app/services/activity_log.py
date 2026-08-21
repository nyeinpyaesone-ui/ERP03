from sqlalchemy.orm import Session
from app.models import ActivityLog
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("erp03.audit")


def log_activity(
    db: Session,
    user_id: Optional[int] = None,
    action: str = "",
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    status: str = "SUCCESS",
    commit: bool = True,
):
    """Record an audit event, optionally joining the caller's transaction."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id,
        request_id=request_id,
        status=status,
    )
    db.add(log)
    if commit:
        db.commit()
    else:
        db.flush()
    logger.info("Audit log: %s by user %s on %s:%s", action, user_id, entity_type, entity_id)
    return log


def log_before_after(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: int,
    before_state: Optional[Dict[str, Any]],
    after_state: Optional[Dict[str, Any]],
    **kwargs
):
    """Create an audit log entry containing entity state and detected changes."""
    changes = {}
    if before_state and after_state:
        all_keys = set(before_state.keys()) | set(after_state.keys())
        for key in all_keys:
            old_val = before_state.get(key)
            new_val = after_state.get(key)
            if old_val != new_val:
                changes[key] = {"old": old_val, "new": new_val}

    details = {
        "changes": changes,
        "before": before_state,
        "after": after_state,
        **(kwargs.get("details", {}) or {}),
    }

    return log_activity(
        db=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        **kwargs
    )
