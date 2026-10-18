"""POS sale creation endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validation import validate_idempotency_key
from app.core.authorization import permission_dependency
from app.db.session import get_db_session
from app.schemas.sales import CreateSaleRequest, SaleResultResponse
from app.services.sales import SaleLine, SalePayment, create_pos_sale

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleResultResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    payload: CreateSaleRequest,
    claims: dict = Depends(permission_dependency("sales.create")),
    session: AsyncSession = Depends(get_db_session),
    x_idempotency_key: str | None = Header(default=None),
) -> SaleResultResponse:
    business_id = UUID(claims["business_id"])
    claim_branch = claims.get("branch_id")
    if claim_branch and claim_branch != str(payload.branch_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Branch access denied",
        )

    idempotency_key = validate_idempotency_key(x_idempotency_key)

    # Domain failures (SaleValidationError / ConflictError) propagate to the
    # central AppError handler in app.main, which maps them to the stable
    # error envelope with the correct HTTP status.
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
        idempotency_key=f"{business_id}:{idempotency_key}",
    )
    return SaleResultResponse(
        invoice_id=str(result.invoice_id),
        total=str(result.total),
        paid=str(result.paid),
        balance=str(result.balance),
    )
