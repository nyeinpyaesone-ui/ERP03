"""Typed application errors with stable, machine-readable codes.

Domain services raise these; the API layer maps them to HTTP responses in a
single exception handler, so routers never translate error strings by hand.
"""


class AppError(Exception):
    """Base class for expected business-rule failures.

    ``status_code`` carries the HTTP status the API layer should return and
    ``code`` is a stable identifier safe to expose to clients.
    """

    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """A request violated a business invariant."""

    status_code = 400
    code = "VALIDATION_ERROR"


class ConflictError(AppError):
    """The request conflicts with existing durable state."""

    status_code = 409
    code = "CONFLICT"


class InsufficientStockError(ValidationError):
    """A stock deduction would drive inventory negative."""

    code = "INSUFFICIENT_STOCK"


class SaleValidationError(ValidationError):
    """A POS sale violated a business invariant."""

    code = "SALE_VALIDATION_ERROR"


class BootstrapConflictError(ConflictError):
    """Bootstrap would mutate an existing tenant unexpectedly."""

    code = "BOOTSTRAP_CONFLICT"


class NotFoundError(AppError):
    """The requested resource does not exist in this tenant scope."""

    status_code = 404
    code = "NOT_FOUND"


class ForbiddenError(AppError):
    """The caller is authenticated but not permitted to perform this action."""

    status_code = 403
    code = "FORBIDDEN"
