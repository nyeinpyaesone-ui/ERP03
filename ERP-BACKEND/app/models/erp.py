from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("business_id", "code", name="uq_customers_business_code"),
        Index("ix_customers_branch_active", "branch_id", "active"),
        Index("ix_customers_business_name", "business_id", "name"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"))
    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"))
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(32))
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        UniqueConstraint("business_id", "code", name="uq_suppliers_business_code"),
        Index("ix_suppliers_branch_active", "branch_id", "active"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"))
    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"))
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(32))
    payable_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="uq_products_business_sku"),
        Index("ix_products_branch_active", "branch_id", "active"),
        Index("ix_products_business_name", "business_id", "name"),
        Index("ix_products_barcode", "business_id", "barcode"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"))
    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"))
    sku: Mapped[str] = mapped_column(String(80))
    barcode: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(240))
    unit: Mapped[str] = mapped_column(String(32), default="pcs")
    sale_price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    cost_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    min_stock: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("branch_id", "code", name="uq_warehouses_branch_code"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockBalance(Base):
    __tablename__ = "stock_balances"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_stock_balances_warehouse_product"),
        Index("ix_stock_balances_product", "product_id"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"))
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_stock_movements_warehouse_created", "warehouse_id", "created_at"),
        Index("ix_stock_movements_product_created", "product_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"))
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"))
    movement_type: Mapped[str] = mapped_column(String(32))
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(18, 3))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    reference_type: Mapped[str | None] = mapped_column(String(40))
    reference_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("branch_id", "invoice_no", name="uq_invoices_branch_no"),
        Index("ix_invoices_branch_status_created", "branch_id", "status", "created_at"),
        Index("ix_invoices_customer_created", "customer_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"))
    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"))
    customer_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"))
    invoice_no: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="draft")
    currency: Mapped[str] = mapped_column(String(3), default="MMK")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (Index("ix_invoice_items_invoice", "invoice_id"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    invoice_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"))
    product_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2))


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_branch_created", "branch_id", "created_at"),
        Index("ix_payments_invoice", "invoice_id"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"))
    branch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"))
    invoice_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"))
    method: Mapped[str] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3), default="MMK")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    reference: Mapped[str | None] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
