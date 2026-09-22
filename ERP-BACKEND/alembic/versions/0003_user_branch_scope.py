"""Scope users to a branch when required."""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_user_branch_scope"
down_revision: str | Sequence[str] | None = "0002_transactional_erp"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True))
    op.create_index("ix_users_branch_active", "users", ["branch_id", "active"])


def downgrade() -> None:
    op.drop_index("ix_users_branch_active", table_name="users")
    op.drop_column("users", "branch_id")
