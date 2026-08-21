"""Executable, dependency-light checks for the ERP03 integration contract v1.

These tests intentionally validate the contract artifacts themselves so M2 cannot
be marked complete merely because documentation exists. Runtime HTTP tests should
be added once the ERP integration router is wired into ERP-BACKEND.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def test_command_contract_has_required_identity_and_mutation_fields() -> None:
    contract = json.loads((ROOT / "command-contract.json").read_text(encoding="utf-8"))
    assert contract["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert contract["additionalProperties"] is False
    assert contract["required"] == ["command_id", "command_type", "requested_by", "payload"]
    assert set(contract["properties"]["command_type"]["enum"]) == {
        "purchase_order_approve",
        "purchase_order_reject",
    }


def test_openapi_contract_exposes_versioned_boundary_and_security() -> None:
    spec = (ROOT / "erp-ai.openapi.yaml").read_text(encoding="utf-8")
    assert "url: /integration/v1" in spec
    assert "serviceBearer" in spec
    assert "Idempotency-Key" in spec
    assert "purchase_order_approve" in spec
    assert "purchase_order_reject" in spec
    for status in ("'400'", "'401'", "'403'", "'409'"):
        assert status in spec


def test_openapi_contract_requires_idempotency_key_for_commands() -> None:
    spec = (ROOT / "erp-ai.openapi.yaml").read_text(encoding="utf-8")
    command_section = spec.split("/erp/commands:", 1)[1]
    assert "IdempotencyKey" in command_section
    assert "required: true" in command_section


def test_boundary_policy_forbids_internal_erp_coupling() -> None:
    policy = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "ORM entities are prohibited" in policy
    assert "No direct database" not in policy  # DB prohibition is stated in erp-client policy.

    client_policy = (
        ROOT.parent.parent / "erp-client" / "README.md"
    ).read_text(encoding="utf-8")
    assert "No direct database connection" in client_policy
    assert "No import of ERP ORM models/repositories/services" in client_policy


def test_authentication_policy_keeps_authn_and_authorization_separate() -> None:
    policy = (ROOT.parent.parent / "authentication" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "issuer, audience, signature, expiry" in policy.lower()
    assert "Authorization is performed again by ERP" in policy
    assert "401" in policy
    assert "403" in policy
    assert "Tokens must not be logged" in policy
