from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.models import User, Setting, ActivityLog, Notification
from app.auth import get_current_user, require_admin

router = APIRouter()

class SettingCreate(BaseModel):
    key: str
    value: str
    category: str = "general"
    is_encrypted: bool = False
    description: Optional[str] = None

@router.get("/settings")
def get_settings(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    query = db.query(Setting)
    if category:
        query = query.filter(Setting.category == category)
    return query.all()

@router.post("/settings")
def create_setting(data: SettingCreate, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    existing = db.query(Setting).filter(Setting.key == data.key).first()
    if existing:
        existing.value = data.value
        existing.category = data.category
        existing.is_encrypted = data.is_encrypted
        db.commit()
        db.refresh(existing)
        return existing

    setting = Setting(**data.dict())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

@router.delete("/settings/{key}")
def delete_setting(key: str, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(setting)
    db.commit()
    return {"message": "Setting deleted"}

@router.get("/activity-logs")
def get_activity_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    query = db.query(ActivityLog)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
    return query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/notifications")
def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).all()

@router.put("/notifications/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return notif

@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    from sqlalchemy import func
    return {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active == True).count(),
        "total_activity": db.query(ActivityLog).count(),
        "today_activity": db.query(ActivityLog).filter(
            func.date(ActivityLog.created_at) == func.date(func.now())
        ).count()
    }

