from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionFactory
from app.models.identity import Business, User

password_hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Argon2Error:
        return False


def create_access_token(
    user_id: UUID, business_id: UUID, branch_id: UUID | None, expires_minutes: int | None = None
) -> str:
    now = datetime.now(UTC)
    expiry = expires_minutes if expires_minutes is not None else settings.jwt_expiry_minutes
    payload = {
        "sub": str(user_id),
        "business_id": str(business_id),
        "branch_id": str(branch_id) if branch_id else None,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expiry)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token"
        ) from exc


async def verify_supabase_access_token(token: str) -> dict:
    """Ask Supabase Auth to validate the bearer token (works with current signing keys)."""
    if not settings.supabase_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token"
        )
    url = settings.supabase_url
    publishable_key = settings.supabase_publishable_key
    if not url or publishable_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Supabase Auth is not configured"
        )
    key = publishable_key.get_secret_value()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
            response = await client.get(
                f"{url.rstrip('/')}/auth/v1/user",
                headers={"apikey": key, "Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase identity verification is temporarily unavailable",
        ) from exc
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Supabase session"
        )
    identity = response.json()
    if not isinstance(identity, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase identity response"
        )
    if (
        not identity.get("id")
        or not identity.get("email")
        or not identity.get("email_confirmed_at")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A verified Supabase email identity is required",
        )
    return identity


async def current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    token = credentials.credentials
    try:
        return decode_access_token(token)
    except HTTPException:
        identity = await verify_supabase_access_token(token)
        try:
            supabase_user_id = UUID(identity["id"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase identity"
            ) from exc
        async with SessionFactory() as session:
            user = await session.scalar(
                select(User)
                .join(Business, Business.id == User.business_id)
                .where(
                    User.supabase_user_id == supabase_user_id,
                    User.active.is_(True),
                    Business.active.is_(True),
                )
            )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supabase identity is not linked to an active ERP03 user",
            ) from None
        return {
            "sub": str(user.id),
            "business_id": str(user.business_id),
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "auth_provider": "supabase",
        }
