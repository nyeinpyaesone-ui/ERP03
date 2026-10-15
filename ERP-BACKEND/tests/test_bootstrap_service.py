from app.core.errors import BootstrapConflictError


def test_bootstrap_conflict_is_explicit():
    error = BootstrapConflictError("Business code already exists")
    assert str(error) == "Business code already exists"
