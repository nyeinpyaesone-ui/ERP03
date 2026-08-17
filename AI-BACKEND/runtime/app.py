from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .config import load_settings
from .erp_client import ErpClient
from .provider import DeterministicProvider

app = FastAPI(title="ERP03 AI Runtime", version="0.1.0")
settings = load_settings()
erp = ErpClient(settings)
provider = DeterministicProvider()


class Command(BaseModel):
    command_id: uuid.UUID
    command_type: str = Field(pattern=r"^purchase_order_(approve|reject)$")
    requested_by: str = Field(min_length=1)
    payload: dict[str, Any]


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    if not settings.service_token:
        raise HTTPException(503, "ERP service authentication is not configured")
    return {"status": "ready"}


@app.get("/v1/purchase-orders/{po_id}")
async def purchase_order(po_id: int, x_correlation_id: str | None = Header(default=None)) -> dict[str, Any]:
    correlation_id = x_correlation_id or str(uuid.uuid4())
    return await erp.get_purchase_order(po_id, correlation_id)


@app.post("/v1/commands", status_code=202)
async def command(
    body: Command,
    idempotency_key: str = Header(min_length=16, max_length=128),
    x_correlation_id: str | None = Header(default=None),
) -> dict[str, Any]:
    correlation_id = x_correlation_id or str(uuid.uuid4())
    result = await erp.submit_command(body.model_dump(mode="json"), idempotency_key, correlation_id)
    return result
