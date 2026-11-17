"""Authentication request/response contracts."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    business_code: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class RegisterRequest(BaseModel):
    business_code: str = Field(min_length=1, max_length=64)
    business_name: str | None = Field(None, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=200)
    default_currency: str = Field("MMK", min_length=3, max_length=3)
    timezone: str = Field("Asia/Yangon", max_length=64)
    locale: str = Field("my-MM", max_length=16)


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


class RegisterResponse(BaseModel):
    business_id: str
    user_id: str
    message: str
