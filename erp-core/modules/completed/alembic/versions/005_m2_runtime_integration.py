"""M2 runtime ERP-AI integration tables.

Revision ID: 005
Revises: 004
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ERP-AI integration tables and their supporting indexes."""
    op.create_table(
        "integration_purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_number", sa.String(length=50), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("po_number", name="uq_integration_po_number"),
    )
    op.create_index("ix_integration_po_number", "integration_purchase_orders", ["po_number"], unique=True)
    op.create_index("ix_integration_po_requester", "integration_purchase_orders", ["requester_id"])
    op.create_index("ix_integration_po_status", "integration_purchase_orders", ["status"])

    op.create_table(
        "integration_po_approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("po_id", sa.Integer(), sa.ForeignKey("integration_purchase_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approval_level", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_integration_po_approval_po", "integration_po_approvals", ["po_id"])

    op.create_table(
        "integration_commands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("command_id", sa.String(length=36), nullable=False),
        sa.Column("command_type", sa.String(length=64), nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_integration_command_idempotency"),
    )
    op.create_index("ix_integration_command_id", "integration_commands", ["command_id"])
    op.create_index("ix_integration_command_correlation", "integration_commands", ["correlation_id"])


def downgrade() -> None:
    """
    Remove the ERP-AI integration tables and their associated indexes.
    """
    op.drop_index("ix_integration_command_correlation", table_name="integration_commands")
    op.drop_index("ix_integration_command_id", table_name="integration_commands")
    op.drop_table("integration_commands")
    op.drop_index("ix_integration_po_approval_po", table_name="integration_po_approvals")
    op.drop_table("integration_po_approvals")
    op.drop_index("ix_integration_po_status", table_name="integration_purchase_orders")
    op.drop_index("ix_integration_po_requester", table_name="integration_purchase_orders")
    op.drop_index("ix_integration_po_number", table_name="integration_purchase_orders")
    op.drop_table("integration_purchase_orders")
