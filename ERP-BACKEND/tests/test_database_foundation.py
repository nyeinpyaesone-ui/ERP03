from app.db.base import Base
import app.models  # noqa: F401


def test_identity_metadata_is_registered() -> None:
    tables = set(Base.metadata.tables)
    assert {"businesses", "branches", "users", "roles", "permissions"}.issubset(tables)


def test_identity_indexes_are_present() -> None:
    branch_indexes = {index.name for index in Base.metadata.tables["branches"].indexes}
    user_indexes = {index.name for index in Base.metadata.tables["users"].indexes}
    assert "ix_branches_business_active" in branch_indexes
    assert "ix_users_business_active" in user_indexes
