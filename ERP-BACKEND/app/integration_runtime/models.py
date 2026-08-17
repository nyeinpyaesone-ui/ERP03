from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class PurchaseOrder(Base):
    __tablename__ = "integration_purchase_orders"

    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency_code = Column(String(3), nullable=False)
    status = Column(String(32), nullable=False, default="PENDING_APPROVAL", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PurchaseOrderApproval(Base):
    __tablename__ = "integration_po_approvals"

    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey("integration_purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approval_level = Column(Integer, nullable=False)
    decision = Column(String(16), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IntegrationCommand(Base):
    __tablename__ = "integration_commands"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_integration_command_idempotency"),)

    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String(128), nullable=False)
    command_id = Column(String(36), nullable=False, index=True)
    command_type = Column(String(64), nullable=False)
    requested_by = Column(String(255), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=False)
    response = Column(JSONB, nullable=False)
    correlation_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
