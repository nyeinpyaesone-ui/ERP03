"""Master-data and purchasing request/response contracts."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreateRequest(BaseModel):
    branch_id: UUID
    sku: str = Field(min_length=1, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=240)
    unit: str = Field(default="pcs", min_length=1, max_length=32)
    sale_price: Decimal = Field(ge=0)
    cost_price: Decimal = Field(default=Decimal("0"), ge=0)
    min_stock: Decimal = Field(default=Decimal("0"), ge=0)


class CustomerCreateRequest(BaseModel):
    branch_id: UUID
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)


class SupplierCreateRequest(BaseModel):
    branch_id: UUID
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)


class ActiveFlagRequest(BaseModel):
    active: bool


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    branch_id: UUID
    sku: str
    barcode: str | None
    name: str
    unit: str
    sale_price: Decimal
    cost_price: Decimal
    min_stock: Decimal
    active: bool


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    branch_id: UUID
    code: str
    name: str
    phone: str | None
    credit_limit: Decimal
    active: bool


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    branch_id: UUID
    code: str
    name: str
    phone: str | None
    payable_balance: Decimal
    active: bool


class PageResponse(BaseModel):
    items: list[dict]
    limit: int
    offset: int
    total: int
    has_more: bool


class ReceiveLine(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class ReceivePurchaseRequest(BaseModel):
    branch_id: UUID
    warehouse_id: UUID
    lines: list[ReceiveLine] = Field(min_length=1, max_length=200)


class ReceivePurchaseResponse(BaseModel):
    total_value: str
    lines_received: int
