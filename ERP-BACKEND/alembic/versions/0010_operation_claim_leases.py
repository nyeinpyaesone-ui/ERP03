"""Fence operation workers with expiring claim tokens.

Revision ID: 0010_operation_claim_leases
Revises: 0009_invoice_numbering_index
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0010_operation_claim_leases"
down_revision: str | Sequence[str] | None = "0009_invoice_numbering_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("operations") as batch_op:
        batch_op.add_column(sa.Column("claim_token", sa.String(length=64), nullable=True))
        batch_op.add_column(
            sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.alter_column(
            "operation_type",
            existing_type=sa.String(length=80),
            type_=sa.String(length=100),
            existing_nullable=False,
        )

    op.create_index(
        "ix_operations_state_lease_expiry",
        "operations",
        ["state", "lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_operations_state_lease_expiry", table_name="operations")
    with op.batch_alter_table("operations") as batch_op:
        batch_op.alter_column(
            "operation_type",
            existing_type=sa.String(length=100),
            type_=sa.String(length=80),
            existing_nullable=False,
        )
        batch_op.drop_column("lease_expires_at")
        batch_op.drop_column("claim_token")
