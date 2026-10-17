"""Authentication request/response contracts."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    business_code: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class AuthenticatedUser(BaseModel):
    id: str
    email: str
    display_name: str
    business_id: str
    branch_id: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthenticatedUser
