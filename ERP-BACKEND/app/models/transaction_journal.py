"""Shared tenant-scoped transaction journal persisted in the application database."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class TransactionJournal(Base):
    """Accepted transaction intent with database-enforced tenant idempotency.

    This record is not the domain ledger. A business operation is committed
    only when its authoritative domain transaction commits.
    """

    __tablename__ = "transaction_journal"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "idempotency_key",
            name="uq_transaction_journal_business_key",
        ),
        Index(
            "ix_transaction_journal_business_transaction",
            "business_id",
            "transaction_id",
        ),
    )

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    business_id: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(218), nullable=False)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
    )
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="accepted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
