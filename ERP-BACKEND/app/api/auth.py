"""User registration endpoint."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.security import hash_password
from app.db.session import get_db_session
from app.models.identity import Business, User, Role, Permission, role_permissions, user_roles
from app.schemas.auth import RegisterRequest, RegisterResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """Register a new business and admin user.

    Creates a business, an owner user, assigns the Owner role with default
    permissions, and returns a JWT access token. This is a self-service
    onboarding endpoint — no prior authentication required.
    """
    # Check if business already exists
    existing_business = await session.scalar(
        select(Business).where(Business.code == payload.business_code.strip())
    )
    if existing_business:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business code already exists",
        )

    # Check if user email already exists
    existing_user = await session.scalar(
        select(User).where(User.email == payload.email.lower())
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    async with session.begin():
        # Create business
        business = Business(
            id=uuid4(),
            name=payload.business_name or payload.business_code,
            code=payload.business_code.strip(),
            default_currency=payload.default_currency or "MMK",
            timezone=payload.timezone or "Asia/Yangon",
            locale=payload.locale or "my-MM",
            active=True,
        )
        session.add(business)
        await session.flush()

        # Create owner user
        user = User(
            id=uuid4(),
            business_id=business.id,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            active=True,
        )
        session.add(user)
        await session.flush()

        # Ensure permissions exist
        perm_codes = {"sales.create", "products.manage", "customers.manage", "suppliers.manage", "purchases.receive"}
        permissions = (
            await session.scalars(
                select(Permission).where(Permission.code.in_(perm_codes))
            )
        ).all()
        perm_by_code = {p.code: p for p in permissions}

        missing = [c for c in perm_codes if c not in perm_by_code]
        if missing:
            for code in missing:
                session.add(Permission(id=uuid4(), code=code, description=f"{code} permission"))
            await session.flush()
            permissions = (
                await session.scalars(
                    select(Permission).where(Permission.code.in_(perm_codes))
                )
            ).all()
            perm_by_code = {p.code: p for p in permissions}

        # Create Owner role
        owner_role = Role(
            id=uuid4(),
            business_id=business.id,
            name="Owner",
        )
        session.add(owner_role)
        await session.flush()

        # Assign permissions to Owner role
        for code in perm_codes:
            session.execute(
                role_permissions.insert().values(
                    role_id=owner_role.id,
                    permission_id=perm_by_code[code].id,
                )
            )

        # Assign Owner role to user
        session.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=owner_role.id,
            )
        )

    return RegisterResponse(
        business_id=str(business.id),
        user_id=str(user.id),
        message="Registration successful",
    )
