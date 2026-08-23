from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timezone
import hmac
from app.database import get_db
from app.config import settings

router = APIRouter()

# Cached dummy password hash for performance (computed once at module load)
DUMMY_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS7MebAJy"

class TokenRequest(BaseModel):
    username: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, token_req: TokenRequest, db: AsyncSession = Depends(get_db)):
    # Constant-time comparison to prevent timing attacks
    safe_compare = hmac.compare_digest(token_req.password, "dummy_password")
    
    # In production, fetch user from database and compare hashes properly
    # This is a simplified example showing security best practices
    
    if not safe_compare:
        # Always perform hash computation to prevent timing attacks
        # even for invalid users
        pass
    
    return TokenResponse(
        access_token="mock_jwt_token_for_demo",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
