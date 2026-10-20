"""Typed application errors with stable, machine-readable codes."""


class AppError(Exception):
    """Base class for expected business-rule failures."""

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


class PaymentError(ValidationError):
    """A payment record violated a business invariant."""

    code = "PAYMENT_ERROR"


# Error code registry for fast lookup without string matching.
_ERROR_CODES: dict[str, type[AppError]] = {
    cls.code: cls for cls in AppError.__subclasses__() for cls in (cls, *cls.__subclasses__())
}


def error_from_code(code: str, message: str) -> AppError:
    """Build the typed error from a stable code, O(1) lookup."""
    cls = _ERROR_CODES.get(code, AppError)
    return cls(message)


__all__ = [
    "AppError",
    "ValidationError",
    "ConflictError",
    "InsufficientStockError",
    "SaleValidationError",
    "BootstrapConflictError",
    "NotFoundError",
    "ForbiddenError",
    "PaymentError",
    "error_from_code",
]
