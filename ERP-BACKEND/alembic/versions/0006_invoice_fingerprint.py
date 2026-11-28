"""Store request fingerprint on invoices for idempotency payload-conflict detection."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_invoice_fingerprint"
down_revision: str | Sequence[str] | None = "0005_catalog_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("invoices", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("request_fingerprint", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("invoices", recreate="auto") as batch_op:
        batch_op.drop_column("request_fingerprint")
