"""Versioned runtime boundary used by external AI/integration clients."""

from __future__ import annotations

import hashlib
import json
import uuid
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import decode_token
from app.config import settings
from app.database import get_db
from app.models import User, Company, Contact, Deal, Product
from app.services.activity_log import log_activity
from app.integration_runtime.models import IntegrationCommand, PurchaseOrder, PurchaseOrderApproval
from app.adapters.integration import CRMAdapter, InventoryAdapter

router = APIRouter(prefix="/integration/v1", tags=["ERP-AI Integration v1"])
bearer = HTTPBearer(auto_error=False)


# ============================================================================
# Integration Contract Schemas (mirroring INTEGRATION/contracts)
# ============================================================================

class CustomerResponse(BaseModel):
    """Customer response matching integration contract."""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None
    created_at: Any
    updated_at: Optional[Any] = None
    created_by: Optional[int] = None
    tags: List[str] = []


class ContactResponse(BaseModel):
    """Contact response matching integration contract."""
    id: int
    customer_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None
    created_at: Any
    updated_at: Optional[Any] = None


class OpportunityResponse(BaseModel):
    """Opportunity response matching integration contract."""
    id: int
    customer_id: int
    title: str
    description: Optional[str] = None
    stage: str
    value: float
    currency: str = "USD"
    probability: int = 0
    expected_close_date: Optional[Any] = None
    actual_close_date: Optional[Any] = None
    owner_id: Optional[int] = None
    created_at: Any
    updated_at: Optional[Any] = None
    tags: List[str] = []


class ProductResponse(BaseModel):
    """Product response matching integration contract."""
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: float = 0.0
    cost_price: Optional[float] = None
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    quantity_available: int = 0
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    unit_of_measure: str = "unit"
    is_active: bool = True
    created_at: Any
    updated_at: Optional[Any] = None
    tags: List[str] = []


class CommandRequest(BaseModel):
    command_id: uuid.UUID
    command_type: str = Field(pattern=r"^purchase_order_(approve|reject)$")
    requested_by: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]


class CommandAccepted(BaseModel):
    command_id: uuid.UUID
    status: str
    correlation_id: str
    result: dict[str, Any] | None = None


class ServiceContext(BaseModel):
    actor_id: int
    subject: str


def require_service(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> ServiceContext:
    """
    Authenticate a service principal and return its active actor context.
    
    Parameters:
        credentials: Bearer authorization credentials containing the service token.
    
    Returns:
        ServiceContext: The authenticated service actor ID and token subject.
    
    Raises:
        HTTPException: If authentication fails, the token claims are invalid, or the service actor is inactive or unknown.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing service authentication")
    try:
        payload = decode_token(credentials.credentials)
    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid service token") from exc

    if payload.get("service") is not True:
        raise HTTPException(status_code=403, detail="Service principal required")
    if payload.get("iss") != settings.INTEGRATION_SERVICE_ISSUER:
        raise HTTPException(status_code=401, detail="Invalid service issuer")
    audience = payload.get("aud")
    if audience != settings.INTEGRATION_SERVICE_AUDIENCE:
        raise HTTPException(status_code=401, detail="Invalid service audience")

    actor_id = payload.get("actor_id")
    subject = payload.get("sub")
    if not isinstance(actor_id, int) or not subject:
        raise HTTPException(status_code=401, detail="Invalid service identity")

    actor = db.query(User).filter(User.id == actor_id, User.is_active.is_(True)).first()
    if actor is None:
        raise HTTPException(status_code=403, detail="Service actor is inactive or unknown")
    return ServiceContext(actor_id=actor.id, subject=str(subject))


def _payload_hash(command: CommandRequest) -> str:
    """
    Create a deterministic SHA-256 hash for a command payload.
    
    Parameters:
    	command (CommandRequest): The command payload to hash.
    
    Returns:
    	str: The hexadecimal SHA-256 digest of the canonicalized payload.
    """
    canonical = json.dumps(command.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_command_or_none(db: Session, key: str) -> IntegrationCommand | None:
    """Retrieve the integration command associated with an idempotency key.
    
    Parameters:
    	key (str): Idempotency key used to identify the command.
    
    Returns:
    	IntegrationCommand | None: The matching integration command, or `None` when no command exists for the key.
    """
    return db.query(IntegrationCommand).filter(IntegrationCommand.idempotency_key == key).first()


@router.get("/erp/purchase-orders/{po_id}")
def get_purchase_order(po_id: int, ctx: ServiceContext = Depends(require_service), db: Session = Depends(get_db)):
    """
    Retrieve a purchase order when the authenticated actor is authorized to view it.
    
    Parameters:
    	po_id (int): Identifier of the purchase order.
    
    Returns:
    	dict: The purchase order identifier, number, status, amount, and currency code.
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    actor = db.query(User).filter(User.id == ctx.actor_id).first()
    if actor is None:
        raise HTTPException(status_code=403, detail="Service actor not found")
    if actor.role not in {"admin", "superadmin", "approver", "second_approver"} and po.requester_id != actor.id:
        raise HTTPException(status_code=403, detail="Not authorized to view purchase order")

    return {"id": po.id, "po_number": po.po_number, "status": po.status, "amount": float(po.amount), "currency_code": po.currency_code}


# ============================================================================
# CRM Integration Endpoints (using contract-compatible schemas)
# ============================================================================

@router.get("/crm/customers", response_model=List[CustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """List customers in integration contract format."""
    query = db.query(Company)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    companies = query.offset(skip).limit(limit).all()
    return [CRMAdapter.company_to_customer(c) for c in companies]


@router.get("/crm/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """Get a specific customer in integration contract format."""
    company = db.query(Company).filter(Company.id == customer_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CRMAdapter.company_to_customer(company)


@router.get("/crm/contacts", response_model=List[ContactResponse])
def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """List contacts in integration contract format."""
    query = db.query(Contact)
    if customer_id:
        query = query.filter(Contact.company_id == customer_id)
    contacts = query.offset(skip).limit(limit).all()
    return [CRMAdapter.contact_to_contract(c) for c in contacts]


@router.get("/crm/opportunities", response_model=List[OpportunityResponse])
def list_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """
    List opportunities in the integration contract format.
    
    Parameters:
        customer_id (Optional[int]): Filter opportunities by customer.
        stage (Optional[str]): Filter opportunities by stage.
    
    Returns:
        list: The matching opportunities.
    """
    query = db.query(Deal)
    if customer_id:
        query = query.filter(Deal.company_id == customer_id)
    if stage:
        query = query.filter(Deal.stage == stage)
    deals = query.offset(skip).limit(limit).all()
    return [CRMAdapter.deal_to_opportunity(d) for d in deals]


# ============================================================================
# Inventory Integration Endpoints (using contract-compatible schemas)
# ============================================================================

@router.get("/inventory/products", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """
    List products in the integration contract format, with optional category and name filters.
    
    Parameters:
        skip (int): Number of products to skip.
        limit (int): Maximum number of products to return.
        category_id (Optional[int]): Category identifier used to filter products.
        search (Optional[str]): Case-insensitive text used to filter product names.
    
    Returns:
        list[ProductResponse]: The matching products in contract format.
    """
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    products = query.offset(skip).limit(limit).all()
    return [InventoryAdapter.product_to_contract(p) for p in products]


@router.get("/inventory/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """Get a specific product in integration contract format."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return InventoryAdapter.product_to_contract(product)


@router.get("/inventory/products/sku/{sku}", response_model=ProductResponse)
def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    ctx: ServiceContext = Depends(require_service),
):
    """
    Retrieve a product by its stock-keeping unit in the integration contract format.
    
    Parameters:
    	sku (str): The product's stock-keeping unit.
    
    Returns:
    	ProductResponse: The matching product.
    """
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return InventoryAdapter.product_to_contract(product)


@router.post("/erp/commands", response_model=CommandAccepted, status_code=202)
def submit_command(
    command: CommandRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=128),
    correlation_id: str | None = Header(None, alias="X-Correlation-ID", max_length=128),
    ctx: ServiceContext = Depends(require_service),
    db: Session = Depends(get_db),
):
    """
    Process a purchase-order approval or rejection command with idempotent handling.
    
    Parameters:
    	command (CommandRequest): Command containing the requested action, purchase order identifier, requester identity, and optional comment.
    	idempotency_key (str): Key used to prevent duplicate command processing.
    	correlation_id (str | None): Optional identifier for correlating the command with related operations.
    
    Returns:
    	dict: An accepted command response containing the command identifier, correlation identifier, purchase order identifier, resulting status, and next approval level when applicable.
    """
    if command.requested_by != ctx.subject:
        raise HTTPException(status_code=403, detail="requested_by does not match authenticated service identity")

    payload_hash = _payload_hash(command)
    existing = _get_command_or_none(db, idempotency_key)
    if existing:
        if existing.payload_hash != payload_hash:
            raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
        return existing.response

    correlation = correlation_id or str(uuid.uuid4())
    po_id = command.payload.get("po_id")
    if not isinstance(po_id, int) or po_id < 1:
        raise HTTPException(status_code=400, detail="payload.po_id must be a positive integer")

    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).with_for_update().first()
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    actor = db.query(User).filter(User.id == ctx.actor_id).first()
    if actor is None or not actor.is_active:
        raise HTTPException(status_code=403, detail="Invalid ERP actor")

    level = 1 if po.status == "PENDING_APPROVAL" else 2 if po.status == "PENDING_SECOND_APPROVAL" else 0
    if level == 0:
        raise HTTPException(status_code=409, detail="Purchase order is not awaiting approval")

    if command.command_type == "purchase_order_approve":
        allowed_roles = {"admin", "superadmin", "approver"} if level == 1 else {"admin", "superadmin", "second_approver"}
        if actor.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient approval permission")
        decision = "APPROVED"
        if level == 1 and Decimal(po.amount) > Decimal("50000"):
            po.status = "PENDING_SECOND_APPROVAL"
            next_level = 2
        else:
            po.status = "APPROVED"
            next_level = None
    else:
        if actor.role not in {"admin", "superadmin", "approver", "second_approver"}:
            raise HTTPException(status_code=403, detail="Insufficient rejection permission")
        decision = "REJECTED"
        po.status = "REJECTED"
        next_level = None

    db.add(PurchaseOrderApproval(po_id=po.id, approver_id=actor.id, approval_level=level, decision=decision, comment=command.payload.get("comment")))
    response = {
        "command_id": str(command.command_id),
        "status": "accepted",
        "correlation_id": correlation,
        "result": {"po_id": po.id, "status": po.status, "next_approval_level": next_level},
    }
    db.add(IntegrationCommand(
        idempotency_key=idempotency_key,
        command_id=str(command.command_id),
        command_type=command.command_type,
        requested_by=command.requested_by,
        payload_hash=payload_hash,
        status_code=202,
        response=response,
        correlation_id=correlation,
    ))
    try:
        db.flush()
        log_activity(db, user_id=actor.id, action=f"integration_{command.command_type}", entity_type="purchase_order", entity_id=po.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _get_command_or_none(db, idempotency_key)
        if existing is None:
            raise HTTPException(status_code=409, detail="Idempotency conflict")
        if existing.payload_hash != payload_hash:
            raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
        return existing.response
    return response
