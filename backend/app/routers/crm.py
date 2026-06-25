from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.models import Contact, Company, Deal
from app.auth import get_current_user, require_admin
from app.services.activity_log import log_activity

router = APIRouter()

# Schemas
class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company_id: Optional[int] = None
    status: str = "lead"
    source: Optional[str] = None
    notes: Optional[str] = None

class DealCreate(BaseModel):
    title: str
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    value: float = 0
    stage: str = "prospect"
    probability: int = 0
    expected_close_date: Optional[date] = None
    description: Optional[str] = None

class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None

# Companies
@router.post("/companies")
def create_company(data: CompanyCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = Company(**data.dict())
    db.add(company)
    db.commit()
    db.refresh(company)
    log_activity(db, user_id=current_user.id, action="company_created", entity_type="company", entity_id=company.id)
    return company

@router.get("/companies")
def list_companies(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Company)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/companies/{company_id}")
def get_company(company_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/companies/{company_id}")
def update_company(company_id: int, data: CompanyCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in data.dict().items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company

@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted"}

# Contacts
@router.post("/contacts")
def create_contact(data: ContactCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contact = Contact(**data.dict(), assigned_to=current_user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    log_activity(db, user_id=current_user.id, action="contact_created", entity_type="contact", entity_id=contact.id)
    return contact

@router.get("/contacts")
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Contact)
    if status:
        query = query.filter(Contact.status == status)
    if search:
        query = query.filter(
            (Contact.first_name + " " + Contact.last_name).ilike(f"%{search}%") |
            Contact.email.ilike(f"%{search}%")
        )
    return query.offset(skip).limit(limit).all()

@router.get("/contacts/{contact_id}")
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/contacts/{contact_id}")
def update_contact(contact_id: int, data: ContactCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in data.dict().items():
        setattr(contact, key, value)
    contact.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}

# Deals / Pipeline
@router.post("/deals")
def create_deal(data: DealCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deal = Deal(**data.dict(), assigned_to=current_user.id)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    log_activity(db, user_id=current_user.id, action="deal_created", entity_type="deal", entity_id=deal.id)
    return deal

@router.get("/deals")
def list_deals(
    skip: int = 0,
    limit: int = 100,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Deal)
    if stage:
        query = query.filter(Deal.stage == stage)
    return query.offset(skip).limit(limit).all()

@router.get("/deals/pipeline")
def get_pipeline(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    stages = ["prospect", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
    pipeline = {}
    for stage in stages:
        deals = db.query(Deal).filter(Deal.stage == stage).all()
        total = sum(d.value or 0 for d in deals)
        pipeline[stage] = {
            "count": len(deals),
            "total_value": float(total),
            "deals": deals
        }
    return pipeline

@router.get("/deals/{deal_id}")
def get_deal(deal_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@router.put("/deals/{deal_id}")
def update_deal(deal_id: int, data: DealUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(deal, key, value)

    # Auto-update probability based on stage
    stage_probabilities = {
        "prospect": 10,
        "qualification": 25,
        "proposal": 50,
        "negotiation": 75,
        "closed_won": 100,
        "closed_lost": 0
    }
    if deal.stage in stage_probabilities and "stage" in update_data:
        deal.probability = stage_probabilities[deal.stage]

    if deal.stage == "closed_won" and not deal.actual_close_date:
        deal.actual_close_date = date.today()

    deal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(deal)
    log_activity(db, user_id=current_user.id, action="deal_updated", entity_type="deal", entity_id=deal.id, details={"stage": deal.stage})
    return deal

@router.delete("/deals/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    db.delete(deal)
    db.commit()
    return {"message": "Deal deleted"}

# Dashboard stats
@router.get("/dashboard")
def crm_dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    total_contacts = db.query(Contact).count()
    total_companies = db.query(Company).count()
    total_deals = db.query(Deal).count()
    total_pipeline_value = db.query(func.sum(Deal.value)).filter(Deal.stage != "closed_lost").scalar() or 0
    won_deals = db.query(Deal).filter(Deal.stage == "closed_won").count()

    return {
        "total_contacts": total_contacts,
        "total_companies": total_companies,
        "total_deals": total_deals,
        "pipeline_value": float(total_pipeline_value),
        "won_deals": won_deals,
        "conversion_rate": (won_deals / total_deals * 100) if total_deals > 0 else 0
    }

