"""Authenticated transaction journal endpoints."""

import threading
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validation import validate_idempotency_key
from app.core.config import settings
from app.core.postgres_transaction_store import PostgresTransactionStore
from app.core.security import current_claims
from app.core.transaction_store import IdempotencyConflict, TransactionResult, TransactionStore
from app.db.session import get_db_session

router = APIRouter(prefix="/transactions", tags=["transactions"])

_store: TransactionStore | None = None
_store_lock = threading.Lock()


def _requires_shared_journal() -> bool:
    """Staging and production must use the shared database journal."""
    return settings.environment.lower() in {"staging", "stage", "production", "prod"}


def _uses_postgres_journal() -> bool:
    """Return whether the configured async database is PostgreSQL."""
    return settings.database_url.lower().startswith("postgresql")


def get_store() -> TransactionStore:
    """Return the local SQLite journal; never expose it in shared environments."""
    if _requires_shared_journal():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "TRANSACTION_JOURNAL_UNAVAILABLE",
                "message": (
                    "Staging and production require the shared PostgreSQL "
                    "transaction journal; local SQLite is disabled."
                ),
            },
        )

    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = TransactionStore(settings.database_path)
    return _store


def reset_store(database_path: str | None = None) -> TransactionStore:
    """Replace the process-wide local store (used by tests for isolation)."""
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


def _business_id(claims: dict[str, Any]) -> str:
    """Read tenant identity only from the verified access token."""
    value = claims.get("business_id")
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization claims",
        )
    return value.strip()


def _raise_idempotency_conflict(exc: IdempotencyConflict) -> None:
    code = getattr(exc, "code", "IDEMPOTENCY_KEY_REUSED")
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": code, "message": str(exc)},
    ) from exc


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionRequest,
    claims: dict[str, Any] = Depends(current_claims),
    x_idempotency_key: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> TransactionResponse:
    """Accept a journal entry or replay it; this does not execute the domain operation."""
    idempotency_key = validate_idempotency_key(x_idempotency_key)

    try:
        amount = payload.amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="Invalid amount") from exc
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be at least 0.01")

    business_id = _business_id(claims)
    transaction_id = uuid4().hex
    try:
        if _requires_shared_journal():
            if not _uses_postgres_journal():
                get_store()  # Raises 503; never fall back to local SQLite.
            result = await PostgresTransactionStore(session).execute(
                transaction_id=transaction_id,
                business_id=business_id,
                idempotency_key=idempotency_key,
                operation=payload.operation,
                amount=str(amount),
                currency=payload.currency,
                metadata=payload.metadata,
            )
            await session.commit()
        else:
            result = get_store().execute(
                transaction_id=transaction_id,
                idempotency_key=f"{business_id}:{idempotency_key}",
                business_id=business_id,
                operation=payload.operation,
                amount=str(amount),
                currency=payload.currency,
                metadata=payload.metadata,
            )
    except IdempotencyConflict as exc:
        if _requires_shared_journal():
            await session.rollback()
        _raise_idempotency_conflict(exc)

    return _to_response(result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    claims: dict[str, Any] = Depends(current_claims),
    session: AsyncSession = Depends(get_db_session),
) -> TransactionResponse:
    """Return a journal entry owned by the authenticated caller's business."""
    business_id = _business_id(claims)
    if _requires_shared_journal():
        if not _uses_postgres_journal():
            get_store()
        result = await PostgresTransactionStore(session).get(
            transaction_id,
            business_id=business_id,
        )
    else:
        result = get_store().get(transaction_id, business_id=business_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(result)
