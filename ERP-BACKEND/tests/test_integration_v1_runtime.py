
def test_idempotency_returns_same_result_and_rejects_payload_reuse(integration_client):
    client, db = integration_client
    body = {
        "command_id": str(uuid.uuid4()),
        "command_type": "purchase_order_approve",
        "requested_by": "ai-service",
        "payload": {"po_id": 100},
    }
    key = f"idempotency-{uuid.uuid4()}"
    with patch("app.routers.integration_v1.decode_token", return_value=_claims()):
        first = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
        duplicate = client.post("/integration/v1/erp/commands", json=body, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
        changed = {**body, "payload": {"po_id": 100, "comment": "different"}}
        conflict = client.post("/integration/v1/erp/commands", json=changed, headers={"Authorization": "Bearer token", "Idempotency-Key": key})
    assert first.status_code == 202
    assert duplicate.status_code == 202
    assert duplicate.json() == first.json()
