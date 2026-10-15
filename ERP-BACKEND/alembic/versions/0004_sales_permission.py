"""Register the permission required to create POS sales."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.db.base import GUID

revision: str = "0004_sales_permission"
down_revision: str | Sequence[str] | None = "0004_invoice_idempotency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PERMISSION_ID = "00000000-0000-0000-0000-000000000401"


def upgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", GUID()),
        sa.column("code", sa.String(120)),
        sa.column("description", sa.String(300)),
    )
    # Idempotent seed: safe to re-run and portable across PostgreSQL/SQLite.
    op.execute(
        permissions.delete().where(permissions.c.code == "sales.create")
    )
    op.bulk_insert(
        permissions,
        [{
            "id": _PERMISSION_ID,
            "code": "sales.create",
            "description": "Create POS sales and invoices",
        }],
    )


def downgrade() -> None:
    role_permissions = sa.table(
        "role_permissions",
        sa.column("permission_id", GUID()),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", GUID()),
    )
    op.execute(role_permissions.delete().where(role_permissions.c.permission_id == _PERMISSION_ID))
    op.execute(permissions.delete().where(permissions.c.id == _PERMISSION_ID))
