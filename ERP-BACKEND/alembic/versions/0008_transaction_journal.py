"""Add transaction_journal table for durable idempotent journaling."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import GUID


revision: str = "0008_transaction_journal"
down_revision: str | Sequence[str] | None = "0007_operation_orchestration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transaction_journal",
        sa.Column("transaction_id", sa.String(length=64), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=512), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("metadata_json", JSONB().with_variant(sa.JSON, "sqlite"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_transaction_journal_idempotency"
        ),
    )


def downgrade() -> None:
    op.drop_table("transaction_journal")
