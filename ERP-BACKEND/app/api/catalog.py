"""Master-data catalog endpoints: products, customers and suppliers."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Claims
from app.core.authorization import permission_dependency
from app.core.pagination import Page
from app.db.session import get_db_session
from app.schemas.catalog import (
    ActiveFlagRequest,
    CustomerCreateRequest,
    CustomerResponse,
    PageResponse,
    ProductCreateRequest,
    ProductResponse,
    SupplierCreateRequest,
    SupplierResponse,
)
from app.services import catalog

router = APIRouter(tags=["catalog"])

_LIMIT = Annotated[int, Query(ge=1, le=200)]
_OFFSET = Annotated[int, Query(ge=0)]


def _page_payload(page: Page, model) -> PageResponse:
    return PageResponse(
        items=[model.model_validate(item).model_dump(mode="json") for item in page.items],
        limit=page.limit,
        offset=page.offset,
        total=page.total,
        has_more=page.has_more,
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreateRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    _auth: dict = Depends(permission_dependency("products.manage")),
) -> ProductResponse:
    product = await catalog.create_product(
        session,
        business_id=UUID(claims["business_id"]),
        **payload.model_dump(),
    )
    return ProductResponse.model_validate(product)


@router.get("/products", response_model=PageResponse)
async def list_products(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    search: Annotated[str | None, Query(max_length=240)] = None,
    include_inactive: Annotated[bool, Query()] = False,
    limit: _LIMIT = 50,
    offset: _OFFSET = 0,
    _auth: dict = Depends(permission_dependency("products.manage")),
) -> PageResponse:
    page = await catalog.list_products(
        session,
        business_id=UUID(claims["business_id"]),
        search=search,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    return _page_payload(page, ProductResponse)


@router.patch("/products/{product_id}/active", response_model=ProductResponse)
async def set_product_active(
    product_id: UUID,
    payload: ActiveFlagRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    _auth: dict = Depends(permission_dependency("products.manage")),
) -> ProductResponse:
    product = await catalog.set_product_active(
        session,
        business_id=UUID(claims["business_id"]),
        product_id=product_id,
        active=payload.active,
    )
    return ProductResponse.model_validate(product)


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    payload: CustomerCreateRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    _auth: dict = Depends(permission_dependency("customers.manage")),
) -> CustomerResponse:
    customer = await catalog.create_customer(
        session,
        claims=claims,
        business_id=UUID(claims["business_id"]),
        **payload.model_dump(),
    )
    return CustomerResponse.model_validate(customer)


@router.get("/customers", response_model=PageResponse)
async def list_customers(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    search: Annotated[str | None, Query(max_length=200)] = None,
    include_inactive: Annotated[bool, Query()] = False,
    limit: _LIMIT = 50,
    offset: _OFFSET = 0,
    _auth: dict = Depends(permission_dependency("customers.manage")),
) -> PageResponse:
    page = await catalog.list_customers(
        session,
        business_id=UUID(claims["business_id"]),
        search=search,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    return _page_payload(page, CustomerResponse)


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    payload: SupplierCreateRequest,
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    _auth: dict = Depends(permission_dependency("suppliers.manage")),
) -> SupplierResponse:
    supplier = await catalog.create_supplier(
        session,
        claims=claims,
        business_id=UUID(claims["business_id"]),
        **payload.model_dump(),
    )
    return SupplierResponse.model_validate(supplier)


@router.get("/suppliers", response_model=PageResponse)
async def list_suppliers(
    claims: Claims,
    session: AsyncSession = Depends(get_db_session),
    search: Annotated[str | None, Query(max_length=200)] = None,
    include_inactive: Annotated[bool, Query()] = False,
    limit: _LIMIT = 50,
    offset: _OFFSET = 0,
    _auth: dict = Depends(permission_dependency("suppliers.manage")),
) -> PageResponse:
    page = await catalog.list_suppliers(
        session,
        business_id=UUID(claims["business_id"]),
        search=search,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    return _page_payload(page, SupplierResponse)
