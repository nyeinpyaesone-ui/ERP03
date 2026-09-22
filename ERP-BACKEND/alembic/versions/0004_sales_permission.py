"""Register the permission required to create POS sales."""

from collections.abc import Sequence
from uuid import UUID

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_sales_permission"
down_revision: str | Sequence[str] | None = "0003_user_branch_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PERMISSION_ID = UUID("00000000-0000-0000-0000-000000000401")


def upgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(120)),
        sa.column("description", sa.String(300)),
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
    op.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id = :permission_id
            """
        ),
        {"permission_id": str(_PERMISSION_ID)},
    )
    op.execute(
        sa.text("DELETE FROM permissions WHERE id = :permission_id"),
        {"permission_id": str(_PERMISSION_ID)},
    )
