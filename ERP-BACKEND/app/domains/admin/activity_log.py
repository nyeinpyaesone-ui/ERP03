from sqlalchemy.orm import Session
from app.models.system import ActivityLog
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
    """
    Record an audit event and persist it to the database.

    Parameters:
        user_id (Optional[int]): Identifier of the user associated with the event.
        action (str): Action recorded by the event.
        entity_type (Optional[str]): Type of entity affected by the event.
        entity_id (Optional[int]): Identifier of the affected entity.
        details (Optional[Dict[str, Any]]): Additional event-specific information.
        ip_address (Optional[str]): Client IP address associated with the event.
        user_agent (Optional[str]): Client user-agent string.
        correlation_id (Optional[str]): Identifier used to correlate related operations.
        request_id (Optional[str]): Identifier of the request that produced the event.
        status (str): Outcome status recorded for the event.
        commit (bool): Whether to commit the transaction; when false, flushes the record instead.

    Returns:
        ActivityLog: The created audit log record.
    """
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
    """
    Create an audit log entry containing entity states and field-level changes.

    Parameters:
        before_state (Optional[Dict[str, Any]]): State before the operation.
        after_state (Optional[Dict[str, Any]]): State after the operation.
        kwargs: Additional activity log arguments; any ``details`` values are
            merged into the generated audit details.

    Returns:
        ActivityLog: The created audit log record.
    """
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
