"""Shared request-level validation helpers for API routers."""

from fastapi import HTTPException, status

MAX_IDEMPOTENCY_KEY_LENGTH = 255


def validate_idempotency_key(key: str | None) -> str:
    """Return a usable idempotency key or raise HTTP 400.

    Idempotent writes must carry a bounded, non-blank key; otherwise retries
    could create duplicates or exhaust storage with oversized values.
    """
    if key is None or not key.strip() or len(key) > MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"X-Idempotency-Key is required and must be "
                f"<= {MAX_IDEMPOTENCY_KEY_LENGTH} characters"
            ),
        )
    return key
