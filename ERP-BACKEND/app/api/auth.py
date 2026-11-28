"""Authentication endpoints: ERP credentials and optional Supabase identity linking."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_supabase_access_token,
)
from app.db.session import get_db_session
from app.models.erp import Warehouse
from app.models.identity import Branch, Business, Permission, Role, User, role_permissions, user_roles
from app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.supabase_identity import link_supabase_identity as link_identity

router = APIRouter(prefix="/auth", tags=["authentication"])


class SupabaseLinkRequest(BaseModel):
    access_token: str = Field(min_length=32, max_length=8192)


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
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
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
    return claims


@router.post("/supabase/link")
async def link_supabase_identity(
    payload: SupabaseLinkRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Explicitly link a verified Supabase user to the already-authenticated ERP user."""
    if claims.get("auth_provider") == "supabase":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign in with existing ERP03 credentials before linking Supabase",
        )
    try:
        erp_user_id = UUID(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ERP identity"
        ) from exc

    erp_user = await session.scalar(
        select(User).where(User.id == erp_user_id, User.active.is_(True))
    )
    if erp_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ERP user is inactive")

    identity = await verify_supabase_access_token(payload.access_token)
    try:
        supabase_user_id = UUID(identity["id"])
        supabase_email = identity["email"]
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase identity"
        ) from exc

    await link_identity(session, erp_user, supabase_user_id, supabase_email)
    return {"status": "linked", "user_id": str(erp_user.id)}


@router.post("/register", response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """Register a new business and an owner user through the existing ERP identity system."""
    existing_business = await session.scalar(
        select(Business).where(Business.code == payload.business_code.strip())
    )
    if existing_business:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Business code already exists"
        )
    existing_user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    async with session.begin():
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
        branch = Branch(
            id=uuid4(),
            business_id=business.id,
            name="Main Branch",
            code="MAIN",
            active=True,
        )
        session.add(branch)
        await session.flush()
        warehouse = Warehouse(
            id=uuid4(),
            branch_id=branch.id,
            code="MAIN",
            name="Main Warehouse",
            active=True,
        )
        session.add(warehouse)
        user = User(
            id=uuid4(),
            business_id=business.id,
            branch_id=branch.id,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            active=True,
        )
        session.add(user)
        await session.flush()

        perm_codes = {
            "sales.create",
            "products.manage",
            "customers.manage",
            "suppliers.manage",
            "purchases.receive",
        }
        permissions = (
            await session.scalars(select(Permission).where(Permission.code.in_(perm_codes)))
        ).all()
        perm_by_code = {p.code: p for p in permissions}
        missing = [code for code in perm_codes if code not in perm_by_code]
        if missing:
            for code in missing:
                session.add(Permission(id=uuid4(), code=code, description=f"{code} permission"))
            await session.flush()
            permissions = (
                await session.scalars(select(Permission).where(Permission.code.in_(perm_codes)))
            ).all()
            perm_by_code = {p.code: p for p in permissions}

        owner_role = Role(id=uuid4(), business_id=business.id, name="Owner")
        session.add(owner_role)
        await session.flush()
        for code in perm_codes:
            await session.execute(
                role_permissions.insert().values(
                    role_id=owner_role.id, permission_id=perm_by_code[code].id
                )
            )
        await session.execute(user_roles.insert().values(user_id=user.id, role_id=owner_role.id))

    return RegisterResponse(
        business_id=str(business.id),
        user_id=str(user.id),
        message="Registration successful",
    )
