from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

password_hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Argon2Error:
        # Any hashing failure (bad hash format, invalid credentials, unknown
        # parameters) authenticates nobody; never surface it as a 500.
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


async def current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return decode_access_token(credentials.credentials)
