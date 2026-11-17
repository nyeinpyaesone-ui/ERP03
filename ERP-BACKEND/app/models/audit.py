"""Audit log model for tamper-evident business operation tracking."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, utcnow


class AuditAction(StrEnum):
    """Categorised audit actions for filtering and alerting."""

    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REGISTER = "auth.register"
    BUSINESS_CREATE = "business.create"
    SALE_CREATE = "sale.create"
    SALE_VOID = "sale.void"
    PRODUCT_CREATE = "product.create"
    PRODUCT_UPDATE = "product.update"
    PRODUCT_DELETE = "product.delete"
    INVENTORY_ADJUST = "inventory.adjust"
    CUSTOMER_CREATE = "customer.create"
    CUSTOMER_UPDATE = "customer.update"
    ROLE_ASSIGN = "role.assign"
    PERMISSION_GRANT = "permission.grant"
    SYSTEM_CONFIG_CHANGE = "system.config_change"


class AuditLog(Base):
    """Immutable record of business operations for compliance and forensics.

    Each entry captures who performed what action, on which resource,
    with before/after snapshots and the request context. Entries are
    append-only: once written, they are never updated or deleted.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_business_created", "business_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    business_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    user_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
