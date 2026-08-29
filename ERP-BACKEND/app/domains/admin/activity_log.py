from typing import Any, Dict, Optional

import logging

from sqlalchemy.orm import Session

from app.domains.admin.system import ActivityLog

logger = logging.getLogger("erp03.audit")


def log_activity(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    status: str = "SUCCESS",
) -> ActivityLog:
    """Persist an auditable business/system activity record."""
    entry = ActivityLog(
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

    try:
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:
        db.rollback()
        logger.exception("Failed to persist activity log: action=%s user_id=%s", action, user_id)
        raise
