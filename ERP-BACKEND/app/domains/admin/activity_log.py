from sqlalchemy.orm import Session
from app.domains.admin.system import ActivityLog
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("erp03.audit")


def log_activity(
    db: Session,
