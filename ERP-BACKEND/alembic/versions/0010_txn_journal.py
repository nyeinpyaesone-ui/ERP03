"""Add shared tenant-scoped transaction journal."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "0010_txn_journal"
down_revision: str | Sequence[str] | None = "0009_invoice_numbering_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transaction_journal",
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("business_id", sa.String(length=255), nullable=False),
        sa.Column("idempotency_key", sa.String(length=218), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "metadata_json",
            JSONB().with_variant(JSON, "sqlite"),
            nullable=False,
        ),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("transaction_id"),
        sa.UniqueConstraint(
            "business_id",
            "idempotency_key",
            name="uq_transaction_journal_business_key",
        ),
    )
    op.create_index(
        "ix_transaction_journal_business_transaction",
        "transaction_journal",
        ["business_id", "transaction_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transaction_journal_business_transaction",
        table_name="transaction_journal",
    )
    op.drop_table("transaction_journal")
