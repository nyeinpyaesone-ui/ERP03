"""Authenticated transaction journal endpoints.

Every write is idempotent: a reused ``X-Idempotency-Key`` (scoped to the
caller's business) replays the original entry instead of recording a new one.
Reads are scoped to the caller's business as well.
"""

from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, status

from app.api.dependencies import Claims
from app.api.validation import validate_idempotency_key
from app.core.config import settings
from app.core.transaction_store import TransactionResult, TransactionStore
from app.schemas.transactions import TransactionRequest, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])
store = TransactionStore(settings.database_path)


def _to_response(result: TransactionResult) -> TransactionResponse:
    return TransactionResponse(
        transaction_id=result.transaction_id,
        status=result.status,
        operation=result.operation,
        amount=result.amount,
        currency=result.currency,
        metadata=result.metadata,
        idempotent_replay=result.idempotent_replay,
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionRequest,
    claims: Claims,
    x_idempotency_key: str | None = Header(default=None),
) -> TransactionResponse:
    """Record a transaction or return the original for a reused idempotency key.

    Round the amount to two decimal places using the current decimal context
    before looking up the key; even a positive amount can round to zero.
    Replays return the original fields with ``idempotent_replay=True``, even
    when the submitted fields differ. Both new records and replays use HTTP 201.
    """
    idempotency_key = validate_idempotency_key(x_idempotency_key)

    try:
        amount = payload.amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="Invalid amount") from exc

    result = store.execute(
        transaction_id=uuid4().hex,
        business_id=claims["business_id"],
        idempotency_key=idempotency_key,
        operation=payload.operation,
        amount=str(amount),
        currency=payload.currency,
        metadata=payload.metadata,
    )
    return _to_response(result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, claims: Claims) -> TransactionResponse:
    """Return a stored journal entry belonging to the caller's business.

    Foreign or unknown identifiers return 404 so existence is never leaked
    across tenants.
    """
    result = store.get(transaction_id, business_id=claims["business_id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(result)
