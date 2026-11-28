"""Add idempotent customer receivable collections to payment records."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0012_receivable_collection_idempotency"
down_revision: str | Sequence[str] | None = "0011_supabase_identity_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.add_column("payments", sa.Column("request_fingerprint", sa.String(64), nullable=True))
    with op.batch_alter_table("payments") as batch_op:
        batch_op.create_unique_constraint(
            "uq_payments_invoice_idempotency",
            ["business_id", "branch_id", "invoice_id", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch_op:
        batch_op.drop_constraint("uq_payments_invoice_idempotency", type_="unique")
        batch_op.drop_column("request_fingerprint")
        batch_op.drop_column("idempotency_key")
