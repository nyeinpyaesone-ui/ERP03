"""GitHub webhook receiver for repository automation."""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config import settings

logger = logging.getLogger("erp03.github_webhook")
router = APIRouter(prefix="/webhooks/github", tags=["GitHub Webhooks"])


def _verify_signature(payload: bytes, signature: str | None) -> bool:
    """Verify GitHub's HMAC SHA-256 signature using a dedicated secret."""
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret or not signature:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
):
    """Accept and authenticate GitHub webhook deliveries.

    The endpoint deliberately acknowledges authenticated events without executing
    repository-changing actions. Automation can be added behind this boundary later.
    """
    payload = await request.body()

    if not _verify_signature(payload, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitHub webhook signature",
        )

    try:
        body = json.loads(payload or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc

    logger.info(
        "GitHub webhook accepted",
        extra={
            "event": x_github_event or "unknown",
            "delivery_id": x_github_delivery or "unknown",
            "action": body.get("action"),
        },
    )

    return {
        "status": "accepted",
        "event": x_github_event or "unknown",
        "delivery_id": x_github_delivery,
    }
