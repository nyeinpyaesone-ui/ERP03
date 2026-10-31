"""TypeSafe System One integration for ERP03.

Provides error classification, transaction risk scoring, and idempotency
conflict judgment. All calls degrade gracefully when the SDK is unavailable
or disabled. Code owns the workflow; TypeSafe supplies programmable common
sense where ordinary code needs semantic understanding.

TypeSafe contract (per System One model design):
- Each question asks ONE narrow, coherent judgment.
- Choice includes a ``unclassified`` no-match outcome when nothing fits.
- Noul polarity is explicit: ``yes`` means "same business command".
- Code owns retry/routing/escalation decisions; TypeSafe only annotates.
- Confidence thresholds gate acting on a judgment.
- Independent judgments over the same request state are asked together.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Self

try:
    from typesafe import AsyncTypeSafeClient, choice, noul, score

    _TYPESAFE_AVAILABLE = True
except ImportError:  # pragma: no cover - TypeSafe is optional
    AsyncTypeSafeClient = None  # type: ignore[assignment]
    choice = noul = score = None  # type: ignore[assignment]
    _TYPESAFE_AVAILABLE = False

from app.core.config import settings

# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------

# Below this confidence, code does NOT act on a TypeSafe judgment for
# state-changing decisions (retry, conflict rejection, risk escalation).
# The value is tuned from observed TypeSafe calibration on ERP03 traffic.
CONFIDENCE_ACT_THRESHOLD = 0.70

# Below this confidence, the judgment is escalated for human review regardless
# of the selected option.
CONFIDENCE_ESCALATE_THRESHOLD = 0.40


@dataclass(frozen=True)
class ErrorClassification:
    """Typed result of an error-classification judgment.

    ``selected`` is the model's pick; ``confidence`` gates whether code acts.
    Code derives retry/routing from ``selected`` only when confidence meets the
    act threshold.
    """

    selected: str
    probability: float
    confidence: float
    escalate: bool

    @property
    def is_retryable(self) -> bool:
        """Code-owned retry decision based on classification + confidence."""
        if self.confidence < CONFIDENCE_ACT_THRESHOLD:
            return False
        return self.selected in {
            "retryable_transient",
            "retryable_rate_limit",
            "retryable_validation",
        }

    @property
    def retry_after_seconds(self) -> int | None:
        """Derived retry delay; code-owned, not model-provided."""
        if not self.is_retryable:
            return None
        delays = {
            "retryable_transient": 2,
            "retryable_rate_limit": 30,
            "retryable_validation": 0,
        }
        return delays.get(self.selected)


@dataclass(frozen=True)
class TransactionRisk:
    """Typed result of a transaction-risk score judgment."""

    score: int  # 0-100
    levels: list[Any]
    confidence: float
    escalate: bool

    @property
    def is_high_risk(self) -> bool:
        if self.confidence < CONFIDENCE_ACT_THRESHOLD:
            return False
        return self.score >= 75


@dataclass(frozen=True)
class IdempotencyJudgment:
    """Typed result of an idempotency-conflict judgment.

    ``yes`` from the Noul means "same business command" → replay, not conflict.
    """

    yes: bool
    probability: float
    confidence: float

    @property
    def is_conflict(self) -> bool:
        """Code-owned conflict decision: not-same-command with adequate confidence."""
        if self.confidence < CONFIDENCE_ACT_THRESHOLD:
            return False  # low confidence → do not reject, escalate instead
        return not self.yes


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

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    # ------------------------------------------------------------------ error classification

    async def classify_error(
        self,
        *,
        error_code: str,
        error_message: str,
        endpoint: str,
        method: str,
        request_id: str,
    ) -> ErrorClassification | None:
        """Classify an API error for retry and routing decisions.

        The model picks one category; code decides retry/escalate based on
        ``selected`` plus ``confidence``.
        """
        client = await self._get_client()
        if client is None:
            return None
        try:
            result = await client.ask(
                choice(
                    "error_classification",
                    instructions=(
                        "Classify this API error for retry and routing decisions. "
                        "If none of the retryable categories apply and the error is "
                        "not clearly auth/not-found/server, select unclassified."
                    ),
                    options=[
                        {"id": "retryable_transient", "label": "Retryable transient error"},
                        {"id": "retryable_rate_limit", "label": "Rate limit exceeded"},
                        {"id": "retryable_validation", "label": "Client validation error"},
                        {"id": "non_retryable_auth", "label": "Auth failure"},
                        {"id": "non_retryable_not_found", "label": "Resource not found"},
                        {"id": "non_retryable_server", "label": "Permanent server error"},
                        {"id": "unclassified", "label": "Cannot determine category"},
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
            escalate = result.confidence < CONFIDENCE_ESCALATE_THRESHOLD
            return ErrorClassification(
                selected=result.selected,
                probability=result.probability,
                confidence=result.confidence,
                escalate=escalate,
            )
        except Exception:
            return None

    # ------------------------------------------------------------------ transaction risk

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
    ) -> TransactionRisk | None:
        """Score a POS sale for fraud or anomaly risk.

        Code decides high-risk action (block/flag/review) from score + confidence.
        """
        client = await self._get_client()
        if client is None:
            return None
        try:
            result = await client.ask(
                score(
                    "transaction_risk",
                    instructions=(
                        "Score this POS sale for fraud or anomaly risk. "
                        "Use level 100 only for clear fraud patterns."
                    ),
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
            escalate = result.confidence < CONFIDENCE_ESCALATE_THRESHOLD
            return TransactionRisk(
                score=result.score,
                levels=result.levels,
                confidence=result.confidence,
                escalate=escalate,
            )
        except Exception:
            return None

    # ------------------------------------------------------------------ idempotency conflict

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
    ) -> IdempotencyJudgment | None:
        """Decide whether two idempotency-keyed requests describe the same command.

        Noul ``yes`` means "same business command" → replay. Code rejects only
        when ``is_conflict`` is true (not same command with adequate confidence).
        """
        client = await self._get_client()
        if client is None:
            return None
        try:
            result = await client.ask(
                noul(
                    "idempotency_conflict",
                    instructions=(
                        "Answer yes if both requests describe the same business "
                        "command (same operation, amount, currency, and business "
                        "meaning despite metadata key-order differences). "
                        "Answer no if they are genuinely different commands."
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
            return IdempotencyJudgment(
                yes=result.yes,
                probability=result.probability,
                confidence=result.confidence,
            )
        except Exception:
            return None

    # ------------------------------------------------------------------ composition

    async def judge_request(
        self,
        *,
        request_id: str,
        method: str,
        endpoint: str,
        error_code: str | None = None,
        error_message: str | None = None,
        business_id: str | None = None,
        branch_id: str | None = None,
        amount: str | None = None,
        currency: str | None = None,
        lines_count: int | None = None,
        payments_count: int | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Ask independent judgments over the same request state together.

        Per TypeSafe guidance: independent questions over identical state run
        in parallel (asyncio.gather) and cannot see one another's answers. Code
        consumes the applicable answers.
        """
        client = await self._get_client()
        if client is None:
            return {"classification": None, "risk": None, "enabled": False}

        tasks: list[Any] = []

        if error_code is not None and error_message is not None:
            tasks.append(
                client.ask(
                    choice(
                        "error_classification",
                        instructions=(
                            "Classify this API error for retry and routing. "
                            "Select unclassified if no category fits."
                        ),
                        options=[
                            {"id": "retryable_transient", "label": "Retryable transient"},
                            {"id": "retryable_rate_limit", "label": "Rate limit"},
                            {"id": "retryable_validation", "label": "Client validation"},
                            {"id": "non_retryable_auth", "label": "Auth failure"},
                            {"id": "non_retryable_not_found", "label": "Not found"},
                            {"id": "non_retryable_server", "label": "Server error"},
                            {"id": "unclassified", "label": "Cannot determine"},
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
            )

        if business_id is not None and amount is not None and currency is not None:
            tasks.append(
                client.ask(
                    score(
                        "transaction_risk",
                        instructions="Score this POS sale for fraud or anomaly risk.",
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
                        "branch_id": branch_id or "",
                        "amount": amount,
                        "currency": currency,
                        "lines_count": lines_count or 0,
                        "payments_count": payments_count or 0,
                        "has_idempotency_key": idempotency_key is not None,
                    },
                )
            )

        if not tasks:
            return {"classification": None, "risk": None, "enabled": True}

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, Any] = {"classification": None, "risk": None, "enabled": True}
        idx = 0
        if error_code is not None and error_message is not None:
            result = results[idx]
            idx += 1
            if isinstance(result, Exception):
                output["classification"] = None
            else:
                output["classification"] = {
                    "selected": result.selected,
                    "probability": result.probability,
                    "confidence": result.confidence,
                    "escalate": result.confidence < CONFIDENCE_ESCALATE_THRESHOLD,
                }
        if business_id is not None and amount is not None and currency is not None:
            result = results[idx]
            if isinstance(result, Exception):
                output["risk"] = None
            else:
                output["risk"] = {
                    "score": result.score,
                    "levels": result.levels,
                    "confidence": result.confidence,
                    "escalate": result.confidence < CONFIDENCE_ESCALATE_THRESHOLD,
                }
        return output

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


typesafe = TypeSafeClient()
