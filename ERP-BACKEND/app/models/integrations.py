"""
Integration and Webhook models
Handles external integrations and webhook deliveries
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class Webhook(Base, TimestampMixin):
    """Webhook configuration for external notifications"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSONB, nullable=False)  # ["invoice.created", "deal.won"]
    secret = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    retry_count = Column(Integer, nullable=False, server_default="3")
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", foreign_keys=[created_by])
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}')>"


class WebhookDelivery(Base):
    """Webhook delivery attempt tracking"""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    event = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt = Column(Integer, nullable=False, server_default="1")
    status = Column(String(50), nullable=False, server_default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    webhook = relationship("Webhook", back_populates="deliveries")

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, status='{self.status}')>"


class Integration(Base, TimestampMixin):
    """External integration configuration"""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)  # slack, teams, zapier, generic
    config = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Integration(id={self.id}, name='{self.name}', provider='{self.provider}')>"
