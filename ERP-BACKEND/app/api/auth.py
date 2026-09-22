from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, current_claims, verify_password
from app.db.session import get_db_session
from app.models.identity import Business, User

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    business_code: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


@router.post("/login")
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> dict:
    result = await session.execute(select(User).join(Business, Business.id == User.business_id).where(Business.code == payload.business_code, User.email == payload.email.lower(), User.active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {
        "access_token": create_access_token(user.id, user.business_id, user.branch_id),
        "token_type": "bearer",
        "user": {"id": str(user.id), "email": user.email, "display_name": user.display_name, "business_id": str(user.business_id), "branch_id": str(user.branch_id) if user.branch_id else None},
    }


@router.get("/me")
async def me(claims: dict = Depends(current_claims)) -> dict:
    return claims
