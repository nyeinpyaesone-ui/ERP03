"""POS sale request/response contracts."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SaleLineRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)


class SalePaymentRequest(BaseModel):
    method: str = Field(min_length=1, max_length=32)
    amount: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=120)
    currency: str = Field(default="MMK", min_length=3, max_length=3)


class CreateSaleRequest(BaseModel):
    branch_id: UUID
    warehouse_id: UUID
    invoice_no: str | None = Field(default=None, min_length=1, max_length=64)
    customer_id: UUID | None = None
    currency: str = Field(default="MMK", min_length=3, max_length=3)
    lines: list[SaleLineRequest] = Field(min_length=1, max_length=200)
    payments: list[SalePaymentRequest] = Field(default_factory=list, max_length=20)


class SaleResultResponse(BaseModel):
    invoice_id: str
    total: str
    paid: str
    balance: str
