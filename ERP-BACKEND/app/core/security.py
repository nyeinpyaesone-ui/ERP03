from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.models.identity import User

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
    """Validate a Supabase session using the Auth server, not a shared JWT secret."""
    if not settings.supabase_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token"
        )
    url = settings.supabase_url.rstrip("/")
    key = settings.supabase_publishable_key.get_secret_value()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
            response = await client.get(
                f"{url}/auth/v1/user",
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
    if (
        not isinstance(identity, dict)
        or not identity.get("id")
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
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    token = credentials.credentials
    expected_issuer = (
        f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None
    )
    try:
        unverified = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
            algorithms=["HS256", "ES256", "RS256"],
        )
    except jwt.PyJWTError:
        unverified = {}

    if expected_issuer and unverified.get("iss") == expected_issuer:
        identity = await verify_supabase_access_token(token)
        try:
            supabase_user_id = UUID(identity["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase identity"
            ) from exc
        user = await session.scalar(
            select(User).where(
                User.supabase_user_id == supabase_user_id,
                User.active.is_(True),
            )
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supabase identity is not linked to an active ERP03 user",
            )
        return {
            "sub": str(user.id),
            "business_id": str(user.business_id),
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "email": user.email,
            "display_name": user.display_name,
            "auth_provider": "supabase",
        }

    return decode_access_token(token)
