"""Master-data catalog service: products, customers and suppliers.

All reads and writes are tenant-scoped by ``business_id``; uniqueness is
enforced at the database level (per-tenant code/SKU) and surfaced through
the typed :class:`ConflictError` contract instead of raw driver errors.
Write helpers flush but never commit: callers own the transaction boundary
(``session.begin()`` in tests/services, autocommit-on-close in routers).
"""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import Page
from app.models.erp import Customer, Product, Supplier


def _ensure_branch_scope(claims: dict, branch_id: UUID) -> None:
    """Reject writes targeting a branch outside the caller's grant."""
    claim_branch = claims.get("branch_id")
    if claim_branch and str(branch_id) != str(claim_branch):
        raise ForbiddenError("Branch access denied")


async def create_product(
    session: AsyncSession,
    *,
    business_id: UUID,
    branch_id: UUID,
    sku: str,
    name: str,
    sale_price: Decimal,
    cost_price: Decimal = Decimal("0"),
    unit: str = "pcs",
    barcode: str | None = None,
    min_stock: Decimal = Decimal("0"),
) -> Product:
    """Register an active product within one tenant scope."""
    product = Product(
        id=uuid4(),
        business_id=business_id,
        branch_id=branch_id,
        sku=sku,
        barcode=barcode,
        name=name,
        unit=unit,
        sale_price=sale_price,
        cost_price=cost_price,
        min_stock=min_stock,
        active=True,
    )
    async with session.begin_nested():
        session.add(product)
        try:
            await session.flush()
        except IntegrityError as exc:
            raise ConflictError("Product SKU already exists for this business") from exc
    return product


async def list_products(
    session: AsyncSession,
    *,
    business_id: UUID,
    search: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Page:
    """Paginated product listing scoped to one business."""
    conditions = [Product.business_id == business_id]
    if not include_inactive:
        conditions.append(Product.active.is_(True))
    if search:
        pattern = f"%{search}%"
        conditions.append(or_(Product.name.ilike(pattern), Product.sku.ilike(pattern)))

    total = await session.scalar(select(func.count(Product.id)).where(*conditions)) or 0
    rows = await session.execute(
        select(Product)
        .where(*conditions)
        .order_by(Product.created_at, Product.id)
        .limit(limit)
        .offset(offset)
    )
    return Page(items=list(rows.scalars().all()), limit=limit, offset=offset, total=total)


async def set_product_active(
    session: AsyncSession, *, business_id: UUID, product_id: UUID, active: bool
) -> Product:
    """Activate or deactivate a product without deleting its history."""
    product = await session.scalar(
        select(Product).where(Product.id == product_id, Product.business_id == business_id)
    )
    if product is None:
        raise NotFoundError("Product not found")
    product.active = active
    await session.flush()
    return product


async def create_customer(
    session: AsyncSession,
    *,
    claims: dict,
    business_id: UUID,
    branch_id: UUID,
    code: str,
    name: str,
    phone: str | None = None,
    credit_limit: Decimal = Decimal("0"),
) -> Customer:
    """Register a walk-in account for one branch of the tenant."""
    _ensure_branch_scope(claims, branch_id)
    customer = Customer(
        id=uuid4(),
        business_id=business_id,
        branch_id=branch_id,
        code=code,
        name=name,
        phone=phone,
        credit_limit=credit_limit,
        active=True,
    )
    async with session.begin_nested():
        session.add(customer)
        try:
            await session.flush()
        except IntegrityError as exc:
            raise ConflictError("Customer code already exists for this business") from exc
    return customer


async def list_customers(
    session: AsyncSession,
    *,
    business_id: UUID,
    search: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Page:
    """Paginated customer listing scoped to one business."""
    conditions = [Customer.business_id == business_id]
    if not include_inactive:
        conditions.append(Customer.active.is_(True))
    if search:
        pattern = f"%{search}%"
        conditions.append(or_(Customer.name.ilike(pattern), Customer.code.ilike(pattern)))

    total = await session.scalar(select(func.count(Customer.id)).where(*conditions)) or 0
    rows = await session.execute(
        select(Customer)
        .where(*conditions)
        .order_by(Customer.created_at, Customer.id)
        .limit(limit)
        .offset(offset)
    )
    return Page(items=list(rows.scalars().all()), limit=limit, offset=offset, total=total)


async def create_supplier(
    session: AsyncSession,
    *,
    claims: dict,
    business_id: UUID,
    branch_id: UUID,
    code: str,
    name: str,
    phone: str | None = None,
) -> Supplier:
    """Register a supplier/payable account for the tenant."""
    _ensure_branch_scope(claims, branch_id)
    supplier = Supplier(
        id=uuid4(),
        business_id=business_id,
        branch_id=branch_id,
        code=code,
        name=name,
        phone=phone,
        payable_balance=Decimal("0"),
        active=True,
    )
    async with session.begin_nested():
        session.add(supplier)
        try:
            await session.flush()
        except IntegrityError as exc:
            raise ConflictError("Supplier code already exists for this business") from exc
    return supplier


async def list_suppliers(
    session: AsyncSession,
    *,
    business_id: UUID,
    search: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Page:
    """Paginated supplier listing scoped to one business."""
    conditions = [Supplier.business_id == business_id]
    if not include_inactive:
        conditions.append(Supplier.active.is_(True))
    if search:
        pattern = f"%{search}%"
        conditions.append(or_(Supplier.name.ilike(pattern), Supplier.code.ilike(pattern)))

    total = await session.scalar(select(func.count(Supplier.id)).where(*conditions)) or 0
    rows = await session.execute(
        select(Supplier)
        .where(*conditions)
        .order_by(Supplier.created_at, Supplier.id)
        .limit(limit)
        .offset(offset)
    )
    return Page(items=list(rows.scalars().all()), limit=limit, offset=offset, total=total)
