"""Authentication endpoints: credential exchange, registration, and current-principal lookup."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db_session
from app.models.identity import Business, Permission, Role, User, role_permissions, user_roles
from app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

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


@router.post("/register", response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """Register a business and its owner atomically.

    Registration returns the new identifiers. The client must call /auth/login
    with the supplied credentials to obtain an access token.
    User email addresses are unique within a business, matching the database
    constraint and the business-code-scoped login contract.
    """
    business_code = payload.business_code.strip()
    email = str(payload.email).lower()
    permission_codes = {
        "sales.create",
        "products.manage",
        "customers.manage",
        "suppliers.manage",
        "purchases.receive",
    }

    try:
        async with session.begin():
            # Keep all reads and writes within one explicit transaction.
            # A query before begin() triggers AsyncSession autobegin.
            existing_business = await session.scalar(
                select(Business.id).where(Business.code == business_code)
            )
            if existing_business is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Business code already exists",
                )

            business = Business(
                id=uuid4(),
                name=payload.business_name or business_code,
                code=business_code,
                default_currency=payload.default_currency or "MMK",
                timezone=payload.timezone or "Asia/Yangon",
                locale=payload.locale or "my-MM",
                active=True,
            )
            session.add(business)
            await session.flush()

            user = User(
                id=uuid4(),
                business_id=business.id,
                email=email,
                password_hash=hash_password(payload.password),
                display_name=payload.display_name,
                active=True,
            )
            session.add(user)
            await session.flush()

            # Permission rows are migration-owned reference data. Do not
            # mutate the shared catalogue during an individual registration.
            permissions = (
                await session.scalars(
                    select(Permission).where(Permission.code.in_(permission_codes))
                )
            ).all()
            permissions_by_code = {permission.code: permission for permission in permissions}
            missing = permission_codes - permissions_by_code.keys()
            if missing:
                missing_list = ", ".join(sorted(missing))
                raise RuntimeError(f"Missing permission catalog entries: {missing_list}")

            owner_role = Role(
                id=uuid4(),
                business_id=business.id,
                name="Owner",
            )
            session.add(owner_role)
            await session.flush()

            for code in sorted(permission_codes):
                await session.execute(
                    role_permissions.insert().values(
                        role_id=owner_role.id,
                        permission_id=permissions_by_code[code].id,
                    )
                )

            await session.execute(
                user_roles.insert().values(
                    user_id=user.id,
                    role_id=owner_role.id,
                )
            )
    except IntegrityError as exc:
        # A concurrent request may lose the unique business-code race after
        # both requests pass the pre-insert check. Translate that known race
        # into the same 409 response; do not mask unrelated integrity errors.
        await session.rollback()
        duplicate_business = await session.scalar(
            select(Business.id).where(Business.code == business_code)
        )
        if duplicate_business is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Business code already exists",
            ) from exc
        raise

    return RegisterResponse(
        business_id=str(business.id),
        user_id=str(user.id),
        message="Registration successful",
    )
