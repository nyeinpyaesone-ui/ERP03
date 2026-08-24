from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from app.models import Contact, Company, Deal, FollowUp
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

class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company_id: Optional[int] = None
    status: str = "lead"
    source: Optional[str] = None
    notes: Optional[str] = None

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company_id: Optional[int] = None
    status: str
    source: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[int] = None
    lifetime_value: float = 0.0
    created_at: datetime
    updated_at: datetime

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

class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    value: float
    stage: str
    probability: int
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    assigned_to: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# FollowUp Schemas
class FollowUpCreate(BaseModel):
    title: str
    description: Optional[str] = None
    entity_type: str  # deal, contact, company
    entity_id: int
    scheduled_for: datetime
    priority: str = "medium"  # low, medium, high, urgent

class FollowUpUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    priority: Optional[str] = None
    completed: Optional[bool] = None

class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str] = None
    entity_type: str
    entity_id: int
    deal_id: Optional[int] = None
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    scheduled_for: datetime
    completed: bool
    completed_at: Optional[datetime] = None
    completed_by: Optional[int] = None
    reminder_sent: bool
    priority: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

# Companies
@router.post("/companies", response_model=CompanyResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a company and record its creation activity.
    
    Parameters:
    	data (CompanyCreate): Company details used to create the record.
    
    Returns:
    	Company: The newly created company.
    """
    company = Company(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    log_activity(db, user_id=current_user.id, action="company_created", entity_type="company", entity_id=company.id)
    return company

@router.get("/companies", response_model=List[CompanyResponse])
def list_companies(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List companies with optional name search and pagination.
    
    Parameters:
        skip (int): Number of companies to skip.
        limit (int): Maximum number of companies to return.
        search (Optional[str]): Case-insensitive text to match against company names.
    
    Returns:
        list[Company]: Companies matching the search and pagination criteria.
    """
    query = db.query(Company)
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve a company by its identifier.
    
    Parameters:
    	company_id (int): The identifier of the company to retrieve.
    
    Returns:
    	Company: The matching company record.
    
    Raises:
    	HTTPException: If no company matches the identifier.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/companies/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, data: CompanyCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update a company's stored details.
    
    Parameters:
    	company_id (int): Identifier of the company to update.
    	data (CompanyCreate): Replacement company details.
    
    Returns:
    	Company: The updated company.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in data.model_dump().items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company

@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Delete a company by its identifier.
    
    Parameters:
    	company_id (int): Identifier of the company to delete.
    
    Returns:
    	dict: Confirmation message indicating that the company was deleted.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted"}

# Contacts
@router.post("/contacts", response_model=ContactResponse)
def create_contact(data: ContactCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a contact assigned to the authenticated user.
    
    Parameters:
    	data (ContactCreate): Contact details used to create the record.
    
    Returns:
    	Contact: The newly created contact.
    """
    contact = Contact(**data.model_dump(), assigned_to=current_user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    log_activity(db, user_id=current_user.id, action="contact_created", entity_type="contact", entity_id=contact.id)
    return contact

@router.get("/contacts", response_model=List[ContactResponse])
def list_contacts(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List contacts with optional status filtering and name or email search.
    
    Parameters:
    	status (Optional[str]): Contact status used to filter results.
    	search (Optional[str]): Text matched case-insensitively against the contact's full name or email.
    
    Returns:
    	list[Contact]: Contacts matching the filters and pagination settings.
    """
    query = db.query(Contact)
    if status:
        query = query.filter(Contact.status == status)
    if search:
        query = query.filter(
            (Contact.first_name + " " + Contact.last_name).ilike(f"%{search}%") |
            Contact.email.ilike(f"%{search}%")
        )
    return query.offset(skip).limit(limit).all()

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Retrieve a contact by its identifier.
    
    Parameters:
    	contact_id (int): The identifier of the contact to retrieve.
    
    Returns:
    	Contact: The requested contact.
    
    Raises:
    	HTTPException: If the contact does not exist.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, data: ContactCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update a contact with the supplied details.
    
    Parameters:
    	contact_id (int): The identifier of the contact to update.
    	data (ContactCreate): The contact details to apply.
    
    Returns:
    	Contact: The updated contact.
    
    Raises:
    	HTTPException: If the contact does not exist.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in data.model_dump().items():
        setattr(contact, key, value)
    from datetime import timezone
    contact.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Delete a contact by its identifier.
    
    Parameters:
        contact_id (int): Identifier of the contact to delete.
    
    Returns:
        dict: A confirmation message indicating that the contact was deleted.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}

# Deals / Pipeline
@router.post("/deals", response_model=DealResponse)
def create_deal(data: DealCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a deal assigned to the authenticated user.
    
    Parameters:
    	data (DealCreate): Deal details used to create the record.
    
    Returns:
    	Deal: The newly created deal.
    """
    deal = Deal(**data.model_dump(), assigned_to=current_user.id)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    log_activity(db, user_id=current_user.id, action="deal_created", entity_type="deal", entity_id=deal.id)
    return deal

@router.get("/deals", response_model=List[DealResponse])
def list_deals(
    skip: int = 0,
    limit: int = 100,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List deals with optional stage filtering and pagination.
    
    Parameters:
    	stage (Optional[str]): Deal stage used to filter the results.
    
    Returns:
    	list[Deal]: The matching deals.
    """
    query = db.query(Deal)
    if stage:
        query = query.filter(Deal.stage == stage)
    return query.offset(skip).limit(limit).all()

@router.get("/deals/pipeline")
def get_pipeline(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Group deals by pipeline stage with counts, total values, and deal records.
    
    Returns:
    	pipeline (dict): Mapping of each pipeline stage to its deal count, total value, and deals.
    """
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

@router.get("/deals/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Retrieve a deal by its identifier.
    
    Parameters:
        deal_id (int): Identifier of the deal to retrieve.
    
    Returns:
        Deal: The matching deal.
    
    Raises:
        HTTPException: If the deal does not exist.
    """
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@router.put("/deals/{deal_id}", response_model=DealResponse)
def update_deal(deal_id: int, data: DealUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update a deal and apply stage-based closing details.
    
    Parameters:
        deal_id (int): Identifier of the deal to update.
        data (DealUpdate): Fields to change on the deal.
    
    Raises:
        HTTPException: If the deal does not exist.
    
    Returns:
        Deal: The updated deal.
    """
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    update_data = data.model_dump(exclude_unset=True)
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

    from datetime import timezone
    deal.updated_at = datetime.now(timezone.utc)
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

# Follow-ups endpoints
@router.post("/follow-ups", response_model=FollowUpResponse)
def create_follow_up(data: FollowUpCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a follow-up task for a deal, contact, or company.
    
    Parameters:
        data (FollowUpCreate): Follow-up details including title, scheduled time, and priority.
    
    Returns:
        FollowUp: The newly created follow-up record.
    
    Raises:
        HTTPException: If the related entity does not exist.
    """
    # Validate entity exists and set appropriate foreign key
    deal_id = None
    contact_id = None
    company_id = None
    
    if data.entity_type == "deal":
        entity = db.query(Deal).filter(Deal.id == data.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Deal not found")
        deal_id = data.entity_id
    elif data.entity_type == "contact":
        entity = db.query(Contact).filter(Contact.id == data.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Contact not found")
        contact_id = data.entity_id
    elif data.entity_type == "company":
        entity = db.query(Company).filter(Company.id == data.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Company not found")
        company_id = data.entity_id
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type. Must be 'deal', 'contact', or 'company'")
    
    follow_up = FollowUp(
        title=data.title,
        description=data.description,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        deal_id=deal_id,
        contact_id=contact_id,
        company_id=company_id,
        scheduled_for=data.scheduled_for,
        priority=data.priority,
        created_by=current_user.id
    )
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    log_activity(db, user_id=current_user.id, action="follow_up_created", entity_type="follow_up", entity_id=follow_up.id)
    return follow_up

@router.get("/follow-ups", response_model=List[FollowUpResponse])
def list_follow_ups(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    upcoming: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List follow-ups with optional filtering.
    
    Parameters:
        entity_type (Optional[str]): Filter by entity type (deal, contact, company).
        entity_id (Optional[int]): Filter by specific entity ID.
        completed (Optional[bool]): Filter by completion status.
        priority (Optional[str]): Filter by priority level.
        upcoming (Optional[bool]): If True, only show incomplete follow-ups scheduled for the future.
    
    Returns:
        list[FollowUp]: Follow-ups matching the filters.
    """
    query = db.query(FollowUp)
    
    if entity_type:
        query = query.filter(FollowUp.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(FollowUp.entity_id == entity_id)
    if completed is not None:
        query = query.filter(FollowUp.completed == completed)
    if priority:
        query = query.filter(FollowUp.priority == priority)
    if upcoming:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        query = query.filter(FollowUp.completed == False, FollowUp.scheduled_for >= now)
    
    return query.offset(skip).limit(limit).all()

@router.get("/follow-ups/{follow_up_id}", response_model=FollowUpResponse)
def get_follow_up(follow_up_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve a specific follow-up by its identifier.
    
    Parameters:
        follow_up_id (int): The identifier of the follow-up to retrieve.
    
    Returns:
        FollowUp: The requested follow-up record.
    
    Raises:
        HTTPException: If no follow-up matches the identifier.
    """
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return follow_up

@router.put("/follow-ups/{follow_up_id}", response_model=FollowUpResponse)
def update_follow_up(follow_up_id: int, data: FollowUpUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update a follow-up's details or mark it as completed.
    
    Parameters:
        follow_up_id (int): Identifier of the follow-up to update.
        data (FollowUpUpdate): Fields to change on the follow-up.
    
    Returns:
        FollowUp: The updated follow-up.
    
    Raises:
        HTTPException: If the follow-up does not exist.
    """
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "completed" and value:
            follow_up.completed = True
            from datetime import datetime, timezone
            follow_up.completed_at = datetime.now(timezone.utc)
            follow_up.completed_by = current_user.id
        else:
            setattr(follow_up, key, value)
    
    from datetime import timezone
    follow_up.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(follow_up)
    log_activity(db, user_id=current_user.id, action="follow_up_updated", entity_type="follow_up", entity_id=follow_up.id)
    return follow_up

@router.delete("/follow-ups/{follow_up_id}")
def delete_follow_up(follow_up_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Delete a follow-up by its identifier.
    
    Parameters:
        follow_up_id (int): Identifier of the follow-up to delete.
    
    Returns:
        dict: Confirmation message indicating that the follow-up was deleted.
    """
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    db.delete(follow_up)
    db.commit()
    return {"message": "Follow-up deleted"}

@router.get("/deals/{deal_id}/follow-ups", response_model=List[FollowUpResponse])
def get_deal_follow_ups(deal_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve all follow-ups associated with a specific deal.
    
    Parameters:
        deal_id (int): Identifier of the deal.
    
    Returns:
        list[FollowUp]: All follow-ups linked to the deal.
    """
    # Verify deal exists
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return db.query(FollowUp).filter(FollowUp.deal_id == deal_id).all()

@router.get("/contacts/{contact_id}/follow-ups", response_model=List[FollowUpResponse])
def get_contact_follow_ups(contact_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve all follow-ups associated with a specific contact.
    
    Parameters:
        contact_id (int): Identifier of the contact.
    
    Returns:
        list[FollowUp]: All follow-ups linked to the contact.
    """
    # Verify contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return db.query(FollowUp).filter(FollowUp.contact_id == contact_id).all()

@router.get("/companies/{company_id}/follow-ups", response_model=List[FollowUpResponse])
def get_company_follow_ups(company_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve all follow-ups associated with a specific company.
    
    Parameters:
        company_id (int): Identifier of the company.
    
    Returns:
        list[FollowUp]: All follow-ups linked to the company.
    """
    # Verify company exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return db.query(FollowUp).filter(FollowUp.company_id == company_id).all()

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

