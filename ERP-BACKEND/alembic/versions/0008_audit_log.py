"""Audit log table for tamper-evident business operation tracking."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import GUID


revision: str = "0008_audit_log"
down_revision: str | Sequence[str] | None = "0007_operation_orchestration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("business_id", GUID(), nullable=True),
        sa.Column("user_id", GUID(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("request_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "before",
            JSONB().with_variant(JSON, "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "after",
            JSONB().with_variant(JSON, "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "metadata_json",
            JSONB().with_variant(JSON, "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_logs_business_created", "audit_logs", ["business_id", "created_at"]
    )
    op.create_index(
        "ix_audit_logs_action_created", "audit_logs", ["action", "created_at"]
    )
    op.create_index(
        "ix_audit_logs_user_created", "audit_logs", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_created", "audit_logs")
    op.drop_index("ix_audit_logs_business_created", "audit_logs")
    op.drop_table("audit_logs")
