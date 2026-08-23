from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.domain.identity.model.user import User, Role, Permission, UserRole, RolePermission
from app.domain.identity.schema.user import UserCreate, UserUpdate, RoleCreate

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def update(self, user: User, update_data: UserUpdate) -> User:
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user: User) -> bool:
        await self.db.delete(user)
        return True
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, role_id: int) -> Optional[Role]:
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(self, role_data: RoleCreate) -> Role:
        role = Role(
            name=role_data.name,
            description=role_data.description,
        )
        self.db.add(role)
        await self.db.flush()
        
        # Assign permissions
        if role_data.permission_ids:
            for perm_id in role_data.permission_ids:
                rp = RolePermission(role_id=role.id, permission_id=perm_id)
                self.db.add(rp)
        
        await self.db.refresh(role)
        return role
    
    async def get_all(self) -> List[Role]:
        result = await self.db.execute(
            select(Role).options(selectinload(Role.permissions))
        )
        return list(result.scalars().unique().all())

class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, perm_id: int) -> Optional[Permission]:
        result = await self.db.execute(
            select(Permission).where(Permission.id == perm_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Permission]:
        result = await self.db.execute(
            select(Permission).where(Permission.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[Permission]:
        result = await self.db.execute(select(Permission))
        return list(result.scalars().all())
    
    async def create(self, name: str, resource: str, action: str, description: str = None) -> Permission:
        perm = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description,
        )
        self.db.add(perm)
        await self.db.flush()
        await self.db.refresh(perm)
        return perm
