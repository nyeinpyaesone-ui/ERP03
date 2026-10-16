"""Merge the two concurrent heads left by 0004_invoice_idempotency and 0004_sales_permission.

Both 0004 revisions descend from 0003_user_branch_scope, which leaves alembic
with two heads and makes `alembic upgrade head` fail — blocking CI,
scripts/qualify.sh, and the docker-compose migrate service. This merge revision
re-unifies the graph without rewriting either revision's history, so databases
that already applied either 0004 only need this revision applied afterwards.
"""
import sqlalchemy as sa
from alembic import op

revision = "0005_merge_heads"
down_revision = ("0004_invoice_idempotency", "0004_sales_permission")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Structural merge: no schema change is required.
    pass


def downgrade() -> None:
    # A merge revision cannot be downgraded; roll back the schema changes of
    # the individual 0004 revisions instead.
    pass
