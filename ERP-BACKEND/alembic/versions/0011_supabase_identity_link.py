"""Add an optional, explicitly linked Supabase Auth identity to ERP users."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.db.base import GUID

revision: str = "0011_supabase_identity_link"
down_revision: str | Sequence[str] | None = "0010_txn_journal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("supabase_user_id", GUID(), nullable=True))
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_unique_constraint(
            "uq_users_supabase_user_id", ["supabase_user_id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_supabase_user_id", type_="unique")
        batch_op.drop_column("supabase_user_id")
