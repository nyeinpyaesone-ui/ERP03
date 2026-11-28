"""Add durable business-scoped POS sale idempotency."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_invoice_idempotency"
down_revision: str | Sequence[str] | None = "0003_user_branch_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite cannot ALTER constraints in-place; batch mode rebuilds the table
    # with the new unique constraint on both supported backends.
    with op.batch_alter_table(
        "invoices",
        recreate="auto",
        naming_convention={"uq": "uq_invoices_idempotency"},
    ) as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint(
            "uq_invoices_idempotency",
            ["business_id", "branch_id", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("invoices", recreate="auto") as batch_op:
        batch_op.drop_constraint("uq_invoices_idempotency", type_="unique")
        batch_op.drop_column("idempotency_key")
