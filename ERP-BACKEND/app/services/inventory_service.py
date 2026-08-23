"""
Inventory Service Layer - Business Logic and Transactions

This module contains the core business logic for inventory operations,
separated from the API layer for better testability and maintainability.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Product, InventoryMovement, User


class InventoryService:
    """Service class for inventory business operations."""
    
    def __init__(self, db: Session):
        """Initialize the inventory service with a database session."""
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
        created_by: Optional[int] = None
    ) -> Product:
        """
        Create and persist a product after validating its SKU, prices, and stock levels.
        
        Parameters:
            sku (str): Unique product SKU.
            name (str): Product name.
            unit_price (Decimal): Selling price.
            reorder_level (int): Stock quantity at which reordering is triggered.
            reorder_quantity (int): Quantity to reorder.
            updates (dict): Product attributes to store, when applicable.
        
        Returns:
            Product: The newly created product.
        
        Raises:
            ValueError: If the SKU already exists or a price or stock value is negative.
        """
        # Check for duplicate SKU
        existing = self.db.query(Product).filter(Product.sku == sku).first()
        if existing:
            raise ValueError(f"Product with SKU '{sku}' already exists")
        
        # Validate prices
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        if cost_price is not None and cost_price < 0:
            raise ValueError("Cost price cannot be negative")
        
        # Validate stock levels
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
            dimensions=dimensions
        )
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def get_product(self, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Retrieve a product by its stock-keeping unit.
        
        Parameters:
        	sku (str): The product's stock-keeping unit.
        
        Returns:
        	Optional[Product]: The matching product, or `None` if no product has the SKU.
        """
        return self.db.query(Product).filter(Product.sku == sku).first()
    
    def list_products(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        low_stock: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        List products with optional category, status, stock, name, and pagination filters.
        
        Parameters:
            category (Optional[str]): Category to filter by.
            status (Optional[str]): Status to filter by.
            low_stock (bool): Whether to include only products at or below their reorder level.
            search (Optional[str]): Case-insensitive text to search for in product names.
            skip (int): Number of matching products to skip.
            limit (int): Maximum number of products to return.
        
        Returns:
            List[Product]: Matching products.
        """
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
        updated_by: Optional[int] = None
    ) -> Optional[Product]:
        """
        Update a product and persist the changes.
        
        Parameters:
            product_id (int): Identifier of the product to update.
            updates (dict): Product fields and values to change.
            updated_by (Optional[int]): Identifier of the user performing the update.
        
        Returns:
            Optional[Product]: The updated product, or `None` if the product does not exist.
        
        Raises:
            ValueError: If the SKU is already used, a price is negative, or stock quantity is negative.
        """
        product = self.get_product(product_id)
        if not product:
            return None
        
        # Validate updates before applying
        if 'sku' in updates:
            existing = self.db.query(Product).filter(
                Product.sku == updates['sku'],
                Product.id != product_id
            ).first()
            if existing:
                raise ValueError(f"Product with SKU '{updates['sku']}' already exists")
        
        if 'unit_price' in updates and updates['unit_price'] < 0:
            raise ValueError("Unit price cannot be negative")
        
        if 'cost_price' in updates and updates['cost_price'] is not None:
            if updates['cost_price'] < 0:
                raise ValueError("Cost price cannot be negative")
        
        if 'quantity_in_stock' in updates and updates['quantity_in_stock'] < 0:
            raise ValueError("Stock quantity cannot be negative")
        
        # Apply updates
        for key, value in updates.items():
            setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product by its identifier.
        
        Parameters:
            product_id (int): Identifier of the product to delete.
        
        Returns:
            bool: `True` if the product was deleted, `False` if it was not found.
        """
        product = self.get_product(product_id)
        if not product:
            return False
        
        self.db.delete(product)
        self.db.commit()
        return True
    
    def create_stock_movement(
        self,
        product_id: int,
        movement_type: str,
        quantity: int,
        unit_cost: Optional[Decimal] = None,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> InventoryMovement:
        """
        Create an inventory movement and update the product stock atomically.
        
        Args:
            product_id: ID of the product affected by the movement.
            movement_type: Movement type: ``"in"``, ``"out"``, ``"adjustment"``, or
                ``"transfer"``.
            quantity: Movement quantity, which must be nonnegative.
            unit_cost: Optional cost per unit.
            reference: Optional reference number for the movement.
            notes: Optional notes about the movement.
            created_by: Optional ID of the user who created the movement.
        
        Returns:
            The created inventory movement.
        
        Raises:
            ValueError: If the movement type is invalid, the quantity is negative, the
                product does not exist, or an outbound movement exceeds available stock.
        """
        valid_types = ["in", "out", "adjustment", "transfer"]
        if movement_type not in valid_types:
            raise ValueError(f"Invalid movement type. Must be one of: {valid_types}")
        
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        product = self.get_product(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Begin transaction
        try:
            # Create movement record
            movement = InventoryMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reference=reference,
                notes=notes,
                created_by=created_by
            )
            
            # Update stock based on movement type
            if movement_type == "in":
                product.quantity_in_stock += quantity
            elif movement_type == "out":
                if product.quantity_in_stock < quantity:
                    raise ValueError(
                        f"Insufficient stock. Available: {product.quantity_in_stock}, "
                        f"Requested: {quantity}"
                    )
                product.quantity_in_stock -= quantity
            elif movement_type == "adjustment":
                product.quantity_in_stock = quantity
            elif movement_type == "transfer":
                # Transfer doesn't change total stock, just location
                pass
            
            product.updated_at = datetime.utcnow()
            
            self.db.add(movement)
            self.db.commit()
            self.db.refresh(movement)
            
            return movement
            
        except Exception as e:
            self.db.rollback()
            raise
    
    def get_movements(
        self,
        product_id: Optional[int] = None,
        movement_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """
        List inventory movements with optional product and movement-type filters.
        
        Parameters:
            product_id (Optional[int]): ID of the product whose movements should be listed.
            movement_type (Optional[str]): Type of movement to include.
            skip (int): Number of movements to skip.
            limit (int): Maximum number of movements to return.
        
        Returns:
            List[InventoryMovement]: Movements ordered from newest to oldest.
        """
        query = self.db.query(InventoryMovement)
        
        if product_id:
            query = query.filter(InventoryMovement.product_id == product_id)
        if movement_type:
            query = query.filter(InventoryMovement.movement_type == movement_type)
        
        return query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_dashboard_stats(self) -> dict:
        """
        Collect aggregate inventory metrics for dashboard reporting.
        
        Returns:
            dict: A dictionary containing total product count, total stock value,
            low-stock count, out-of-stock count, and per-category product counts
            and stock values.
        """
        total_products = self.db.query(Product).count()
        
        total_stock_value = self.db.query(
            func.sum(Product.quantity_in_stock * Product.unit_price)
        ).scalar() or Decimal("0")
        
        low_stock_count = self.db.query(Product).filter(
            Product.quantity_in_stock <= Product.reorder_level
        ).count()
        
        out_of_stock = self.db.query(Product).filter(
            Product.quantity_in_stock == 0
        ).count()
        
        # Category breakdown
        categories = self.db.query(
            Product.category,
            func.count(Product.id).label('product_count'),
            func.sum(Product.quantity_in_stock * Product.unit_price).label('total_value')
        ).group_by(Product.category).all()
        
        category_breakdown = [
            {
                "category": cat.category or "Uncategorized",
                "product_count": count,
                "total_value": float(value) if value else 0
            }
            for cat, count, value in categories
        ]
        
        return {
            "total_products": total_products,
            "total_stock_value": float(total_stock_value),
            "low_stock_count": low_stock_count,
            "out_of_stock": out_of_stock,
            "categories": category_breakdown
        }
    
    def get_low_stock_products(self, limit: int = 50) -> List[Product]:
        """
        Identify products whose stock is at or below their reorder level.
        
        Parameters:
            limit (int): Maximum number of products to return.
        
        Returns:
            List[Product]: Products ordered by increasing stock quantity.
        """
        return self.db.query(Product).filter(
            Product.quantity_in_stock <= Product.reorder_level
        ).order_by(
            Product.quantity_in_stock.asc()
        ).limit(limit).all()
    
    def get_out_of_stock_products(self) -> List[Product]:
        """Get products with zero stock."""
        return self.db.query(Product).filter(
            Product.quantity_in_stock == 0
        ).all()
