import pytest

from app.services.bootstrap import BootstrapConflictError


def test_bootstrap_conflict_is_explicit():
    error = BootstrapConflictError("Business code already exists")
    assert str(error) == "Business code already exists"
