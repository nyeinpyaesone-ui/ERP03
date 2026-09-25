from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.core.transaction_store import TransactionStore

router = APIRouter(prefix="/transactions", tags=["transactions"])
store = TransactionStore(settings.database_path)


class TransactionRequest(BaseModel):
    operation: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    metadata: dict = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    operation: str
    amount: str
    currency: str
    metadata: dict
    idempotent_replay: bool


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionRequest,
    x_idempotency_key: str | None = Header(default=None),
) -> TransactionResponse:
    if not x_idempotency_key or len(x_idempotency_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Idempotency-Key is required and must be <= 255 characters",
        )

    try:
        amount = payload.amount.quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=422, detail="Invalid amount") from exc

    result = store.execute(
        transaction_id=uuid4().hex,
        idempotency_key=x_idempotency_key,
        operation=payload.operation,
        amount=str(amount),
        currency=payload.currency,
        metadata=payload.metadata,
    )
    return TransactionResponse(
        transaction_id=result.transaction_id,
        status=result.status,
        operation=result.operation,
        amount=result.amount,
        currency=result.currency,
        metadata=result.metadata,
        idempotent_replay=result.idempotent_replay,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str) -> TransactionResponse:
    result = store.get(transaction_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse(
        transaction_id=result.transaction_id,
        status=result.status,
        operation=result.operation,
        amount=result.amount,
        currency=result.currency,
        metadata=result.metadata,
        idempotent_replay=False,
    )
