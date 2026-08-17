from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import RuntimeSettings


class ErpClient:
    """AI-side adapter; contains no ORM, repository, or database access."""

    def __init__(self, settings: RuntimeSettings, transport: httpx.AsyncClient | None = None):
        self.settings = settings
        self._transport = transport

    def _headers(self, correlation_id: str, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.settings.service_token}", "X-Correlation-ID": correlation_id}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def _request(self, method: str, path: str, *, correlation_id: str, idempotency_key: str | None = None, json: Any = None) -> httpx.Response:
        client = self._transport or httpx.AsyncClient()
        own_client = self._transport is None
        try:
            last: Exception | None = None
            for attempt in range(self.settings.max_retries + 1):
                try:
                    return await client.request(
                        method, f"{self.settings.erp_base_url}{path}",
                        headers=self._headers(correlation_id, idempotency_key),
                        json=json, timeout=self.settings.request_timeout_seconds,
                    )
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last = exc
                    if attempt < self.settings.max_retries:
                        await asyncio.sleep(0.1 * (2 ** attempt))
            raise RuntimeError("ERP integration unavailable") from last
        finally:
            if own_client:
                await client.aclose()

    async def get_purchase_order(self, po_id: int, correlation_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/erp/purchase-orders/{po_id}", correlation_id=correlation_id)
        response.raise_for_status()
        return response.json()

    async def submit_command(self, command: dict[str, Any], idempotency_key: str, correlation_id: str) -> dict[str, Any]:
        response = await self._request("POST", "/erp/commands", correlation_id=correlation_id, idempotency_key=idempotency_key, json=command)
        if response.status_code not in (202, 400, 401, 403, 409):
            response.raise_for_status()
        return response.json()
