"""Core module initialization - exports repository pattern and exceptions."""

from app.core.repository import RepositoryBase
from app.core.repositories import (
    UserRepository,
    ProductRepository,
    InventoryMovementRepository,
    CustomerRepository,
    SupplierRepository,
    SalesOrderRepository,
    PurchaseOrderRepository,
    InvoiceRepository,
    PaymentRepository,
    ProjectRepository,
    TaskRepository,
    DocumentRepository,
    WorkflowRepository,
    ActivityLogRepository,
    get_repository,
)
from app.core.exceptions import (
    ErrorResponse,
    AppException,
    NotFoundException,
    ValidationException,
    ConflictException,
    UnauthorizedException,
    ForbiddenException,
    DatabaseException,
    TransactionRollbackException,
)

__all__ = [
    # Repository Pattern
    "RepositoryBase",
    "UserRepository",
    "ProductRepository",
    "InventoryMovementRepository",
    "CustomerRepository",
    "SupplierRepository",
    "SalesOrderRepository",
    "PurchaseOrderRepository",
    "InvoiceRepository",
    "PaymentRepository",
    "ProjectRepository",
    "TaskRepository",
    "DocumentRepository",
    "WorkflowRepository",
    "ActivityLogRepository",
    "get_repository",
    # Exceptions
    "ErrorResponse",
    "AppException",
    "NotFoundException",
    "ValidationException",
    "ConflictException",
    "UnauthorizedException",
    "ForbiddenException",
    "DatabaseException",
    "TransactionRollbackException",
]
