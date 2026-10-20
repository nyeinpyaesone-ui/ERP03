"""TypeSafe System One integration for ERP03.

TypeSafe provides fast, structured judgments (Jev) that software can consume
directly. ERP03 uses TypeSafe for:

- Error classification: deciding whether an error is retryable and how to route it
- Transaction risk scoring: detecting anomalous POS sales before they commit
- Idempotency conflict resolution: judging whether two requests are semantically equal

All TypeSafe calls are gated behind ``TYPESAFE_ENABLED`` and degrade gracefully
when the API is unavailable or misconfigured. Code owns the workflow; TypeSafe
supplies programmable common sense where ordinary code needs semantic
understanding.
"""

from __future__ import annotations

from typing import Any

try:
    from typesafe import AsyncTypeSafeClient, choice, noul, score

    _TYPESAFE_AVAILABLE = True
except ImportError:  # pragma: no cover - TypeSafe is an optional dependency
    AsyncTypeSafeClient = None  # type: ignore[assignment]
    choice = None  # type: ignore[assignment]
    noul = None  # type: ignore[assignment]
    score = None  # type: ignore[assignment]
    _TYPESAFE_AVAILABLE = False

from app.core.config import settings


class TypeSafeClient:
    """Wrapper around the TypeSafe async client with ERP03-specific judgments.

    All methods return ``None`` when TypeSafe is disabled or unavailable, so
    callers can always fall back to deterministic logic.
    """

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

    # ------------------------------------------------------------------ classify error

    async def classify_error(
        self,
        *,
        error_code: str,
        error_message: str,
        endpoint: str,
        method: str,
        request_id: str,
    ) -> dict[str, Any] | None:
        """Classify an error for retry and routing decisions.

        Returns a dict with ``retryable`` (bool), ``severity`` (low/medium/high),
        and ``route_to`` (engineering/support/auto-resolve).
        """
        client = await self._get_client()
        if client is None:
            return None

        try:
            result = await client.ask(
                choice(  # type: ignore[misc]
                    "error_classification",
                    instructions=(
                        "Classify this API error for retry and routing decisions. "
                        "Consider the error code, message, endpoint, and HTTP method."
                    ),
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

    # ------------------------------------------------------------------ score transaction risk

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
        """Score a POS sale for fraud/anomaly risk before commit.

        Returns a dict with ``score`` (0-100) and ``levels`` (probability per level).
        """
        client = await self._get_client()
        if client is None:
            return None

        try:
            result = await client.ask(
                score(  # type: ignore[misc]
                    "transaction_risk",
                    instructions=(
                        "Score this POS sale for fraud or anomaly risk. Consider "
                        "amount, currency, line count, payment count, and whether "
                        "an idempotency key is present."
                    ),
                    levels=[
                        {"id": "0", "description": "No risk - normal transaction"},
                        {"id": "25", "description": "Low risk - minor anomaly"},
                        {"id": "50", "description": "Medium risk - review recommended"},
                        {"id": "75", "description": "High risk - block pending review"},
                        {"id": "100", "description": "Critical risk - block immediately"},
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

    # ------------------------------------------------------------- idempotency conflict resolution

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
        """Judge whether two idempotency-keyed requests are semantically equal.

        Returns a dict with ``conflict`` (bool) and ``reason`` (str).
        """
        client = await self._get_client()
        if client is None:
            return None

        try:
            result = await client.ask(
                noul(  # type: ignore[misc]
                    "idempotency_conflict",
                    instructions=(
                        "Decide whether two idempotency-keyed requests describe "
                        "the same business command. Consider operation, amount, "
                        "currency, and metadata. Canonicalize metadata key order."
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
            return {
                "conflict": not result.yes,  # noul asks "is this the same?"
                "probability": result.probability,
            }
        except Exception:
            return None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()  # type: ignore[attr-defined]
            self._client = None


typesafe = TypeSafeClient()
