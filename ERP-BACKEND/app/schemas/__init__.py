"""Pydantic request/response schemas shared across API routers."""

from app.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse
from app.schemas.sales import (
    CreateSaleRequest,
    SaleLineRequest,
    SalePaymentRequest,
    SaleResultResponse,
)
from app.schemas.transactions import TransactionRequest, TransactionResponse

__all__ = [
    "AuthenticatedUser",
    "CreateSaleRequest",
    "LoginRequest",
    "LoginResponse",
    "SaleLineRequest",
    "SalePaymentRequest",
    "SaleResultResponse",
    "TransactionRequest",
    "TransactionResponse",
]
