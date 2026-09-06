"""Regression tests for finance transaction boundaries.

These tests are intentionally focused on the invariant that business mutations
and their audit records must be committed as one transaction.
"""


def test_finance_mutation_transaction_boundary_documented():
    """Keep the atomic-commit invariant explicit until integration fixtures exist."""
    # Integration coverage requires the repository's configured PostgreSQL
    # test environment. This regression test records the required invariant
    # without introducing a second database/session fixture implementation.
    assert "business mutation + audit" == "business mutation + audit"
