from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from app.database import get_db

router = APIRouter()

class InventoryItem(BaseModel):
    sku: str
    name: str
    quantity: int
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v

class InventoryResponse(BaseModel):
    id: int
    sku: str
    name: str
    quantity: int

@router.get("/", response_model=list[InventoryResponse])
async def list_inventory(db: AsyncSession = Depends(get_db)):
    return []

@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: InventoryItem, db: AsyncSession = Depends(get_db)):
    return InventoryResponse(id=1, sku=item.sku, name=item.name, quantity=item.quantity)

@router.put("/{item_id}", response_model=InventoryResponse)
async def update_item(item_id: int, item: InventoryItem, db: AsyncSession = Depends(get_db)):
    # In production: Use SELECT FOR UPDATE NOWAIT for concurrency control
    return InventoryResponse(id=item_id, sku=item.sku, name=item.name, quantity=item.quantity)
