"""Regression tests for the ORM, migration, and authentication contracts."""

from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.main import app
from app.models import Business, Invoice, Permission, Role, User
from httpx import ASGITransport, AsyncClient


def test_identity_and_invoice_models_expose_migrated_contracts() -> None:
    assert {"businesses", "users", "roles", "permissions", "invoices"}.issubset(
        Base.metadata.tables
    )

    user_columns = set(User.__table__.columns.keys())
    assert {
        "business_id",
        "branch_id",
        "email",
        "password_hash",
        "display_name",
        "active",
    } <= user_columns
    assert {"code"} <= set(Business.__table__.columns.keys())
    assert {"code"} <= set(Permission.__table__.columns.keys())
    assert {"business_id", "name"} <= set(Role.__table__.columns.keys())

    invoice_columns = set(Invoice.__table__.columns.keys())
    assert {"idempotency_key", "request_fingerprint"} <= invoice_columns


def test_alembic_history_has_one_complete_head() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["0009_invoice_numbering_index"]
    revisions = {revision.revision for revision in script.walk_revisions()}
    assert {
        "0001_identity",
        "0002_transactional_erp",
        "0003_user_branch_scope",
        "0004_invoice_idempotency",
        "0004_sales_permission",
        "0005_catalog_permissions",
        "0006_invoice_fingerprint",
        "0007_operation_orchestration",
        "0008_audit_log",
        "0009_invoice_numbering_index",
    } <= revisions


def test_password_hash_contract_uses_argon2_and_fails_closed() -> None:
    password = "Correct-Horse-123"
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2")
    assert verify_password(password, password_hash)
    assert not verify_password("incorrect-password", password_hash)
    assert not verify_password(password, "not-a-valid-password-hash")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_registration_and_login_follow_business_scoped_identity_contract() -> None:
    email = f"shared-{uuid4().hex}@example.com"
    password = "Correct-Horse-123"
    business_codes = [f"AUTH-{uuid4().hex[:10]}" for _ in range(2)]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        registered = []
        for business_code in business_codes:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "business_code": business_code,
                    "business_name": f"{business_code} Business",
                    "email": email,
                    "password": password,
                    "display_name": "Tenant Owner",
                    "default_currency": "MMK",
                    "timezone": "Asia/Yangon",
                    "locale": "my-MM",
                },
            )
            assert response.status_code == 200, response.text
            registered.append(response.json())

            login = await client.post(
                "/api/v1/auth/login",
                json={
                    "business_code": business_code,
                    "email": email,
                    "password": password,
                },
            )
            assert login.status_code == 200, login.text
            assert login.json()["user"]["business_id"] == response.json()["business_id"]

        duplicate = await client.post(
            "/api/v1/auth/register",
            json={
                "business_code": business_codes[0],
                "email": f"another-{uuid4().hex}@example.com",
                "password": password,
                "display_name": "Duplicate Business",
            },
        )
        assert duplicate.status_code == 409
        assert registered[0]["business_id"] != registered[1]["business_id"]
