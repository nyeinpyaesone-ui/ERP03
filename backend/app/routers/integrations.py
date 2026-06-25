from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import hmac
import hashlib
import json

from app.database import get_db
from app.models import Integration, Webhook, WebhookDelivery
from app.auth import get_current_user
from app.config import settings
from app.services.activity_log import log_activity

router = APIRouter()

class IntegrationCreate(BaseModel):
    name: str
    provider: str
    config: Dict[str, Any]

class WebhookCreate(BaseModel):
    name: str
    url: str
    events: list[str]
    secret: Optional[str] = None

@router.post("/integrations")
def create_integration(data: IntegrationCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    integration = Integration(**data.dict(), created_by=current_user.id)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration

@router.get("/integrations")
def list_integrations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Integration).all()

@router.post("/webhooks")
def create_webhook(data: WebhookCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    webhook = Webhook(**data.dict(), created_by=current_user.id)
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook

@router.get("/webhooks")
def list_webhooks(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Webhook).all()

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    payload = {"event": "test", "timestamp": str(datetime.now()), "data": {"message": "Test webhook delivery"}}

    headers = {"Content-Type": "application/json"}
    if webhook.secret:
        signature = hmac.new(webhook.secret.encode(), json.dumps(payload).encode(), hashlib.sha256).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event="test",
        payload=payload,
        attempt=1
    )
    db.add(delivery)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook.url, json=payload, headers=headers)
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]
            delivery.status = "delivered" if response.status_code < 400 else "failed"
    except Exception as e:
        delivery.status = "failed"
        delivery.response_body = str(e)[:1000]

    db.commit()
    db.refresh(delivery)
    return delivery

@router.get("/webhooks/{webhook_id}/deliveries")
def get_deliveries(webhook_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == webhook_id).order_by(WebhookDelivery.created_at.desc()).all()

from datetime import datetime

