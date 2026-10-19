"""Durable cross-module operation orchestration table."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.db.base import GUID


revision: str = "0007_operation_orchestration"
down_revision: str | Sequence[str] | None = "0006_invoice_fingerprint"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "operations",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("operation_id", sa.String(length=255), nullable=False),
        sa.Column("operation_type", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("business_id", GUID(), nullable=False),
        sa.Column("branch_id", GUID(), nullable=True),
        sa.Column(
            "payload_json",
            sa.Text(),
            nullable=False,
        ),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("backoff_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_by", sa.String(length=128), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("operation_id", name="uq_operations_operation_id"),
    )
    op.create_index(
        "ix_operations_state_updated", "operations", ["state", "updated_at"]
    )
    op.create_index(
        "ix_operations_business_state", "operations", ["business_id", "state"]
    )


def downgrade() -> None:
    op.drop_index("ix_operations_business_state", table_name="operations")
    op.drop_index("ix_operations_state_updated", table_name="operations")
    op.drop_table("operations")
