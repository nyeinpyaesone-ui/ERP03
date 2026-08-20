"""
Inventory Service Layer - Business Logic and Transactions

This module contains the core business logic for inventory operations,
separated from the API layer for better testability and maintainability.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models import Product, InventoryMovement, User


class InventoryService:
    """Service class for inventory business operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_product(
        self,
        sku: str,
        name: str,
        unit_price: Decimal,
        description: Optional[str] = None,
        category: Optional[str] = None,
        cost_price: Optional[Decimal] = None,
        quantity_in_stock: int = 0,
        reorder_level: int = 10,
        reorder_quantity: int = 50,
        supplier: Optional[str] = None,
        supplier_contact: Optional[str] = None,
        status: str = "active",
        barcode: Optional[str] = None,
        weight: Optional[float] = None,
        dimensions: Optional[str] = None,
        created_by: Optional[int] = None,
        commit: bool = True,
    ) -> Product:
        """Create a new product with validation.

        ``commit=False`` lets an API use-case include the mutation and its
        audit event in one database transaction.
        """
        existing = self.db.query(Product).filter(Product.sku == sku).first()
        if existing:
            raise ValueError(f"Product with SKU '{sku}' already exists")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        if cost_price is not None and cost_price < 0:
            raise ValueError("Cost price cannot be negative")
        if quantity_in_stock < 0:
            raise ValueError("Initial stock cannot be negative")
        if reorder_level < 0:
            raise ValueError("Reorder level cannot be negative")
        if reorder_quantity < 0:
            raise ValueError("Reorder quantity cannot be negative")

        product = Product(
            sku=sku,
            name=name,
            description=description,
            category=category,
            unit_price=unit_price,
            cost_price=cost_price,
            quantity_in_stock=quantity_in_stock,
            reorder_level=reorder_level,
            reorder_quantity=reorder_quantity,
            supplier=supplier,
            supplier_contact=supplier_contact,
            status=status,
            barcode=barcode,
            weight=weight,
            dimensions=dimensions,
        )

        self.db.add(product)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get a product by SKU."""
        return self.db.query(Product).filter(Product.sku == sku).first()

    def list_products(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        low_stock: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        """List products with optional filters."""
        query = self.db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if status:
            query = query.filter(Product.status == status)
        if low_stock:
            query = query.filter(Product.quantity_in_stock <= Product.reorder_level)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        return query.offset(skip).limit(limit).all()

    def update_product(
        self,
        product_id: int,
        updates: dict,
        updated_by: Optional[int] = None,
        commit: bool = True,
    ) -> Optional[Product]:
        """Update a product with validation."""
        product = self.get_product(product_id)
        if not product:
            return None

        if "sku" in updates:
            existing = self.db.query(Product).filter(
                Product.sku == updates["sku"],
                Product.id != product_id,
            ).first()
            if existing:
                raise ValueError(f"Product with SKU '{updates['sku']}' already exists")

        if "unit_price" in updates and updates["unit_price"] < 0:
            raise ValueError("Unit price cannot be negative")
        if "cost_price" in updates and updates["cost_price"] is not None and updates["cost_price"] < 0:
            raise ValueError("Cost price cannot be negative")
        if "quantity_in_stock" in updates and updates["quantity_in_stock"] < 0:
            raise ValueError("Stock quantity cannot be negative")

        for key, value in updates.items():
            setattr(product, key, value)
        product.updated_at = datetime.utcnow()

        if commit:
            self.db.commit()
        else:
            self.db.flush()
        self.db.refresh(product)
        return product

    def delete_product(self, product_id: int, commit: bool = True) -> bool:
        """Delete a product."""
        product = self.get_product(product_id)
        if not product:
            return False
        self.db.delete(product)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return True

    def create_stock_movement(
        self,
        product_id: int,
        movement_type: str,
        quantity: int,
        unit_cost: Optional[Decimal] = None,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None,
        commit: bool = True,
    ) -> InventoryMovement:
        """Create a stock movement with transaction safety."""
        valid_types = ["in", "out", "adjustment", "transfer"]
        if movement_type not in valid_types:
            raise ValueError(f"Invalid movement type. Must be one of: {valid_types}")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        try:
            product = (
                self.db.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )
            if not product:
                raise ValueError(f"Product with ID {product_id} not found")

            movement = InventoryMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reference=reference,
                notes=notes,
                created_by=created_by,
            )

            if movement_type == "in":
                product.quantity_in_stock += quantity
            elif movement_type == "out":
                if product.quantity_in_stock < quantity:
                    raise ValueError(
                        f"Insufficient stock. Available: {product.quantity_in_stock}, Requested: {quantity}"
                    )
                product.quantity_in_stock -= quantity
            elif movement_type == "adjustment":
                product.quantity_in_stock = quantity
            elif movement_type == "transfer":
                pass

            product.updated_at = datetime.utcnow()
            self.db.add(movement)
            if commit:
                self.db.commit()
            else:
                self.db.flush()
            self.db.refresh(movement)
            return movement
        except Exception:
            self.db.rollback()
            raise

    def get_movements(
        self,
        product_id: Optional[int] = None,
        movement_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[InventoryMovement]:
        """Get inventory movements with optional filters."""
        query = self.db.query(InventoryMovement)
        if product_id:
            query = query.filter(InventoryMovement.product_id == product_id)
        if movement_type:
            query = query.filter(InventoryMovement.movement_type == movement_type)
        return query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()

    def get_dashboard_stats(self) -> dict:
        """Get inventory dashboard statistics using bounded aggregate queries."""
        metrics = self.db.query(
            func.count(Product.id).label("total_products"),
            func.coalesce(func.sum(Product.quantity_in_stock * Product.unit_price), 0).label("total_stock_value"),
            func.coalesce(
                func.sum(case((Product.quantity_in_stock <= Product.reorder_level, 1), else_=0)), 0
            ).label("low_stock_count"),
            func.coalesce(func.sum(case((Product.quantity_in_stock == 0, 1), else_=0)), 0).label("out_of_stock"),
        ).one()

        categories = self.db.query(
            Product.category,
            func.count(Product.id).label("product_count"),
            func.sum(Product.quantity_in_stock * Product.unit_price).label("total_value"),
        ).group_by(Product.category).all()

        category_breakdown = [
            {
                "category": cat.category or "Uncategorized",
                "product_count": count,
                "total_value": float(value) if value else 0,
            }
            for cat, count, value in categories
        ]

        return {
            "total_products": int(metrics.total_products or 0),
            "total_stock_value": float(metrics.total_stock_value or 0),
            "low_stock_count": int(metrics.low_stock_count or 0),
            "out_of_stock": int(metrics.out_of_stock or 0),
            "categories": category_breakdown,
        }

    def get_low_stock_products(self, limit: int = 50) -> List[Product]:
        """Get products below reorder level."""
        return self.db.query(Product).filter(
            Product.quantity_in_stock <= Product.reorder_level
        ).order_by(Product.quantity_in_stock.asc()).limit(limit).all()

    def get_out_of_stock_products(self) -> List[Product]:
        """Get products with zero stock."""
        return self.db.query(Product).filter(Product.quantity_in_stock == 0).all()
