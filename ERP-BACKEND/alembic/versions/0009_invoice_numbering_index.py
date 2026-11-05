"""Composite index on invoices(branch_id, invoice_no) for numbering queries.

Optimizes next_invoice_no() which filters by branch_id and invoice_no prefix.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_invoice_numbering_index"
down_revision: str | Sequence[str] | None = "0008_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_invoices_branch_invoice_no",
        "invoices",
        ["branch_id", "invoice_no"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("ix_invoices_branch_invoice_no", table_name="invoices")
