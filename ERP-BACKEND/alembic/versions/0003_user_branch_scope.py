"""Scope users to a branch when required."""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from app.db.base import GUID

revision: str = "0003_user_branch_scope"
down_revision: str | Sequence[str] | None = "0002_transactional_erp"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite cannot ALTER constraints in-place; batch mode rebuilds the table
    # with the new FK column on both supported backends.
    with op.batch_alter_table("users", recreate="auto") as batch_op:
        batch_op.add_column(
            sa.Column("branch_id", GUID(), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True)
        )
    op.create_index("ix_users_branch_active", "users", ["branch_id", "active"])


def downgrade() -> None:
    op.drop_index("ix_users_branch_active", table_name="users")
    with op.batch_alter_table("users", recreate="auto") as batch_op:
        batch_op.drop_column("branch_id")
