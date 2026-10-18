"""Pydantic request/response schemas shared across API routers."""

from app.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse
from app.schemas.catalog import (
    CustomerCreateRequest,
    CustomerResponse,
    PageResponse,
    ProductCreateRequest,
    ProductResponse,
    ReceivePurchaseRequest,
    ReceivePurchaseResponse,
    SupplierCreateRequest,
    SupplierResponse,
)
from app.schemas.sales import (
    CreateSaleRequest,
    SaleLineRequest,
    SalePaymentRequest,
    SaleResultResponse,
)
from app.schemas.transactions import TransactionRequest, TransactionResponse

__all__ = [
    "AuthenticatedUser",
    "CustomerCreateRequest",
    "CustomerResponse",
    "PageResponse",
    "ProductCreateRequest",
    "ProductResponse",
    "ReceivePurchaseRequest",
    "ReceivePurchaseResponse",
    "SupplierCreateRequest",
    "SupplierResponse",
    "CreateSaleRequest",
    "LoginRequest",
    "LoginResponse",
    "SaleLineRequest",
    "SalePaymentRequest",
    "SaleResultResponse",
    "TransactionRequest",
    "TransactionResponse",
]
