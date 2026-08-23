"""
Inventory schemas for ERP03 Integration Contracts.

These schemas define the contract for inventory operations between ERP-BACKEND and AI-BACKEND.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProductSchema(BaseModel):
    """Product entity schema."""
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: float = Field(..., ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    quantity_on_hand: int = Field(default=0, ge=0)
    quantity_reserved: int = Field(default=0, ge=0)
    quantity_available: int = Field(default=0, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    unit_of_measure: str = Field(default="unit")
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class ProductCreateSchema(BaseModel):
    """Schema for creating a product."""
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: float = Field(..., ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    unit_of_measure: str = Field(default="unit")
    tags: List[str] = Field(default_factory=list)


class ProductUpdateSchema(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    unit_of_measure: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


# ============================================================================
# Category Schemas
# ============================================================================

class CategorySchema(BaseModel):
    """Product category schema."""
    id: int
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    product_count: int = Field(default=0)


class CategoryCreateSchema(BaseModel):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[int] = None
    description: Optional[str] = None


# ============================================================================
# Stock Movement Schemas
# ============================================================================

class StockMovementType(str):
    """Types of stock movements."""
    RECEIPT = "receipt"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    WRITE_OFF = "write_off"


class StockMovementSchema(BaseModel):
    """Stock movement entity schema."""
    id: int
    product_id: int
    movement_type: str
    quantity: int
    reference_type: Optional[str] = None  # e.g., 'sale_order', 'purchase_order'
    reference_id: Optional[int] = None
    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None
    notes: Optional[str] = None
    performed_by: Optional[int] = None
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StockMovementCreateSchema(BaseModel):
    """Schema for creating a stock movement."""
    product_id: int
    movement_type: str
    quantity: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Location/Warehouse Schemas
# ============================================================================

class LocationSchema(BaseModel):
    """Warehouse/location schema."""
    id: int
    code: str
    name: str
    type: str = Field(..., description="warehouse/bin/zone")
    parent_id: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True
    capacity: Optional[int] = Field(None, ge=0)
    created_at: datetime
    updated_at: Optional[datetime] = None


class LocationCreateSchema(BaseModel):
    """Schema for creating a location."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(...)
    parent_id: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)


# ============================================================================
# Stock Level Schemas
# ============================================================================

class StockLevelSchema(BaseModel):
    """Current stock level for a product at a location."""
    product_id: int
    product_sku: str
    product_name: str
    location_id: int
    location_code: str
    quantity_on_hand: int = Field(..., ge=0)
    quantity_reserved: int = Field(default=0, ge=0)
    quantity_available: int = Field(..., ge=0)
    last_counted_at: Optional[datetime] = None
    last_movement_at: Optional[datetime] = None


# ============================================================================
# Stock Adjustment Schemas
# ============================================================================

class StockAdjustmentSchema(BaseModel):
    """Stock adjustment record."""
    id: int
    product_id: int
    location_id: int
    quantity_before: int
    quantity_after: int
    quantity_adjusted: int
    reason: str
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    adjusted_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: datetime


class StockAdjustmentCreateSchema(BaseModel):
    """Schema for creating a stock adjustment."""
    product_id: int
    location_id: int
    quantity_adjusted: int
    reason: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None
    reference_number: Optional[str] = None
