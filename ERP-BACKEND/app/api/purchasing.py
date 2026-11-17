"""Idempotent purchase receiving endpoint with atomic inventory commit."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.api.validation import validate_idempotency_key
from app.core.authorization import permission_dependency
from app.core.errors import ConflictError
from app.db.session import get_db_session
from app.models.operations import OperationState
from app.schemas.catalog import ReceivePurchaseRequest, ReceivePurchaseResponse
from app.services.orchestration import OperationService
from app.services.receiving import receive_purchase_lines

router = APIRouter(prefix="/purchases", tags=["purchasing"])


@router.post("/receipts", response_model=ReceivePurchaseResponse, status_code=201)
async def receive_purchase(
    payload: ReceivePurchaseRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    x_idempotency_key: str | None = Header(default=None),
    _auth: dict = Depends(permission_dependency("purchases.receive")),
) -> ReceivePurchaseResponse:
    """Receive stock exactly once per tenant-scoped idempotency key.

    The inventory movements, weighted-average product costs and operation
    COMMITTED transition are persisted in one PostgreSQL transaction.
    """
    business_id = UUID(claims["business_id"])
    claim_branch = claims.get("branch_id")
    if claim_branch and str(claim_branch) != str(payload.branch_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Branch access denied",
        )

    idempotency_key = validate_idempotency_key(x_idempotency_key)
    operation_id = f"{business_id}:{idempotency_key}"
    command = {
        "warehouse_id": str(payload.warehouse_id),
        "lines": [
            {
                "product_id": str(line.product_id),
                "quantity": str(line.quantity),
                "unit_cost": str(line.unit_cost),
            }
            for line in payload.lines
        ],
    }

    try:
        async with session.begin():
            service = OperationService(
                session,
                worker_id=f"purchase-receipt-{uuid4().hex}",
            )
            operation, _replayed = await service.create_operation_with_replay(
                operation_id=operation_id,
                operation_type="purchase.receipt",
                business_id=business_id,
                branch_id=payload.branch_id,
                payload=command,
            )

            if operation.state == OperationState.COMMITTED:
                result = operation.result_json or {}
                if "total_value" not in result or "lines_received" not in result:
                    raise ConflictError(
                        "Committed purchase receipt has no stored result; "
                        "manual reconciliation is required"
                    )
                return ReceivePurchaseResponse(
                    total_value=str(result["total_value"]),
                    lines_received=int(result["lines_received"]),
                )

            claimed = await service.claim_operation(operation_id)
            if claimed is None:
                raise ConflictError(
                    "Purchase receipt is already processing, not yet retryable, "
                    "or requires manual reconciliation"
                )

            total_value = await receive_purchase_lines(
                session,
                business_id=business_id,
                branch_id=payload.branch_id,
                warehouse_id=payload.warehouse_id,
                lines=[
                    (line.product_id, line.quantity, line.unit_cost)
                    for line in payload.lines
                ],
            )
            await service.commit_operation(
                claimed,
                result={
                    "total_value": str(total_value),
                    "lines_received": len(payload.lines),
                    "currency": "MMK",
                },
            )
        return ReceivePurchaseResponse(
            total_value=str(total_value),
            lines_received=len(payload.lines),
        )
