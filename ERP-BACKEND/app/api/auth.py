"""Authentication endpoints: credential exchange and current-principal lookup."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.security import create_access_token, verify_password
from app.db.session import get_db_session
from app.models.identity import Business, User
from app.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    result = await session.execute(
        select(User)
        .join(Business, Business.id == User.business_id)
        .where(
            Business.code == payload.business_code.strip(),
            Business.active.is_(True),
            User.email == payload.email.lower(),
            User.active.is_(True),
        )
    )
    user = result.scalar_one_or_none()
    # One generic error for both unknown-user and bad-password paths so the
    # endpoint never becomes a tenant/user enumeration oracle.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return LoginResponse(
        access_token=create_access_token(user.id, user.business_id, user.branch_id),
        user=AuthenticatedUser(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            business_id=str(user.business_id),
            branch_id=str(user.branch_id) if user.branch_id else None,
        ),
    )


@router.get("/me")
async def me(claims: Claims) -> dict:
    """Return the verified JWT claims for the current principal."""
    return claims
