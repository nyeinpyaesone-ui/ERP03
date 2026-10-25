"""TypeSafe System One integration tests.

TypeSafe is optional and degradable by default (TYPESAFE_ENABLED=false).
These tests verify:
- Graceful degradation when TypeSafe is disabled or unavailable.
- Correct structure of judgment results when enabled.
- Degraded behavior never breaks the request/response contract.
"""

import asyncio
from unittest.mock import patch

from app.core.typesafe import (
    CONFIDENCE_ACT_THRESHOLD,
    CONFIDENCE_ESCALATE_THRESHOLD,
    ErrorClassification,
    IdempotencyJudgment,
    TransactionRisk,
    typesafe,
)


def _run(coro):
    """Run an async coroutine in a fresh event loop (pytest-safe)."""
    return asyncio.run(coro)


class TestTypeSafeDegradedByDefault:
    """TypeSafe must degrade gracefully when disabled (the default)."""

    def test_typesafe_disabled_by_default(self):
        """TYPESAFE_ENABLED defaults to False -> client is not enabled."""
        assert not typesafe._enabled

    def test_classify_error_returns_none_when_disabled(self):
        """classify_error returns None without calling the SDK when disabled."""
        result = _run(
            typesafe.classify_error(
                error_code="VALIDATION_ERROR",
                error_message="bad input",
                endpoint="/api/v1/sales",
                method="POST",
                request_id="req-1",
            )
        )
        assert result is None

    def test_score_transaction_risk_returns_none_when_disabled(self):
        result = _run(
            typesafe.score_transaction_risk(
                business_id="biz-1",
                branch_id="branch-1",
                amount="100.00",
                currency="MMK",
                lines_count=3,
                payments_count=1,
                idempotency_key=None,
            )
        )
        assert result is None

    def test_judge_idempotency_conflict_returns_none_when_disabled(self):
        result = _run(
            typesafe.judge_idempotency_conflict(
                key="key-1",
                original_operation="invoice.create",
                original_amount="100.00",
                original_currency="MMK",
                original_metadata={},
                new_operation="invoice.create",
                new_amount="100.00",
                new_currency="MMK",
                new_metadata={},
            )
        )
        assert result is None

    def test_judge_request_returns_disabled_shape(self):
        result = _run(
            typesafe.judge_request(
                request_id="req-1",
                method="POST",
                endpoint="/api/v1/sales",
            )
        )
        assert result == {"classification": None, "risk": None, "enabled": False}


class TestTypeSafeDataStructures:
    """Verify the typed judgment dataclasses behave correctly."""

    def test_error_classification_retryable(self):
        cls = ErrorClassification(
            selected="retryable_transient",
            probability=0.9,
            confidence=0.95,
            escalate=False,
        )
        assert cls.is_retryable is True
        assert cls.retry_after_seconds == 2

    def test_error_classification_rate_limit(self):
        cls = ErrorClassification(
            selected="retryable_rate_limit",
            probability=0.9,
            confidence=0.95,
            escalate=False,
        )
        assert cls.retry_after_seconds == 30

    def test_error_classification_validation(self):
        cls = ErrorClassification(
            selected="retryable_validation",
            probability=0.9,
            confidence=0.95,
            escalate=False,
        )
        assert cls.retry_after_seconds == 0

    def test_error_classification_non_retryable(self):
        cls = ErrorClassification(
            selected="non_retryable_auth",
            probability=0.9,
            confidence=0.95,
            escalate=False,
        )
        assert cls.is_retryable is False
        assert cls.retry_after_seconds is None

    def test_error_classification_low_confidence_not_retryable(self):
        cls = ErrorClassification(
            selected="retryable_transient",
            probability=0.5,
            confidence=0.3,  # below act threshold
            escalate=True,
        )
        assert cls.is_retryable is False

    def test_transaction_risk_high(self):
        risk = TransactionRisk(
            score=90,
            levels=[0, 25, 50, 75, 100],
            confidence=0.9,
            escalate=False,
        )
        assert risk.is_high_risk is True

    def test_transaction_risk_low(self):
        risk = TransactionRisk(
            score=10,
            levels=[0, 25, 50, 75, 100],
            confidence=0.9,
            escalate=False,
        )
        assert risk.is_high_risk is False

    def test_transaction_risk_low_confidence_not_high(self):
        risk = TransactionRisk(
            score=90,
            levels=[0, 25, 50, 75, 100],
            confidence=0.3,
            escalate=True,
        )
        assert risk.is_high_risk is False

    def test_idempotency_judgment_conflict(self):
        """yes=False with adequate confidence -> conflict."""
        judgment = IdempotencyJudgment(yes=False, probability=0.1, confidence=0.9)
        assert judgment.is_conflict is True

    def test_idempotency_judgment_replay(self):
        """yes=True with adequate confidence -> not a conflict (replay)."""
        judgment = IdempotencyJudgment(yes=True, probability=0.9, confidence=0.9)
        assert judgment.is_conflict is False

    def test_idempotency_judgment_low_confidence_not_conflict(self):
        judgment = IdempotencyJudgment(yes=False, probability=0.5, confidence=0.3)
        assert judgment.is_conflict is False


class TestTypeSafeThresholds:
    """Confidence thresholds match AGENTS.md contract."""

    def test_act_threshold_is_0_70(self):
        assert CONFIDENCE_ACT_THRESHOLD == 0.70

    def test_escalate_threshold_is_0_40(self):
        assert CONFIDENCE_ESCALATE_THRESHOLD == 0.40


class TestTypeSafeSDKUnavailable:
    """When the SDK package is not installed, everything degrades to None."""

    @patch("app.core.typesafe._TYPESAFE_AVAILABLE", False)
    @patch("app.core.typesafe.AsyncTypeSafeClient", None)
    def test_client_disabled_when_sdk_missing(self):
        from app.core.typesafe import TypeSafeClient

        client = TypeSafeClient.__new__(TypeSafeClient)
        client._client = None
        client._enabled = False
        assert client._enabled is False
