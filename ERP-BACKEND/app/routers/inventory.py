from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from app.database import get_db
from app.models import Product, InventoryMovement
from app.auth import get_current_user
from app.services.activity_log import log_activity
from app.services.inventory_service import InventoryService

router = APIRouter()


class ProductCreate(BaseModel):
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

    @validator("status")
    def validate_status(cls, v):
        allowed = ["active", "discontinued", "draft"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v


class ProductUpdate(BaseModel):
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

    @validator("status")
    def validate_status(cls, v):
        if v is None:
            return v
        allowed = ["active", "discontinued", "draft"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v


class MovementCreate(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID")
    movement_type: str = Field(..., description="Movement type: in, out, adjustment, transfer")
    quantity: int = Field(..., ge=0, description="Movement quantity")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")
    reference: Optional[str] = Field(None, max_length=255, description="Reference number")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes")

    @validator("movement_type")
    def validate_movement_type(cls, v):
        allowed = ["in", "out", "adjustment", "transfer"]
        if v not in allowed:
            raise ValueError(f"Movement type must be one of: {allowed}")
        return v


class MovementResponse(BaseModel):
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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    total_products: int
    total_stock_value: float
    low_stock_count: int
    out_of_stock: int
    categories: List[dict]


def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(db)


def _rollback_and_raise(db: Session, exc: Exception):
    db.rollback()
    if isinstance(exc, HTTPException):
        raise exc
    raise HTTPException(status_code=400, detail=str(exc))


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    try:
        product = service.create_product(
            sku=data.sku, name=data.name, unit_price=data.unit_price,
            description=data.description, category=data.category, cost_price=data.cost_price,
            quantity_in_stock=data.quantity_in_stock, reorder_level=data.reorder_level,
            reorder_quantity=data.reorder_quantity, supplier=data.supplier,
            supplier_contact=data.supplier_contact, status=data.status, barcode=data.barcode,
            weight=data.weight, dimensions=data.dimensions, created_by=current_user.id,
            commit=False,
        )
        log_activity(db, user_id=current_user.id, action="product_created", entity_type="product", entity_id=product.id, commit=False)
        db.commit()
        return product
    except ValueError as e:
        return _rollback_and_raise(db, e)
    except Exception:
        db.rollback()
        raise


@router.get("/products", response_model=List[ProductResponse])
def list_products(category: Optional[str] = None, status: Optional[str] = None, low_stock: bool = False, search: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    return service.list_products(category=category, status=status, low_stock=low_stock, search=search, skip=skip, limit=limit)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        product = service.update_product(product_id=product_id, updates=updates, updated_by=current_user.id, commit=False)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        log_activity(db, user_id=current_user.id, action="product_updated", entity_type="product", entity_id=product.id, commit=False)
        db.commit()
        return product
    except ValueError as e:
        return _rollback_and_raise(db, e)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    try:
        success = service.delete_product(product_id, commit=False)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        log_activity(db, user_id=current_user.id, action="product_deleted", entity_type="product", entity_id=product_id, commit=False)
        db.commit()
        return {"message": "Product deleted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.post("/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(data: MovementCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    try:
        movement = service.create_stock_movement(
            product_id=data.product_id, movement_type=data.movement_type, quantity=data.quantity,
            unit_cost=data.unit_cost, reference=data.reference, notes=data.notes,
            created_by=current_user.id, commit=False,
        )
        log_activity(db, user_id=current_user.id, action="inventory_moved", entity_type="inventory_movement", entity_id=movement.id, commit=False)
        db.commit()
        return movement
    except ValueError as e:
        return _rollback_and_raise(db, e)
    except Exception:
        db.rollback()
        raise


@router.get("/movements", response_model=List[MovementResponse])
def list_movements(product_id: Optional[int] = None, movement_type: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    return service.get_movements(product_id=product_id, movement_type=movement_type, skip=skip, limit=limit)


@router.get("/dashboard", response_model=DashboardResponse)
def inventory_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    return service.get_dashboard_stats()


@router.get("/alerts/low-stock", response_model=List[ProductResponse])
def get_low_stock_alerts(limit: int = 50, db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    return service.get_low_stock_products(limit=limit)


@router.get("/alerts/out-of-stock", response_model=List[ProductResponse])
def get_out_of_stock_alerts(db: Session = Depends(get_db), current_user=Depends(get_current_user), service: InventoryService = Depends(get_inventory_service)):
    return service.get_out_of_stock_products()
