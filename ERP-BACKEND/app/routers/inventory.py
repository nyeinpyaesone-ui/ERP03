from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal

from app.database import get_db
from app.models import Product, InventoryMovement
from app.auth import get_current_user
from app.services.activity_log import log_activity
from app.core.repositories import ProductRepository, InventoryMovementRepository

router = APIRouter()

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: float = 0
    cost_price: Optional[float] = None
    quantity_in_stock: int = 0
    reorder_level: int = 10
    reorder_quantity: int = 50
    supplier: Optional[str] = None
    supplier_contact: Optional[str] = None
    status: str = "active"
    barcode: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: float
    cost_price: Optional[float] = None
    quantity_in_stock: int
    reorder_level: int
    reorder_quantity: int
    supplier: Optional[str] = None
    supplier_contact: Optional[str] = None
    status: str
    barcode: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class MovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: int
    unit_cost: Optional[float] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    movement_type: str
    quantity: int
    unit_cost: Optional[float] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

@router.post("/products", response_model=ProductResponse)
def create_product(data: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a product and record its creation activity.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        data (ProductCreate): Product details, including its SKU.
        current_user: Authenticated user creating the product.
    
    Returns:
        Product: The newly created product.
    """
    repo = ProductRepository(db)
    
    # Check for duplicate SKU using repository
    existing = repo.get_by_sku(data.sku)
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    # Create product using repository
    product = repo.create(data.model_dump())
    
    # Log activity
    log_activity(db, user_id=current_user.id, action="product_created", entity_type="product", entity_id=product.id)
    return product

@router.get("/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None,
    status: Optional[str] = None,
    low_stock: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List products with optional category, status, low-stock, and name filters.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        category (Optional[str]): Restrict results to a product category.
        status (Optional[str]): Restrict results to a product status.
        low_stock (bool): Restrict results to products at or below their reorder level.
        search (Optional[str]): Restrict results to products whose names contain this text.
    
    Returns:
        list[Product]: Matching products.
    """
    repo = ProductRepository(db)
    
    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if status:
        filters["status"] = status
    
    # Use specialized repository methods when available
    if low_stock:
        return repo.get_low_stock_products()
    elif search:
        return repo.search("name", search, limit=100)
    elif filters:
        return repo.filter(filters, limit=100)
    else:
        return repo.list(limit=100)

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve a product by its identifier.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        product_id (int): The product identifier.
    
    Returns:
        Product: The matching product record.
    """
    repo = ProductRepository(db)
    product = repo.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update an existing product with the supplied fields.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        product_id (int): Identifier of the product to update.
        data (ProductCreate): Product fields and values to apply.
    
    Returns:
        Product: The updated product.
    
    Raises:
        HTTPException: If the product does not exist.
    """
    repo = ProductRepository(db)
    product = repo.update(product_id, data.model_dump())
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Delete a product by its identifier.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        product_id (int): Identifier of the product to delete.
    
    Returns:
        dict: Confirmation message indicating that the product was deleted.
    """
    repo = ProductRepository(db)
    if not repo.delete(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

@router.post("/movements", response_model=MovementResponse)
def create_movement(data: MovementCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create an inventory movement and update the associated product's stock.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        data (MovementCreate): Movement details, including the product, movement type, and quantity.
    
    Returns:
        InventoryMovement: The created inventory movement.
    
    Raises:
        HTTPException: If the product does not exist or an outgoing movement exceeds available stock.
    """
    product_repo = ProductRepository(db)
    movement_repo = InventoryMovementRepository(db)
    
    # Get product using repository
    product = product_repo.get(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Create movement
    movement_data = data.model_dump()
    movement_data["created_by"] = current_user.id
    movement = movement_repo.create(movement_data)

    # Update stock based on movement type
    if data.movement_type == "in":
        product.quantity_in_stock += data.quantity
    elif data.movement_type == "out":
        if product.quantity_in_stock < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.quantity_in_stock -= data.quantity
    elif data.movement_type == "adjustment":
        product.quantity_in_stock = data.quantity

    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(movement)
    
    # Log activity
    log_activity(db, user_id=current_user.id, action="inventory_moved", entity_type="inventory_movement", entity_id=movement.id)
    return movement

@router.get("/movements", response_model=List[MovementResponse])
def list_movements(product_id: Optional[int] = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    List inventory movements, optionally filtered by product.
    
    Uses Repository pattern for clean data access separation.
    
    Parameters:
        product_id (Optional[int]): Product identifier used to filter the movements.
    
    Returns:
        List[InventoryMovement]: Inventory movements ordered from newest to oldest.
    """
    repo = InventoryMovementRepository(db)
    
    if product_id:
        return repo.get_by_product(product_id, limit=100)
    else:
        return repo.list(limit=100, order_by="created_at", desc=True)

@router.get("/dashboard")
def inventory_dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get inventory dashboard with key metrics.
    
    Uses Repository pattern for clean data access separation.
    
    Returns:
        dict: Inventory metrics including total products, stock value, low stock count, and categories.
    """
    repo = ProductRepository(db)
    
    total_products = repo.count()
    total_stock_value = repo.get_total_stock_value()
    low_stock_count = len(repo.get_low_stock_products())
    out_of_stock_count = len(repo.get_out_of_stock_products())
    
    # Get category counts
    from sqlalchemy import func
    categories = db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()

    return {
        "total_products": total_products,
        "total_stock_value": total_stock_value,
        "low_stock_count": low_stock_count,
        "out_of_stock": out_of_stock_count,
        "categories": categories
    }

