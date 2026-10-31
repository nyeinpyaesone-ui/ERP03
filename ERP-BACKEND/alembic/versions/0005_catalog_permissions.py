"""Register master-data and purchasing permissions for the catalog APIs."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.db.base import GUID

revision: str = "0005_catalog_permissions"
down_revision: str | Sequence[str] | None = "0004_sales_permission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PERMISSIONS = [
    ("00000000-0000-0000-0000-000000000501", "products.manage", "Create and maintain product catalog"),
    ("00000000-0000-0000-0000-000000000502", "customers.manage", "Create and maintain customer accounts"),
    ("00000000-0000-0000-0000-000000000503", "suppliers.manage", "Create and maintain supplier accounts"),
    ("00000000-0000-0000-0000-000000000504", "purchases.receive", "Receive purchase stock into a warehouse"),
]


def upgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", GUID()),
        sa.column("code", sa.String(120)),
        sa.column("description", sa.String(300)),
    )
    codes = [code for _, code, _ in _PERMISSIONS]
    # Idempotent seed: safe to re-run and portable across PostgreSQL/SQLite.
    op.execute(permissions.delete().where(permissions.c.code.in_(codes)))
    op.bulk_insert(
        permissions,
        [{"id": pid, "code": code, "description": description} for pid, code, description in _PERMISSIONS],
    )


def downgrade() -> None:
    role_permissions = sa.table("role_permissions", sa.column("permission_id", GUID()))
    permissions = sa.table("permissions", sa.column("id", GUID()))
    ids = [pid for pid, _, _ in _PERMISSIONS]
    op.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(ids)))
    op.execute(permissions.delete().where(permissions.c.id.in_(ids)))
