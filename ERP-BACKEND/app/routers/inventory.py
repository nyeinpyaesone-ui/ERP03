from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models import Product, InventoryMovement
from app.auth import get_current_user
from app.services.activity_log import log_activity

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

class MovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: int
    unit_cost: Optional[float] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

@router.post("/products")
def create_product(data: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    existing = db.query(Product).filter(Product.sku == data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    product = Product(**data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    log_activity(db, user_id=current_user.id, action="product_created", entity_type="product", entity_id=product.id)
    return product

@router.get("/products")
def list_products(
    category: Optional[str] = None,
    status: Optional[str] = None,
    low_stock: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if status:
        query = query.filter(Product.status == status)
    if low_stock:
        query = query.filter(Product.quantity_in_stock <= Product.reorder_level)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.all()

@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}")
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.dict().items():
        setattr(product, key, value)
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

@router.post("/movements")
def create_movement(data: MovementCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    movement = InventoryMovement(**data.dict(), created_by=current_user.id)

    # Update stock
    if data.movement_type == "in":
        product.quantity_in_stock += data.quantity
    elif data.movement_type == "out":
        if product.quantity_in_stock < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.quantity_in_stock -= data.quantity
    elif data.movement_type == "adjustment":
        product.quantity_in_stock = data.quantity

    product.updated_at = datetime.utcnow()
    db.add(movement)
    db.commit()
    db.refresh(movement)
    log_activity(db, user_id=current_user.id, action="inventory_moved", entity_type="inventory_movement", entity_id=movement.id)
    return movement

@router.get("/movements")
def list_movements(product_id: Optional[int] = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    query = db.query(InventoryMovement)
    if product_id:
        query = query.filter(InventoryMovement.product_id == product_id)
    return query.order_by(InventoryMovement.created_at.desc()).all()

@router.get("/dashboard")
def inventory_dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from sqlalchemy import func
    total_products = db.query(Product).count()
    total_stock_value = db.query(func.sum(Product.quantity_in_stock * Product.unit_price)).scalar() or 0
    low_stock_count = db.query(Product).filter(Product.quantity_in_stock <= Product.reorder_level).count()
    out_of_stock = db.query(Product).filter(Product.quantity_in_stock == 0).count()

    return {
        "total_products": total_products,
        "total_stock_value": float(total_stock_value),
        "low_stock_count": low_stock_count,
        "out_of_stock": out_of_stock,
        "categories": db.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    }

