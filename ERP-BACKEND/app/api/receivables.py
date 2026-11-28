"""Customer receivables and idempotent invoice collection endpoints."""

import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.validation import validate_idempotency_key
from app.core.authorization import permission_dependency
from app.db.session import get_db_session
from app.models.erp import Customer, Invoice, Payment

router = APIRouter(prefix="/receivables", tags=["receivables"])
CENT = Decimal("0.01")


class CollectionRequest(BaseModel):
    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    method: str = Field(min_length=1, max_length=32)
    currency: str = Field(min_length=3, max_length=3)
    reference: str | None = Field(default=None, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


def _branch_scope(claims: dict, requested: UUID | None) -> UUID | None:
    assigned = claims.get("branch_id")
    if assigned:
        assigned_id = UUID(str(assigned))
        if requested is not None and requested != assigned_id:
            raise HTTPException(status_code=403, detail="Branch access denied")
        return assigned_id
    return requested


def _fingerprint(payload: CollectionRequest) -> str:
    canonical = json.dumps(
        {
            "invoice_id": str(payload.invoice_id),
            "amount": str(payload.amount.quantize(CENT, rounding=ROUND_HALF_UP)),
            "method": payload.method.strip().lower(),
            "currency": payload.currency.strip().upper(),
            "reference": payload.reference,
            "note": payload.note,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.get("/outstanding")
async def list_outstanding_receivables(
    claims: dict = Depends(permission_dependency("sales.create")),
    session: AsyncSession = Depends(get_db_session),
    branch_id: UUID | None = None,
    customer_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    business_id = UUID(claims["business_id"])
    scoped_branch = _branch_scope(claims, branch_id)
    conditions = [
        Invoice.business_id == business_id,
        Invoice.customer_id.is_not(None),
        Invoice.total > Invoice.paid,
    ]
    if scoped_branch is not None:
        conditions.append(Invoice.branch_id == scoped_branch)
    if customer_id is not None:
        conditions.append(Invoice.customer_id == customer_id)

    statement = (
        select(Invoice, Customer.name)
        .join(
            Customer,
            and_(
                Customer.id == Invoice.customer_id,
                Customer.business_id == business_id,
                Customer.branch_id == Invoice.branch_id,
            ),
        )
        .where(*conditions)
        .order_by(Invoice.created_at.asc(), Invoice.id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(statement)).all()
    total = await session.scalar(
        select(func.count(Invoice.id))
        .join(
            Customer,
            and_(
                Customer.id == Invoice.customer_id,
                Customer.business_id == business_id,
                Customer.branch_id == Invoice.branch_id,
            ),
        )
        .where(*conditions)
    ) or 0
    outstanding = await session.scalar(
        select(func.coalesce(func.sum(Invoice.total - Invoice.paid), 0))
        .select_from(Invoice)
        .join(
            Customer,
            and_(
                Customer.id == Invoice.customer_id,
                Customer.business_id == business_id,
                Customer.branch_id == Invoice.branch_id,
            ),
        )
        .where(*conditions)
    ) or Decimal("0")

    return {
        "items": [
            {
                "invoice_id": str(invoice.id),
                "invoice_no": invoice.invoice_no,
                "customer_id": str(invoice.customer_id),
                "customer_name": customer_name,
                "currency": invoice.currency,
                "total": str(invoice.total),
                "paid": str(invoice.paid),
                "balance": str(invoice.total - invoice.paid),
                "created_at": invoice.created_at.isoformat(),
            }
            for invoice, customer_name in rows
        ],
        "total": total,
        "outstanding_total": str(outstanding),
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(rows) < total,
    }


@router.post("/collect", status_code=status.HTTP_201_CREATED)
async def collect_receivable(
    payload: CollectionRequest,
    claims: dict = Depends(permission_dependency("sales.create")),
    session: AsyncSession = Depends(get_db_session),
    x_idempotency_key: str | None = Header(default=None),
) -> dict:
    business_id = UUID(claims["business_id"])
    idempotency_key = validate_idempotency_key(x_idempotency_key)
    fingerprint = _fingerprint(payload)
    amount = payload.amount.quantize(CENT, rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be at least 0.01")
    method = payload.method.strip().lower()
    currency = payload.currency.strip().upper()

    async with session.begin():
        invoice = await session.scalar(
            select(Invoice)
            .where(
                Invoice.id == payload.invoice_id,
                Invoice.business_id == business_id,
            )
            .with_for_update()
        )
        if invoice is None or invoice.customer_id is None:
            raise HTTPException(status_code=404, detail="Customer invoice not found")
        scoped_branch = _branch_scope(claims, invoice.branch_id)
        if scoped_branch is not None and invoice.branch_id != scoped_branch:
            raise HTTPException(status_code=403, detail="Branch access denied")
        if invoice.currency.upper() != currency:
            raise HTTPException(status_code=422, detail="Collection currency must match invoice")
        existing = await session.scalar(
            select(Payment).where(
                Payment.business_id == business_id,
                Payment.branch_id == invoice.branch_id,
                Payment.invoice_id == invoice.id,
                Payment.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "IDEMPOTENCY_KEY_REUSED",
                        "message": "Idempotency key was already used for a different collection",
                    },
                )
            return {
                "invoice_id": str(invoice.id),
                "payment_id": str(existing.id),
                "total": str(invoice.total),
                "paid": str(invoice.paid),
                "balance": str(invoice.total - invoice.paid),
                "idempotent_replay": True,
            }

        balance = invoice.total - invoice.paid
        if balance <= 0:
            raise HTTPException(status_code=409, detail="Invoice is already settled")
        if amount > balance:
            raise HTTPException(status_code=422, detail="Collection exceeds outstanding balance")

        payment = Payment(
            business_id=business_id,
            branch_id=invoice.branch_id,
            invoice_id=invoice.id,
            method=method,
            currency=currency,
            amount=amount,
            reference=payload.reference,
            note=payload.note,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )
        session.add(payment)
        invoice.paid = (invoice.paid + amount).quantize(CENT, rounding=ROUND_HALF_UP)
        invoice.status = "paid" if invoice.paid == invoice.total else "partial"
        await session.flush()

        return {
            "invoice_id": str(invoice.id),
            "payment_id": str(payment.id),
            "total": str(invoice.total),
            "paid": str(invoice.paid),
            "balance": str(invoice.total - invoice.paid),
            "idempotent_replay": False,
        }
