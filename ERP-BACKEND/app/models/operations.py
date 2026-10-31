"""Durable cross-module transaction orchestration state machine.

Tracks operations that cross the journal (SQLite) and domain (PostgreSQL)
transaction boundaries so they can be safely resumed after process
termination, retried with bounded backoff, and reconciled under multiple
replicas without duplicate side effects.

Legal lifecycle transitions:

    PENDING -> PROCESSING -> COMMITTED  (happy path)
    PENDING -> PROCESSING -> FAILED     (domain error, retryable)
    FAILED  -> PROCESSING               (retry after backoff)
    PROCESSING -> RECONCILIATION_REQUIRED  (max retries exceeded)
    RECONCILIATION_REQUIRED -> CANCELLED   (terminal, manual review)
    any -> CANCELLED                    (manual abort)

An operation is *committed* only when its domain transaction commits. The
operation row itself is updated in the same PostgreSQL transaction as the
domain mutations, so either both succeed or neither does.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, utcnow


class OperationState(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMMITTED = "committed"
    FAILED = "failed"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    CANCELLED = "cancelled"


# States from which a worker may legally claim the operation for processing.
_CLAIMABLE_STATES = (
    OperationState.PENDING,
    OperationState.FAILED,
)

# Terminal states: no further transitions are permitted.
_TERMINAL_STATES = (
    OperationState.COMMITTED,
    OperationState.CANCELLED,
)


class Operation(Base):
    """Durable record of a cross-module business operation."""

    __tablename__ = "operations"
    __table_args__ = (
        UniqueConstraint("operation_id", name="uq_operations_operation_id"),
        Index("ix_operations_state_updated", "state", "updated_at"),
        Index("ix_operations_business_state", "business_id", "state"),
    )

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    operation_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    operation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[OperationState] = mapped_column(
        SAEnum(OperationState, name="operation_state", native_enum=False),
        default=OperationState.PENDING,
        nullable=False,
    )
    business_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    result_json: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=5, nullable=False)
    backoff_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL_STATES

    @property
    def is_claimable(self) -> bool:
        if self.state not in _CLAIMABLE_STATES:
            return False
        if self.state == OperationState.FAILED and self.backoff_until is not None:
            backoff = self.backoff_until
            if backoff.tzinfo is None:
                backoff = backoff.replace(tzinfo=UTC)
            return datetime.now(UTC) >= backoff
        return True

    def can_transition_to(self, next_state: OperationState) -> bool:
        """Validate a state transition against the legal lifecycle."""
        current = self.state
        if current in _TERMINAL_STATES:
            return False
        if next_state == OperationState.CANCELLED:
            return True
        if current == OperationState.PENDING and next_state == OperationState.PROCESSING:
            return True
        if current == OperationState.PROCESSING and next_state in (
            OperationState.COMMITTED,
            OperationState.FAILED,
            OperationState.RECONCILIATION_REQUIRED,
        ):
            return True
        return bool(current == OperationState.FAILED and next_state == OperationState.PROCESSING)
