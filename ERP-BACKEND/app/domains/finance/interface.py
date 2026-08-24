from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.core.module_registry import ModuleDescriptor, registry
from app.api_boundary.boundary import boundary
from . import application


class InvoiceItemCreate(BaseModel):
    product_id: Optional[int] = None
    description: str
    quantity: float = 1
    unit_price: float


class InvoiceCreate(BaseModel):
    invoice_number: str
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    issue_date: date
    due_date: date
    tax_rate: float = 0
    notes: Optional[str] = None
    terms: Optional[str] = None
    items: List[InvoiceItemCreate]


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str
    payment_date: date


def build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/invoices")
    def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
        try:
            invoice = application.create_invoice(
                db,
                invoice_number=data.invoice_number,
                contact_id=data.contact_id,
                company_id=data.company_id,
                issue_date=data.issue_date,
                due_date=data.due_date,
                tax_rate=data.tax_rate,
                notes=data.notes,
                terms=data.terms,
                items=[item.dict() for item in data.items],
            )
            return {"id": invoice.id, "invoice_number": invoice.invoice_number}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/payments")
    def record_payment(data: PaymentCreate, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
        try:
            payment = application.record_payment(
                db,
                invoice_id=data.invoice_id,
                amount=data.amount,
                payment_method=data.payment_method,
                payment_date=data.payment_date,
            )
            return {"id": payment.id, "amount": payment.amount}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/invoices/{invoice_id}")
    def get_invoice(invoice_id: int, db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):
        invoice = application.get_invoice(db, invoice_id=invoice_id)
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    @router.get("/invoices")
    def list_invoices(status: Optional[str] = None, contact_id: Optional[int] = None,
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
        return application.list_invoices(db, status=status, contact_id=contact_id)

    @router.get("/dashboard")
    def dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
        return application.dashboard(db)

    # Register with module registry
    registry.register(ModuleDescriptor(
        name="finance",
        version="1.0.0",
        router_factory=build_router,
    ))

    return router
