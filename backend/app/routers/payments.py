from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import stripe

from app.database import get_db
from app.models import Invoice, Payment
from app.auth import get_current_user
from app.config import settings
from app.services.activity_log import log_activity

router = APIRouter()

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentIntentRequest(BaseModel):
    invoice_id: int
    amount: Optional[float] = None

@router.post("/create-intent")
def create_payment_intent(
    data: PaymentIntentRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe not configured")

    invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    amount = data.amount or float(invoice.total - (invoice.amount_paid or 0))
    amount_cents = int(amount * 100)

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={"invoice_id": invoice.id, "invoice_number": invoice.invoice_number}
        )

        invoice.stripe_payment_intent_id = intent.id
        db.commit()

        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": amount,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        invoice_id = intent["metadata"].get("invoice_id")

        if invoice_id:
            invoice = db.query(Invoice).filter(Invoice.id == int(invoice_id)).first()
            if invoice:
                amount = intent["amount_received"] / 100
                payment = Payment(
                    invoice_id=invoice.id,
                    amount=amount,
                    payment_method="stripe",
                    payment_date=datetime.now().date(),
                    stripe_payment_intent_id=intent["id"],
                    stripe_charge_id=intent["charges"]["data"][0]["id"] if intent.get("charges") else None,
                    status="completed"
                )
                db.add(payment)
                invoice.amount_paid = (invoice.amount_paid or 0) + amount
                if invoice.amount_paid >= invoice.total:
                    invoice.status = "paid"
                db.commit()

    return {"status": "success"}

from datetime import datetime

