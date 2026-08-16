from sqlalchemy.orm import Session
from app.models import ActivityLog
from typing import Optional, Dict, Any

def log_activity(
    db: Session,
    user_id: Optional[int] = None,
    action: str = "",
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log an activity to the database."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    return log

