from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal

from app.database import get_db
from app.models import Product, InventoryMovement
from app.auth import get_current_user
from app.services.activity_log import log_activity
from app.services.inventory_service import InventoryService

router = APIRouter()


# Request/Response Schemas
class ProductCreate(BaseModel):
    """Schema for creating a product."""
    sku: str = Field(..., min_length=1, max_length=100, description="Unique product SKU")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    unit_price: Decimal = Field(..., ge=0, description="Selling price")
    cost_price: Optional[Decimal] = Field(None, ge=0, description="Cost price")
    quantity_in_stock: int = Field(0, ge=0, description="Current stock quantity")
    reorder_level: int = Field(10, ge=0, description="Stock level triggering reorder")
    reorder_quantity: int = Field(50, ge=0, description="Quantity to reorder")
    supplier: Optional[str] = Field(None, max_length=255, description="Supplier name")
    supplier_contact: Optional[str] = Field(None, max_length=255, description="Supplier contact")
    status: str = Field("active", description="Product status")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    weight: Optional[float] = Field(None, gt=0, description="Product weight")
    dimensions: Optional[str] = Field(None, max_length=100, description="Product dimensions")

    @validator('status')
    def validate_status(cls, v):
        allowed = ['active', 'discontinued', 'draft']
        if v not in allowed:
            raise ValueError(f'Status must be one of: {allowed}')
        return v


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    quantity_in_stock: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=255)
    supplier_contact: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    barcode: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[str] = Field(None, max_length=100)

    @validator('status')
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = ['active', 'discontinued', 'draft']
        if v not in allowed:
            raise ValueError(f'Status must be one of: {allowed}')
        return v


class MovementCreate(BaseModel):
    """Schema for creating a stock movement."""
    product_id: int = Field(..., gt=0, description="Product ID")
    movement_type: str = Field(..., description="Movement type: in, out, adjustment, transfer")
    quantity: int = Field(..., ge=0, description="Movement quantity")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")
    reference: Optional[str] = Field(None, max_length=255, description="Reference number")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes")

    @validator('movement_type')
    def validate_movement_type(cls, v):
        allowed = ['in', 'out', 'adjustment', 'transfer']
        if v not in allowed:
            raise ValueError(f'Movement type must be one of: {allowed}')
        return v


class MovementResponse(BaseModel):
    """Schema for movement response."""
    id: int
    product_id: int
    movement_type: str
    quantity: int
    unit_cost: Optional[Decimal]
    reference: Optional[str]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    unit_price: Decimal
    cost_price: Optional[Decimal]
    quantity_in_stock: int
    reorder_level: int
    reorder_quantity: int
    supplier: Optional[str]
    supplier_contact: Optional[str]
    status: str
    barcode: Optional[str]
    weight: Optional[float]
    dimensions: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """Schema for inventory dashboard."""
    total_products: int
    total_stock_value: float
    low_stock_count: int
    out_of_stock: int
    categories: List[dict]


def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    """Dependency to get inventory service instance."""
    return InventoryService(db)


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Create a new product.
    
    - **sku**: Unique product identifier (required)
    - **name**: Product name (required)
    - **unit_price**: Selling price (required, must be >= 0)
    - **category**: Optional product category
    - **quantity_in_stock**: Initial stock level (default: 0)
    """
    try:
        product = service.create_product(
            sku=data.sku,
            name=data.name,
            unit_price=data.unit_price,
            description=data.description,
            category=data.category,
            cost_price=data.cost_price,
            quantity_in_stock=data.quantity_in_stock,
            reorder_level=data.reorder_level,
            reorder_quantity=data.reorder_quantity,
            supplier=data.supplier,
            supplier_contact=data.supplier_contact,
            status=data.status,
            barcode=data.barcode,
            weight=data.weight,
            dimensions=data.dimensions,
            created_by=current_user.id
        )
        
        # Log activity
        log_activity(
            db,
            user_id=current_user.id,
            action="product_created",
            entity_type="product",
            entity_id=product.id
        )
        
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None,
    status: Optional[str] = None,
    low_stock: bool = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    List products with optional filters.
    
    - **category**: Filter by category
    - **status**: Filter by status (active/discontinued/draft)
    - **low_stock**: Show only products below reorder level
    - **search**: Search in product name
    - **skip**: Pagination offset
    - **limit**: Maximum results (default: 100)
    """
    return service.list_products(
        category=category,
        status=status,
        low_stock=low_stock,
        search=search,
        skip=skip,
        limit=limit
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get a product by ID."""
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Update a product.
    
    Only provided fields will be updated.
    """
    # Filter out None values
    updates = {k: v for k, v in data.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        product = service.update_product(
            product_id=product_id,
            updates=updates,
            updated_by=current_user.id
        )
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Log activity
        log_activity(
            db,
            user_id=current_user.id,
            action="product_updated",
            entity_type="product",
            entity_id=product.id
        )
        
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Delete a product.
    
    This will also delete all associated stock movements.
    """
    success = service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Log activity
    log_activity(
        db,
        user_id=current_user.id,
        action="product_deleted",
        entity_type="product",
        entity_id=product_id
    )
    
    return {"message": "Product deleted successfully"}


@router.post("/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(
    data: MovementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Create a stock movement.
    
    This atomically updates both the movement record and product stock level.
    
    - **movement_type**: Type of movement (in/out/adjustment/transfer)
    - **quantity**: Quantity for movement (must be >= 0)
    - **unit_cost**: Optional unit cost for valuation
    - **reference**: Optional reference number (e.g., PO/SO number)
    """
    try:
        movement = service.create_stock_movement(
            product_id=data.product_id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            reference=data.reference,
            notes=data.notes,
            created_by=current_user.id
        )
        
        # Log activity
        log_activity(
            db,
            user_id=current_user.id,
            action="inventory_moved",
            entity_type="inventory_movement",
            entity_id=movement.id
        )
        
        return movement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/movements", response_model=List[MovementResponse])
def list_movements(
    product_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    List inventory movements with optional filters.
    
    - **product_id**: Filter by product
    - **movement_type**: Filter by movement type
    - **skip**: Pagination offset
    - **limit**: Maximum results (default: 100)
    """
    return service.get_movements(
        product_id=product_id,
        movement_type=movement_type,
        skip=skip,
        limit=limit
    )


@router.get("/dashboard", response_model=DashboardResponse)
def inventory_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """
    Get inventory dashboard statistics.
    
    Returns:
    - Total number of products
    - Total stock value
    - Count of low stock items
    - Count of out of stock items
    - Breakdown by category
    """
    return service.get_dashboard_stats()


@router.get("/alerts/low-stock", response_model=List[ProductResponse])
def get_low_stock_alerts(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get products below reorder level."""
    return service.get_low_stock_products(limit=limit)


@router.get("/alerts/out-of-stock", response_model=List[ProductResponse])
def get_out_of_stock_alerts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get products with zero stock."""
    return service.get_out_of_stock_products()

