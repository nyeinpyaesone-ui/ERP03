"""Low-cardinality Prometheus metrics for durable operation transitions."""

from prometheus_client import Counter

OPERATION_TRANSITIONS = Counter(
    "erp03_operation_transitions_total",
    "Total durable operation state transitions",
    ["operation_type", "from_state", "to_state"],
)
OPERATION_RETRIES = Counter(
    "erp03_operation_retries_total",
    "Total scheduled durable-operation retries",
    ["operation_type", "error_code"],
)


def record_operation_transition(operation_type: str, from_state: str, to_state: str) -> None:
    """Record a state transition without high-cardinality IDs as labels."""
    OPERATION_TRANSITIONS.labels(
        operation_type=operation_type,
        from_state=from_state,
        to_state=to_state,
    ).inc()


def record_operation_retry(operation_type: str, error_code: str) -> None:
    """Record a retry using the stable error code, never raw error text."""
    OPERATION_RETRIES.labels(
        operation_type=operation_type,
        error_code=error_code or "unknown",
    ).inc()
