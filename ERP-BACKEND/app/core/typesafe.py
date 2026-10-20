"""TypeSafe System One integration for ERP03.

Provides error classification, transaction risk scoring, and idempotency
conflict judgment. All calls degrade gracefully when the SDK is unavailable
or disabled. Code owns the workflow; TypeSafe supplies programmable common
sense where ordinary code needs semantic understanding.
"""

from __future__ import annotations

from typing import Any

try:
    from typesafe import AsyncTypeSafeClient, choice, noul, score

    _TYPESAFE_AVAILABLE = True
except ImportError:  # pragma: no cover - TypeSafe is optional
    AsyncTypeSafeClient = None  # type: ignore[assignment]
    choice = noul = score = None  # type: ignore[assignment]
    _TYPESAFE_AVAILABLE = False

from app.core.config import settings


class TypeSafeClient:
    """System One client wrapper with ERP03-specific judgments."""

    def __init__(self) -> None:
        self._client: Any | None = None
        self._enabled = bool(
            settings.typesafe_enabled
            and _TYPESAFE_AVAILABLE
            and settings.typesafe_api_key
            and settings.typesafe_api_key.get_secret_value()
        )

    async def _get_client(self) -> Any | None:
        if not self._enabled:
            return None
        if self._client is None:
            assert AsyncTypeSafeClient is not None
            self._client = AsyncTypeSafeClient(
                api_key=settings.typesafe_api_key.get_secret_value(),
            )
        return self._client

    async def classify_error(
        self,
        *,
        error_code: str,
        error_message: str,
        endpoint: str,
        method: str,
        request_id: str,
    ) -> dict[str, Any] | None:
        client = await self._get_client()
        if client is None:
            return None
        try:
            result = await client.ask(
                choice(
                    "error_classification",
                    instructions=("Classify this API error for retry and routing decisions."),
                    options=[
                        {"id": "retryable_transient", "label": "Retryable transient error"},
                        {"id": "retryable_rate_limit", "label": "Rate limit exceeded"},
                        {"id": "retryable_validation", "label": "Client validation error"},
                        {"id": "non_retryable_auth", "label": "Auth failure"},
                        {"id": "non_retryable_not_found", "label": "Resource not found"},
                        {"id": "non_retryable_server", "label": "Permanent server error"},
                    ],
                ),
                state={
                    "error_code": error_code,
                    "error_message": error_message,
                    "endpoint": endpoint,
                    "method": method,
                    "request_id": request_id,
                },
            )
            return {
                "selected": result.selected,
                "probability": result.probability,
                "confidence": result.confidence,
            }
        except Exception:
            return None

    async def score_transaction_risk(
        self,
        *,
        business_id: str,
        branch_id: str,
        amount: str,
        currency: str,
        lines_count: int,
        payments_count: int,
        idempotency_key: str | None,
    ) -> dict[str, Any] | None:
        client = await self._get_client()
        if client is None:
            return None
        try:
            result = await client.ask(
                score(
                    "transaction_risk",
                    instructions=("Score this POS sale for fraud or anomaly risk."),
                    levels=[
                        {"id": "0", "description": "No risk"},
                        {"id": "25", "description": "Low risk"},
                        {"id": "50", "description": "Medium risk"},
                        {"id": "75", "description": "High risk"},
                        {"id": "100", "description": "Critical risk"},
                    ],
                ),
                state={
                    "business_id": business_id,
                    "branch_id": branch_id,
                    "amount": amount,
                    "currency": currency,
                    "lines_count": lines_count,
                    "payments_count": payments_count,
                    "has_idempotency_key": idempotency_key is not None,
                },
            )
            return {
                "score": result.score,
                "levels": result.levels,
                "confidence": result.confidence,
            }
        except Exception:
            return None

    async def judge_idempotency_conflict(
        self,
        *,
        key: str,
        original_operation: str,
        original_amount: str,
        original_currency: str,
        original_metadata: dict[str, Any],
        new_operation: str,
        new_amount: str,
        new_currency: str,
        new_metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        client = await self._get_client()
        if client is None:
            return None
        try:
            result = await client.ask(
                noul(
                    "idempotency_conflict",
                    instructions=(
                        "Decide whether two idempotency-keyed requests describe "
                        "the same business command."
                    ),
                ),
                state={
                    "key": key,
                    "original_operation": original_operation,
                    "original_amount": original_amount,
                    "original_currency": original_currency,
                    "original_metadata": original_metadata,
                    "new_operation": new_operation,
                    "new_amount": new_amount,
                    "new_currency": new_currency,
                    "new_metadata": new_metadata,
                },
            )
            return {"conflict": not result.yes, "probability": result.probability}
        except Exception:
            return None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


typesafe = TypeSafeClient()
