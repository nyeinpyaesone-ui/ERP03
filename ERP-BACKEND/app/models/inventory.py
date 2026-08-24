"""Inventory Management Models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    """Product model for inventory management"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    unit_price = Column(Numeric(15, 2), nullable=False, server_default="0")
    cost_price = Column(Numeric(15, 2), nullable=True)
    quantity_in_stock = Column(Integer, nullable=False, server_default="0")
    reorder_level = Column(Integer, nullable=False, server_default="10")
    reorder_quantity = Column(Integer, nullable=False, server_default="50")
    supplier = Column(String(255), nullable=True)
    supplier_contact = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="active")
    barcode = Column(String(100), nullable=True)
    weight = Column(Float, nullable=True)
    dimensions = Column(String(100), nullable=True)

    movements = relationship("InventoryMovement", back_populates="product", cascade="all, delete-orphan")
    invoice_items = relationship("InvoiceItem", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class InventoryMovement(Base, TimestampMixin):
    """Track inventory movements (in, out, adjustments, transfers)"""
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(String(50), nullable=False)  # in, out, adjustment, transfer
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(15, 2), nullable=True)
    reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    product = relationship("Product", back_populates="movements")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<InventoryMovement(id={self.id}, product_id={self.product_id}, type='{self.movement_type}')>"


class StockAdjustment(Base, TimestampMixin):
    """Manual stock adjustments with approval workflow"""
    __tablename__ = "stock_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    adjustment_type = Column(String(50), nullable=False)  # increase, decrease
    quantity = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")  # pending, approved, rejected
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship("Product")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<StockAdjustment(id={self.id}, product_id={self.product_id}, status='{self.status}')>"


class Warehouse(Base, TimestampMixin):
    """Warehouse/location management"""
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    manager = relationship("User")

    def __repr__(self):
        return f"<Warehouse(id={self.id}, code='{self.code}', name='{self.name}')>"


class WarehouseStock(Base, TimestampMixin):
    """Stock levels per warehouse"""
    __tablename__ = "warehouse_stock"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, server_default="0")
    reserved_quantity = Column(Integer, nullable=False, server_default="0")
    bin_location = Column(String(100), nullable=True)

    warehouse = relationship("Warehouse")
    product = relationship("Product")

    def __repr__(self):
        return f"<WarehouseStock(warehouse_id={self.warehouse_id}, product_id={self.product_id})>"
