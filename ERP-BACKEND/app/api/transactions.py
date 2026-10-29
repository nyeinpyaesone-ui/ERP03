"""Authenticated transaction journal endpoints."""

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.api.validation import validate_idempotency_key
from app.core.config import settings
from app.core.security import current_claims
from app.core.transaction_store import IdempotencyConflict, TransactionResult, TransactionStore

router = APIRouter(prefix="/transactions", tags=["transactions"])

_store: TransactionStore | None = None


def get_store() -> TransactionStore:
    """Return the process-wide transaction journal (lazy, resettable for tests)."""
    global _store
    if _store is None:
        _store = TransactionStore(settings.database_path)
    return _store


def reset_store(database_path: str | None = None) -> TransactionStore:
    """Replace the process-wide store (used by tests for hermetic isolation)."""
    global _store
    _store = TransactionStore(database_path or settings.database_path)
    return _store


class TransactionRequest(BaseModel):
    operation: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("operation")
    @classmethod
    def normalize_operation(cls, value: str) -> str:
        operation = value.strip()
        if not operation:
            raise ValueError("operation must not be blank")
        return operation

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    operation: str
    amount: str
    currency: str
    metadata: dict[str, Any]
    idempotent_replay: bool


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


def _business_id(claims: dict[str, Any]) -> str:
    """Read tenant identity only from the verified access token."""
    value = claims.get("business_id")
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization claims",
        )
    return value.strip()


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionRequest,
    claims: dict[str, Any] = Depends(current_claims),
    x_idempotency_key: str | None = Header(default=None),
) -> TransactionResponse:
    """Record a journal entry or return the original entry for a repeated key."""
    idempotency_key = validate_idempotency_key(x_idempotency_key)

    try:
        amount = payload.amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="Invalid amount") from exc
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be at least 0.01")

    business_id = _business_id(claims)
    try:
        result = get_store().execute(
            transaction_id=uuid4().hex,
            idempotency_key=f"{business_id}:{idempotency_key}",
            business_id=business_id,
            operation=payload.operation,
            amount=str(amount),
            currency=payload.currency,
            metadata=payload.metadata,
        )
    except IdempotencyConflict as exc:
        code = getattr(exc, "code", "IDEMPOTENCY_KEY_REUSED")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": code, "message": str(exc)},
        ) from exc
    return _to_response(result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    claims: dict[str, Any] = Depends(current_claims),
) -> TransactionResponse:
    """Return a journal entry owned by the authenticated caller's business."""
    business_id = _business_id(claims)
    result = get_store().get(transaction_id, business_id=business_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(result)
