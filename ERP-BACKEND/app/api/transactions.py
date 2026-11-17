"""Authenticated transaction intake backed by PostgreSQL in shared environments.

SQLite remains a local-development adapter only. PostgreSQL requests use the
existing operations table so idempotency and operation state are shared across
all API replicas.
"""

import asyncio
import threading
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validation import validate_idempotency_key
from app.core.config import settings
from app.core.errors import ConflictError
from app.core.security import current_claims
from app.core.transaction_store import IdempotencyConflict, TransactionResult, TransactionStore
from app.db.session import get_db_session
from app.models.operations import Operation, OperationState
from app.services.orchestration import OperationService

router = APIRouter(prefix="/transactions", tags=["transactions"])

_store: TransactionStore | None = None
_store_lock = threading.Lock()

_OPERATION_STATUS = {
    OperationState.PENDING: "accepted",
    OperationState.PROCESSING: "processing",
    OperationState.COMMITTED: "committed",
    OperationState.FAILED: "retryable",
    OperationState.RECONCILIATION_REQUIRED: "reconciliation_required",
    OperationState.CANCELLED: "cancelled",
}


def _uses_shared_journal() -> bool:
    """Use PostgreSQL operations for shared environments, SQLite for local dev."""
    return settings.database_url.lower().startswith(("postgresql://", "postgresql+"))


def get_store() -> TransactionStore:
    """Return the local SQLite adapter (never used for PostgreSQL requests)."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = TransactionStore(settings.database_path)
    return _store


def reset_store(database_path: str | None = None) -> TransactionStore:
    """Replace the local SQLite adapter (used by isolated tests)."""
    global _store
    with _store_lock:
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


def _to_operation_response(
    operation: Operation,
    *,
    replay: bool = False,
) -> TransactionResponse:
    payload = operation.payload_json
    return TransactionResponse(
        transaction_id=operation.id.hex,
        status=_OPERATION_STATUS[operation.state],
        operation=operation.operation_type,
        amount=str(payload["amount"]),
        currency=str(payload["currency"]),
        metadata=payload.get("metadata") or {},
        idempotent_replay=replay,
    )


def _business_id(claims: dict[str, Any]) -> str:
    """Read tenant identity only from verified access-token claims."""
    value = claims.get("business_id")
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization claims",
        )
    return value.strip()


def _as_business_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization claims",
        ) from exc


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionRequest,
    claims: dict[str, Any] = Depends(current_claims),
    x_idempotency_key: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> TransactionResponse:
    """Accept an operation or replay the same tenant-scoped command.

    This endpoint accepts work; it does not execute the named domain operation.
    A committed state is written only by a domain handler in the same database
    transaction as its authoritative business mutations.
    """
    idempotency_key = validate_idempotency_key(x_idempotency_key)
    try:
        amount = payload.amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="Invalid amount") from exc
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be at least 0.01")

    business_id = _business_id(claims)
    if _uses_shared_journal():
        business_uuid = _as_business_uuid(business_id)
        branch_id = claims.get("branch_id")
        try:
            branch_uuid = UUID(str(branch_id)) if branch_id else None
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization claims",
            ) from exc

        operation_id = f"{business_uuid}:{idempotency_key}"
        command = {
            "amount": str(amount),
            "currency": payload.currency,
            "metadata": payload.metadata,
        }
        try:
            async with session.begin():
                operation, replay = await OperationService(
                    session
                ).create_operation_with_replay(
                    operation_id=operation_id,
                    operation_type=payload.operation,
                    business_id=business_uuid,
                    branch_id=branch_uuid,
                    payload=command,
                )
        except ConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "IDEMPOTENCY_PAYLOAD_MISMATCH",
                    "message": str(exc),
                },
            ) from exc
        return _to_operation_response(operation, replay=replay)

    # SQLite is deliberately retained only for local/dev and isolated tests.
    result = await asyncio.to_thread(
        get_store().execute,
        transaction_id=uuid4().hex,
        idempotency_key=f"{business_id}:{idempotency_key}",
        business_id=business_id,
        operation=payload.operation,
        amount=str(amount),
        currency=payload.currency,
        metadata=payload.metadata,
    )
    return _to_response(result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    claims: dict[str, Any] = Depends(current_claims),
    session: AsyncSession = Depends(get_db_session),
) -> TransactionResponse:
    """Return an operation owned by the authenticated business."""
    business_id = _business_id(claims)
    if _uses_shared_journal():
        business_uuid = _as_business_uuid(business_id)
        try:
            operation_uuid = UUID(transaction_id)
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(status_code=404, detail="Transaction not found") from None

        result = await session.execute(
            select(Operation).where(
                Operation.id == operation_uuid,
                Operation.business_id == business_uuid,
            )
        )
        operation = result.scalar_one_or_none()
        if operation is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return _to_operation_response(operation)

    result = await asyncio.to_thread(
        get_store().get,
        transaction_id,
        business_id=business_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(result)
