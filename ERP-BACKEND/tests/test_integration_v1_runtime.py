import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import User
from app.integration_runtime.models import IntegrationCommand, PurchaseOrder, PurchaseOrderApproval


@pytest.fixture
def integration_client(db_session):
    db_session.add_all([
        User(id=10, email="approver@example.com", hashed_password="x", full_name="Approver", role="approver", is_active=True),
        User(id=11, email="second@example.com", hashed_password="x", full_name="Second", role="second_approver", is_active=True),
        User(id=12, email="user@example.com", hashed_password="x", full_name="User", role="user", is_active=True),
        PurchaseOrder(id=100, po_number="PO-100", requester_id=12, amount=Decimal("60000.00"), currency_code="USD", status="PENDING_APPROVAL"),
    ])
    db_session.commit()

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    try:
        yield client, db_session
    finally:
        app.dependency_overrides.pop(get_db, None)


def _claims(actor_id=10, subject="ai-service", service=True, valid_issuer=True, valid_audience=True):
    return {
        "sub": subject,
        "service": service,
        "actor_id": actor_id,
        "iss": settings.INTEGRATION_SERVICE_ISSUER if valid_issuer else "invalid-issuer",
        "aud": settings.INTEGRATION_SERVICE_AUDIENCE if valid_audience else "invalid-audience",
    }


def test_missing_service_authentication_is_401(integration_client):
    client, _ = integration_client
    response = client.get("/integration/v1/erp/purchase-orders/100")
    assert response.status_code == 401


def test_non_service_principal_is_403(integration_client):
    client, _ = integration_client
    with patch("app.routers.integration_v1.decode_token", return_value=_claims(service=False)):
        response = client.get("/integration/v1/erp/purchase-orders/100", headers={"Authorization": "Bearer token"})
    assert response.status_code == 403


def test_invalid_service_issuer_is_401(integration_client):
    client, _ = integration_client
    with patch("app.routers.integration_v1.decode_token", return_value=_claims(valid_issuer=False)):
        response = client.get("/integration/v1/erp/purchase-orders/100", headers={"Authorization": "Bearer token"})
    assert response.status_code == 401


def test_purchase_order_read_and_not_found(integration_client):
    client, _ = integration_client
    with patch("app.routers.integration_v1.decode_token", return_value=_claims()):
        ok = client.get("/integration/v1/erp/purchase-orders/100", headers={"Authorization": "Bearer token"})
        missing = client.get("/integration/v1/erp/purchase-orders/999", headers={"Authorization": "Bearer token"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "PENDING_APPROVAL"
    assert missing.status_code == 404


def test_first_level_approval_requires_second_level_for_high_value_po(integration_client):
    client, db = integration_client
    key = "m2-approval-60000-001"
    body = {
        "command_id": str(uuid.uuid4()),
        "command_type": "purchase_order_approve",
        "requested_by": "ai-service",
        "payload": {"po_id": 100, "comment": "Approved at level one"},
    }
    with patch("app.routers.integration_v1.decode_token", return_value=_claims(actor_id=10)):
        response = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
    assert response.status_code == 202
    assert response.json()["result"]["status"] == "PENDING_SECOND_APPROVAL"
    assert db.query(PurchaseOrder).filter_by(id=100).one().status == "PENDING_SECOND_APPROVAL"
    assert db.query(PurchaseOrderApproval).filter_by(po_id=100).one().approval_level == 1


def test_idempotency_returns_same_result_and_rejects_payload_reuse(integration_client):
    client, db = integration_client
    body = {
        "command_id": str(uuid.uuid4()),
        "command_type": "purchase_order_approve",
        "requested_by": "ai-service",
        "payload": {"po_id": 100},
    }
    key = "m2-idempotency-001"
    with patch("app.routers.integration_v1.decode_token", return_value=_claims()):
        first = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
        duplicate = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
        changed = {**body, "payload": {"po_id": 100, "comment": "different"}}
        conflict = client.post("/integration/v1/erp/commands", json=changed, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
    assert first.status_code == 202
    assert duplicate.status_code == 202
    assert duplicate.json() == first.json()
    assert conflict.status_code == 409
    assert db.query(IntegrationCommand).filter_by(idempotency_key=key).count() == 1


def test_second_level_approval_is_authorized_and_completes(integration_client):
    client, db = integration_client
    po = db.query(PurchaseOrder).filter_by(id=100).one()
    po.status = "PENDING_SECOND_APPROVAL"
    db.commit()
    body = {
        "command_id": str(uuid.uuid4()),
        "command_type": "purchase_order_approve",
        "requested_by": "ai-service",
        "payload": {"po_id": 100},
    }
    with patch("app.routers.integration_v1.decode_token", return_value=_claims(actor_id=11)):
        response = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": "m2-level2-001"})
    assert response.status_code == 202
    assert response.json()["result"]["status"] == "APPROVED"


def test_wrong_role_is_403(integration_client):
    client, _ = integration_client
    body = {
        "command_id": str(uuid.uuid4()),
        "command_type": "purchase_order_approve",
        "requested_by": "ai-service",
        "payload": {"po_id": 100},
    }
    with patch("app.routers.integration_v1.decode_token", return_value=_claims(actor_id=12)):
        response = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": "m2-rbac-001"})
    assert response.status_code == 403
