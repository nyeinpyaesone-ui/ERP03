"""Transaction journal request/response contracts."""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class TransactionRequest(BaseModel):
    operation: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    metadata: dict = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Uppercase the currency without checking whether it is a known code."""
        return value.upper()


class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    operation: str
    amount: str
    currency: str
    metadata: dict
    idempotent_replay: bool
