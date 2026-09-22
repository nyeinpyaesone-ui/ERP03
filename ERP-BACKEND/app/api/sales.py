from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_claims
from app.db.session import get_db_session
from app.services.sales import SaleLine, SalePayment, SaleValidationError, create_pos_sale

router = APIRouter(prefix="/sales", tags=["sales"])


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
    invoice_no: str = Field(min_length=1, max_length=64)
    customer_id: UUID | None = None
    currency: str = Field(default="MMK", min_length=3, max_length=3)
    lines: list[SaleLineRequest] = Field(min_length=1, max_length=200)
    payments: list[SalePaymentRequest] = Field(default_factory=list, max_length=20)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sale(
    payload: CreateSaleRequest,
    claims: dict = Depends(current_claims),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        business_id = UUID(claims["business_id"])
        result = await create_pos_sale(
            session,
            business_id=business_id,
            branch_id=payload.branch_id,
            warehouse_id=payload.warehouse_id,
            invoice_no=payload.invoice_no,
            customer_id=payload.customer_id,
            currency=payload.currency.upper(),
            lines=[SaleLine(**line.model_dump()) for line in payload.lines],
            payments=[SalePayment(**payment.model_dump()) for payment in payload.payments],
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "invoice_id": str(result.invoice_id),
        "total": str(result.total),
        "paid": str(result.paid),
        "balance": str(result.balance),
    }
