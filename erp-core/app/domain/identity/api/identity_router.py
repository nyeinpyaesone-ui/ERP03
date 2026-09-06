from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.domain.identity.service.identity_service import IdentityService
from app.domain.identity.schema.user import (
    UserCreate, UserUpdate, UserResponse, RoleCreate, RoleResponse, Token
)

router = APIRouter(prefix="/api/v1/identity", tags=["Identity & Access Management"])

def get_identity_service(db: AsyncSession = Depends(get_db)) -> IdentityService:
    return IdentityService(db)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, service: IdentityService = Depends(get_identity_service)):
    """Register a new user"""
    try:
        return await service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(email: str, password: str, service: IdentityService = Depends(get_identity_service)):
    """Authenticate user and return tokens"""
    result = await service.authenticate_user(email, password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user_id: int,  # Extracted from token via middleware
    service: IdentityService = Depends(get_identity_service)
):
    """Get current user profile"""
    try:
        return await service.get_user_profile(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_id: int,
    update_data: UserUpdate,
    service: IdentityService = Depends(get_identity_service)
):
    """Update current user profile"""
    try:
        return await service.update_user(user_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(service: IdentityService = Depends(get_identity_service)):
    """List all roles"""
    return await service.get_all_roles()

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    service: IdentityService = Depends(get_identity_service)
):
    """Create a new role"""
    try:
        return await service.create_role(role_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/permissions")
async def list_permissions(service: IdentityService = Depends(get_identity_service)):
    """List all permissions"""
    return await service.get_all_permissions()
