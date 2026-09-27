"""Add transactional ERP entities for inventory, sales and payments."""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_transactional_erp"
down_revision: str | Sequence[str] | None = "0001_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    uuid = _uuid()

    op.create_table(
        "customers",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("business_id", uuid, sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", uuid, sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("credit_limit", sa.Numeric(18, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "code", name="uq_customers_business_code"),
    )
    op.create_index("ix_customers_branch_active", "customers", ["branch_id", "active"])
    op.create_index("ix_customers_business_name", "customers", ["business_id", "name"])

    op.create_table(
        "suppliers",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("business_id", uuid, sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", uuid, sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("payable_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "code", name="uq_suppliers_business_code"),
    )
    op.create_index("ix_suppliers_branch_active", "suppliers", ["branch_id", "active"])

    op.create_table(
        "products",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("business_id", uuid, sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", uuid, sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("barcode", sa.String(80)),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("sale_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("cost_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("min_stock", sa.Numeric(18, 3), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("business_id", "sku", name="uq_products_business_sku"),
    )
    op.create_index("ix_products_branch_active", "products", ["branch_id", "active"])
    op.create_index("ix_products_business_name", "products", ["business_id", "name"])
    op.create_index("ix_products_barcode", "products", ["business_id", "barcode"])

    op.create_table(
        "warehouses",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("branch_id", uuid, sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("branch_id", "code", name="uq_warehouses_branch_code"),
    )

    op.create_table(
        "stock_balances",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("warehouse_id", uuid, sa.ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", uuid, sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("warehouse_id", "product_id", name="uq_stock_balances_warehouse_product"),
    )
    op.create_index("ix_stock_balances_product", "stock_balances", ["product_id"])

    op.create_table(
        "stock_movements",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("warehouse_id", uuid, sa.ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_id", uuid, sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(18, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("reference_type", sa.String(40)),
        sa.Column("reference_id", uuid),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stock_movements_warehouse_created", "stock_movements", ["warehouse_id", "created_at"])
    op.create_index("ix_stock_movements_product_created", "stock_movements", ["product_id", "created_at"])

    op.create_table(
        "invoices",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("business_id", uuid, sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", uuid, sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", uuid, sa.ForeignKey("customers.id", ondelete="RESTRICT")),
        sa.Column("invoice_no", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax", sa.Numeric(18, 2), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("paid", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("branch_id", "invoice_no", name="uq_invoices_branch_no"),
    )
    op.create_index("ix_invoices_branch_status_created", "invoices", ["branch_id", "status", "created_at"])
    op.create_index("ix_invoices_customer_created", "invoices", ["customer_id", "created_at"])

    op.create_table(
        "invoice_items",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("invoice_id", uuid, sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", uuid, sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount", sa.Numeric(18, 2), nullable=False),
        sa.Column("tax", sa.Numeric(18, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(18, 2), nullable=False),
    )
    op.create_index("ix_invoice_items_invoice", "invoice_items", ["invoice_id"])

    op.create_table(
        "payments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("business_id", uuid, sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", uuid, sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("invoice_id", uuid, sa.ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("reference", sa.String(120)),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payments_branch_created", "payments", ["branch_id", "created_at"])
    op.create_index("ix_payments_invoice", "payments", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_invoice", table_name="payments")
    op.drop_index("ix_payments_branch_created", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_invoice_items_invoice", table_name="invoice_items")
    op.drop_table("invoice_items")
    op.drop_index("ix_invoices_customer_created", table_name="invoices")
    op.drop_index("ix_invoices_branch_status_created", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_stock_movements_product_created", table_name="stock_movements")
    op.drop_index("ix_stock_movements_warehouse_created", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("ix_stock_balances_product", table_name="stock_balances")
    op.drop_table("stock_balances")
    op.drop_table("warehouses")
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_index("ix_products_business_name", table_name="products")
    op.drop_index("ix_products_branch_active", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_suppliers_branch_active", table_name="suppliers")
    op.drop_table("suppliers")
    op.drop_index("ix_customers_business_name", table_name="customers")
    op.drop_index("ix_customers_branch_active", table_name="customers")
    op.drop_table("customers")
