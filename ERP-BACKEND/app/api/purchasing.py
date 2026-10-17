"""Purchase receiving endpoint: stock-in with weighted-average costing."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.authorization import permission_dependency
from app.db.session import get_db_session
from app.schemas.catalog import ReceivePurchaseRequest, ReceivePurchaseResponse
from app.services.receiving import receive_purchase_lines

router = APIRouter(prefix="/purchases", tags=["purchasing"])


@router.post("/receipts", response_model=ReceivePurchaseResponse, status_code=201)
async def receive_purchase(
    payload: ReceivePurchaseRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    _auth: dict = Depends(permission_dependency("purchases.receive")),
) -> ReceivePurchaseResponse:
    total_value = await receive_purchase_lines(
        session,
        business_id=UUID(claims["business_id"]),
        branch_id=payload.branch_id,
        warehouse_id=payload.warehouse_id,
        lines=[(line.product_id, line.quantity, line.unit_cost) for line in payload.lines],
    )
    return ReceivePurchaseResponse(total_value=str(total_value), lines_received=len(payload.lines))
