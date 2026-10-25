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

SDK contract (``typesafe-sdk``):
- Questions travel as a mapping of question name -> question object.
- Answers come back grouped by type and keyed by question name:
  ``response.choices``, ``response.nouls``, ``response.scores``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Self

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

    _TYPESAFE_AVAILABLE = True
except ImportError:  # pragma: no cover - TypeSafe is optional
    AsyncTypeSafeClient = None  # type: ignore[assignment]
    Choice = Noul = Score = None  # type: ignore[assignment]
    _TYPESAFE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------

# Below this confidence, code does NOT act on a TypeSafe judgment for
# state-changing decisions (retry, conflict rejection, risk escalation).
CONFIDENCE_ACT_THRESHOLD = 0.70

# Below this confidence, the judgment is escalated for human review regardless
# of the selected option.
CONFIDENCE_ESCALATE_THRESHOLD = 0.40

ERROR_CLASSIFICATION_QUESTION = "error_classification"
TRANSACTION_RISK_QUESTION = "transaction_risk"
IDEMPOTENCY_CONFLICT_QUESTION = "idempotency_conflict"


@dataclass(frozen=True)
class ErrorClassification:
    """Typed result of an error-classification judgment.

    ``selected`` is the model's pick; ``confidence`` gates whether code acts.
    Code derives retry/escalate from ``selected`` only when confidence meets the
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

    score: int
    levels: list[Any]
    confidence: float
    escalate: bool

    @property
    def is_high_risk(self) -> bool:
        """Code-owned high-risk decision based on score + confidence."""
        if self.confidence < CONFIDENCE_ACT_THRESHOLD:
            return False
        return self.score >= 75


@dataclass(frozen=True)
class IdempotencyJudgment:
    """Typed result of an idempotency-conflict judgment.

    ``yes`` from the Noul means "same business command" → replay. Code rejects
    only when ``is_conflict`` is true (not same command with adequate confidence).
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


def _error_classification_question() -> Any:
    """Choice question: classify an API error for retry and routing decisions."""
    return Choice(
        type="choice",
        instructions=(
            "Classify this API error for retry and routing decisions. "
            "If none of the retryable categories apply and the error is "
            "not clearly auth/not-found/server, select unclassified."
        ),
        criteria={
            "retryable_transient": "Retryable transient error; temporary failure",
            "retryable_rate_limit": "Rate limit exceeded; retry after backoff",
            "retryable_validation": "Client validation error; do not retry",
            "non_retryable_auth": "Auth failure; do not retry",
            "non_retryable_not_found": "Resource not found; do not retry",
            "non_retryable_server": "Permanent server error; do not retry",
            "unclassified": "Cannot determine category",
        },
    )


def _transaction_risk_question() -> Any:
    """Score question: fraud or anomaly risk for a POS sale."""
    return Score(
        type="score",
        instructions="Score this POS sale for fraud or anomaly risk.",
        criteria=[
            "No risk",
            "Low risk",
            "Medium risk",
            "High risk",
            "Critical risk",
        ],
    )


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
            await self._client.aclose()
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
            response = await client.system_one(
                state={
                    "error_code": error_code,
                    "error_message": error_message,
                    "endpoint": endpoint,
                    "method": method,
                    "request_id": request_id,
                },
                questions={
                    ERROR_CLASSIFICATION_QUESTION: _error_classification_question(),
                },
            )
            answer = response.choices[ERROR_CLASSIFICATION_QUESTION]
            return ErrorClassification(
                selected=answer.choice,
                probability=answer.probabilities.get(answer.choice, 0.0),
                confidence=answer.confidence,
                escalate=answer.confidence < CONFIDENCE_ESCALATE_THRESHOLD,
            )
        except Exception:  # pragma: no cover - TypeSafe optional
            logger.debug("TypeSafe classify_error failed", exc_info=True)
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
            response = await client.system_one(
                state={
                    "business_id": business_id,
                    "branch_id": branch_id,
                    "amount": amount,
                    "currency": currency,
                    "lines_count": lines_count,
                    "payments_count": payments_count,
                    "has_idempotency_key": idempotency_key is not None,
                },
                questions={
                    TRANSACTION_RISK_QUESTION: _transaction_risk_question(),
                },
            )
            answer = response.scores[TRANSACTION_RISK_QUESTION]
            # legend is a dict mapping index string -> description; preserve order
            legend_vals = [answer.legend[k] for k in sorted(answer.legend, key=lambda x: int(x))]
            return TransactionRisk(
                score=int(answer.score),
                levels=legend_vals,
                confidence=answer.confidence,
                escalate=answer.confidence < CONFIDENCE_ESCALATE_THRESHOLD,
            )
        except Exception:  # pragma: no cover - TypeSafe optional
            logger.debug("TypeSafe score_transaction_risk failed", exc_info=True)
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
            response = await client.system_one(
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
                questions={
                    IDEMPOTENCY_CONFLICT_QUESTION: Noul(
                        type="noul",
                        instructions=(
                            "Answer yes if both requests describe the same business "
                            "command (same operation, amount, currency, and business "
                            "meaning despite metadata key-order differences). "
                            "Answer no if they are genuinely different commands."
                        ),
                    ),
                },
            )
            answer = response.nouls[IDEMPOTENCY_CONFLICT_QUESTION]
            yes = answer.noul > 0.5
            confidence = abs(2 * answer.noul - 1)
            return IdempotencyJudgment(
                yes=yes,
                probability=answer.noul,
                confidence=confidence,
            )
        except Exception:  # pragma: no cover - TypeSafe optional
            logger.debug("TypeSafe judge_idempotency_conflict failed", exc_info=True)
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
        in parallel (one batched call); code consumes the applicable answers.
        """
        client = await self._get_client()
        if client is None:
            return {"classification": None, "risk": None, "enabled": False}

        questions: dict[str, Any] = {}
        state: dict[str, Any] = {
            "request_id": request_id,
            "method": method,
            "endpoint": endpoint,
        }

        if error_code is not None and error_message is not None:
            questions[ERROR_CLASSIFICATION_QUESTION] = _error_classification_question()
            state["error"] = {
                "code": error_code,
                "message": error_message,
                "endpoint": endpoint,
                "method": method,
                "request_id": request_id,
            }

        if business_id is not None and amount is not None and currency is not None:
            questions[TRANSACTION_RISK_QUESTION] = _transaction_risk_question()
            state["business_id"] = business_id
            state["branch_id"] = branch_id or ""
            state["amount"] = amount
            state["currency"] = currency
            state["lines_count"] = lines_count or 0
            state["payments_count"] = payments_count or 0
            state["has_idempotency_key"] = idempotency_key is not None

        if not questions:
            return {"classification": None, "risk": None, "enabled": False}

        try:
            response = await client.system_one(state=state, questions=questions)
        except Exception:  # pragma: no cover - TypeSafe optional
            logger.debug("TypeSafe judge_request failed", exc_info=True)
            return {"classification": None, "risk": None, "enabled": True}

        output: dict[str, Any] = {"classification": None, "risk": None, "enabled": True}
        if ERROR_CLASSIFICATION_QUESTION in response.choices:
            answer = response.choices[ERROR_CLASSIFICATION_QUESTION]
            output["classification"] = {
                "selected": answer.choice,
                "probability": answer.probabilities.get(answer.choice, 0.0),
                "confidence": answer.confidence,
                "escalate": answer.confidence < CONFIDENCE_ESCALATE_THRESHOLD,
            }
        if TRANSACTION_RISK_QUESTION in response.scores:
            answer = response.scores[TRANSACTION_RISK_QUESTION]
            try:
                legend_vals = [
                    answer.legend[k] for k in sorted(answer.legend, key=lambda x: int(x))
                ]
            except (KeyError, ValueError, TypeError):
                legend_vals = []
            output["risk"] = {
                "score": int(answer.score),
                "levels": legend_vals,
                "confidence": answer.confidence,
                "escalate": answer.confidence < CONFIDENCE_ESCALATE_THRESHOLD,
            }
        return output

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()


typesafe = TypeSafeClient()
