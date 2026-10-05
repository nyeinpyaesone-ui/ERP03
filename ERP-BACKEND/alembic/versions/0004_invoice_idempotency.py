"""Add durable business-scoped POS sale idempotency."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_invoice_idempotency"
down_revision: str | Sequence[str] | None = "0003_user_branch_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.create_unique_constraint(
        "uq_invoices_idempotency",
        "invoices",
        ["business_id", "branch_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_invoices_idempotency", "invoices", type_="unique")
    op.drop_column("invoices", "idempotency_key")
