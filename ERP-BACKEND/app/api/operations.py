"""Tenant-scoped operational read models for the ERP workspace."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.authorization import permission_dependency
from app.db.session import get_db_session
from app.models.erp import Customer, Invoice, Product, StockBalance, Warehouse
from app.models.identity import Branch, Business

router = APIRouter(tags=["operations"])


def _tenant_id(claims: Claims) -> UUID:
    try:
        return UUID(claims["business_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tenant identity") from exc


def _branch_scope(claims: Claims, requested: UUID | None) -> UUID | None:
    assigned = claims.get("branch_id")
    if assigned:
        assigned_id = UUID(str(assigned))
        if requested is not None and requested != assigned_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch access denied")
        return assigned_id
    return requested


@router.get("/context", summary="Current business, branch and warehouse context")
async def get_business_context(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    business_id = _tenant_id(claims)
    business = await session.scalar(
        select(Business).where(Business.id == business_id, Business.active.is_(True))
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    branch_id = _branch_scope(claims, None)
    branch_stmt = select(Branch).where(
        Branch.business_id == business_id,
        Branch.active.is_(True),
    )
    if branch_id is not None:
        branch_stmt = branch_stmt.where(Branch.id == branch_id)
    branches = list((await session.scalars(branch_stmt.order_by(Branch.name))).all())
    branch_ids = [branch.id for branch in branches]

    warehouses = []
    if branch_ids:
        warehouse_stmt = select(Warehouse).where(
            Warehouse.branch_id.in_(branch_ids),
            Warehouse.active.is_(True),
        ).order_by(Warehouse.name)
        warehouses = list((await session.scalars(warehouse_stmt)).all())

    return {
        "business": {
            "id": str(business.id),
            "name": business.name,
            "code": business.code,
            "currency": business.default_currency,
            "timezone": business.timezone,
            "locale": business.locale,
        },
        "branches": [
            {"id": str(item.id), "code": item.code, "name": item.name, "address": item.address}
            for item in branches
        ],
        "warehouses": [
            {"id": str(item.id), "branch_id": str(item.branch_id), "code": item.code, "name": item.name}
            for item in warehouses
        ],
    }


@router.get("/inventory/stock", summary="Tenant-scoped stock balances")
async def list_stock_balances(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    branch_id: UUID | None = None,
    warehouse_id: UUID | None = None,
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _auth: dict = Depends(permission_dependency("products.manage")),
) -> dict:
    business_id = _tenant_id(claims)
    scoped_branch = _branch_scope(claims, branch_id)

    conditions = [
        Product.business_id == business_id,
        Product.active.is_(True),
        Warehouse.active.is_(True),
    ]
    if scoped_branch is not None:
        conditions.append(Product.branch_id == scoped_branch)
    if warehouse_id is not None:
        conditions.append(Warehouse.id == warehouse_id)
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(or_(Product.name.ilike(pattern), Product.sku.ilike(pattern)))

    join_condition = and_(
        StockBalance.warehouse_id == Warehouse.id,
        StockBalance.product_id == Product.id,
    )
    stmt = (
        select(Product, Warehouse, StockBalance.quantity)
        .join(Warehouse, Warehouse.branch_id == Product.branch_id)
        .outerjoin(StockBalance, join_condition)
        .where(*conditions)
        .order_by(Product.name, Warehouse.name)
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).all()
    count_stmt = (
        select(func.count())
        .select_from(Product)
        .join(Warehouse, Warehouse.branch_id == Product.branch_id)
        .outerjoin(StockBalance, join_condition)
        .where(*conditions)
    )
    total = await session.scalar(count_stmt) or 0

    return {
        "items": [
            {
                "product_id": str(product.id),
                "sku": product.sku,
                "product": product.name,
                "unit": product.unit,
                "sale_price": str(product.sale_price),
                "min_stock": str(product.min_stock),
                "warehouse_id": str(warehouse.id),
                "warehouse": warehouse.name,
                "branch_id": str(product.branch_id),
                "quantity": str(quantity if quantity is not None else Decimal("0")),
                "status": (
                    "out_of_stock"
                    if (quantity is None or quantity <= 0)
                    else "low_stock"
                    if quantity <= product.min_stock
                    else "in_stock"
                ),
            }
            for product, warehouse, quantity in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total,
        "has_more": offset + len(rows) < total,
    }


@router.get("/sales", summary="Tenant-scoped sales history")
async def list_sales(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    branch_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _auth: dict = Depends(permission_dependency("sales.create")),
) -> dict:
    business_id = _tenant_id(claims)
    scoped_branch = _branch_scope(claims, branch_id)
    conditions = [Invoice.business_id == business_id]
    if scoped_branch is not None:
        conditions.append(Invoice.branch_id == scoped_branch)

    stmt = (
        select(Invoice, Customer.name)
        .outerjoin(Customer, Customer.id == Invoice.customer_id)
        .where(*conditions)
        .order_by(Invoice.created_at.desc(), Invoice.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).all()
    total = await session.scalar(
        select(func.count(Invoice.id)).where(*conditions)
    ) or 0

    return {
        "items": [
            {
                "id": str(invoice.id),
                "invoice_no": invoice.invoice_no,
                "customer_name": customer_name or "Walk-in",
                "status": invoice.status,
                "currency": invoice.currency,
                "total": str(invoice.total),
                "paid": str(invoice.paid),
                "balance": str(invoice.total - invoice.paid),
                "created_at": invoice.created_at.isoformat(),
            }
            for invoice, customer_name in rows
        ],
        "limit": limit,
        "offset": offset,
        "total": total,
        "has_more": offset + len(rows) < total,
    }


@router.get("/dashboard/summary", summary="Tenant-scoped monthly dashboard summary")
async def dashboard_summary(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    business_id = _tenant_id(claims)
    branch_id = _branch_scope(claims, None)
    business = await session.scalar(
        select(Business).where(Business.id == business_id, Business.active.is_(True))
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    try:
        local_now = datetime.now(ZoneInfo(business.timezone))
    except (ZoneInfoNotFoundError, ValueError):
        local_now = datetime.now(UTC)
    month_start = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)

    invoice_conditions = [
        Invoice.business_id == business_id,
        Invoice.currency == business.default_currency,
        Invoice.created_at >= month_start,
    ]
    product_conditions = [Product.business_id == business_id, Product.active.is_(True)]
    customer_conditions = [Customer.business_id == business_id, Customer.active.is_(True)]
    if branch_id is not None:
        invoice_conditions.append(Invoice.branch_id == branch_id)
        product_conditions.append(Product.branch_id == branch_id)
        customer_conditions.append(Customer.branch_id == branch_id)

    revenue = await session.scalar(
        select(func.coalesce(func.sum(Invoice.total), 0)).where(*invoice_conditions)
    ) or Decimal("0")
    order_count = await session.scalar(
        select(func.count(Invoice.id)).where(*invoice_conditions)
    ) or 0
    product_count = await session.scalar(
        select(func.count(Product.id)).where(*product_conditions)
    ) or 0
    customer_count = await session.scalar(
        select(func.count(Customer.id)).where(*customer_conditions)
    ) or 0

    stock_totals = (
        select(
            StockBalance.product_id.label("product_id"),
            func.sum(StockBalance.quantity).label("quantity"),
        )
        .join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
        .where(Warehouse.active.is_(True))
        .group_by(StockBalance.product_id)
        .subquery()
    )
    low_stock_stmt = (
        select(func.count(Product.id))
        .outerjoin(stock_totals, stock_totals.c.product_id == Product.id)
        .where(
            *product_conditions,
            func.coalesce(stock_totals.c.quantity, 0) <= Product.min_stock,
        )
    )
    if branch_id is not None:
        low_stock_stmt = low_stock_stmt.where(
            Product.branch_id == branch_id,
        )
    low_stock_count = await session.scalar(low_stock_stmt) or 0

    outstanding = await session.scalar(
        select(func.coalesce(func.sum(Invoice.total - Invoice.paid), 0)).where(
            Invoice.business_id == business_id,
            Invoice.currency == business.default_currency,
            Invoice.total > Invoice.paid,
            Invoice.status != "void",
            *([Invoice.branch_id == branch_id] if branch_id is not None else []),
        )
    ) or Decimal("0")

    return {
        "currency": business.default_currency,
        "timezone": business.timezone,
        "period": "month_to_date",
        "period_start": month_start.isoformat(),
        "sales_total": str(revenue),
        "orders_count": int(order_count),
        "products_count": int(product_count),
        "customers_count": int(customer_count),
        "low_stock_count": int(low_stock_count),
        "outstanding_balance": str(outstanding),
    }
