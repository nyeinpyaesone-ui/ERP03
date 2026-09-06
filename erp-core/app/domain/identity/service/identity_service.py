from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.identity.repository.user_repository import UserRepository, RoleRepository, PermissionRepository
from app.domain.identity.schema.user import UserCreate, UserUpdate, RoleCreate, UserResponse, RoleResponse
from app.domain.identity.service.auth_service import get_password_hash, create_access_token, create_refresh_token
from datetime import timedelta
from app.core.config import settings

class IdentityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.perm_repo = PermissionRepository(db)
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        # Check if user exists
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")
        
        existing = await self.user_repo.get_by_username(user_data.username)
        if existing:
            raise ValueError("Username already taken")
        
        # Create user
        hashed_pw = get_password_hash(user_data.password)
        user = await self.user_repo.create(user_data, hashed_pw)
        
        # Assign default role
        default_role = await self.role_repo.get_by_name("user")
        if default_role:
            from app.domain.identity.model.user import UserRole
            ur = UserRole(user_id=user.id, role_id=default_role.id)
            self.db.add(ur)
            await self.db.flush()
        
        return UserResponse.model_validate(user)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        from app.domain.identity.service.auth_service import verify_password
        
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(data={"user_id": user.id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }
    
    async def get_user_profile(self, user_id: int) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return UserResponse.model_validate(user)
    
    async def update_user(self, user_id: int, update_data: UserUpdate) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        updated = await self.user_repo.update(user, update_data)
        return UserResponse.model_validate(updated)
    
    async def create_role(self, role_data: RoleCreate) -> RoleResponse:
        existing = await self.role_repo.get_by_name(role_data.name)
        if existing:
            raise ValueError("Role already exists")
        
        role = await self.role_repo.create(role_data)
        return RoleResponse.model_validate(role)
    
    async def get_all_roles(self) -> List[RoleResponse]:
        roles = await self.role_repo.get_all()
        return [RoleResponse.model_validate(r) for r in roles]
    
    async def get_all_permissions(self) -> List[dict]:
        perms = await self.perm_repo.get_all()
        return [{"id": p.id, "name": p.name, "resource": p.resource, "action": p.action} for p in perms]
