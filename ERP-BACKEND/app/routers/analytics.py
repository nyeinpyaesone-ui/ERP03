from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Invoice, Deal, Contact, Product, Employee, Project, Task, ActivityLog
from app.auth import get_current_user

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_analytics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Revenue
    total_revenue = db.query(func.sum(Invoice.total)).filter(Invoice.status == "paid").scalar() or 0
    outstanding = db.query(func.sum(Invoice.total - Invoice.amount_paid)).filter(Invoice.status != "paid").scalar() or 0

    # CRM
    total_contacts = db.query(Contact).count()
    total_deals = db.query(Deal).count()
    pipeline_value = db.query(func.sum(Deal.value)).filter(Deal.stage != "closed_lost").scalar() or 0

    # HR
    total_employees = db.query(Employee).count()
    active_employees = db.query(Employee).filter(Employee.status == "active").count()

    # Inventory
    total_products = db.query(Product).count()
    low_stock = db.query(Product).filter(Product.quantity_in_stock <= Product.reorder_level).count()

    # Projects
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == "done").count()

    # Activity
    recent_activity = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(10).all()

    return {
        "revenue": {
            "total": float(total_revenue),
            "outstanding": float(outstanding),
            "collection_rate": (float(total_revenue) / (float(total_revenue) + float(outstanding)) * 100) if (total_revenue + outstanding) > 0 else 0
        },
        "crm": {
            "contacts": total_contacts,
            "deals": total_deals,
            "pipeline_value": float(pipeline_value)
        },
        "hr": {
            "total_employees": total_employees,
            "active_employees": active_employees
        },
        "inventory": {
            "total_products": total_products,
            "low_stock": low_stock
        },
        "projects": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "tasks": {"total": total_tasks, "completed": completed_tasks}
        },
        "recent_activity": [
            {"action": a.action, "entity_type": a.entity_type, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in recent_activity
        ]
    }

@router.get("/monthly-trends")
def get_monthly_trends(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    months_back = 6
    start_date = datetime.now() - timedelta(days=30 * months_back)

    revenue_by_month = db.query(
        extract('year', Invoice.issue_date).label('year'),
        extract('month', Invoice.issue_date).label('month'),
        func.sum(Invoice.total).label('total')
    ).filter(Invoice.issue_date >= start_date).group_by('year', 'month').order_by('year', 'month').all()

    deals_by_month = db.query(
        extract('year', Deal.created_at).label('year'),
        extract('month', Deal.created_at).label('month'),
        func.count(Deal.id).label('count'),
        func.sum(Deal.value).label('value')
    ).filter(Deal.created_at >= start_date).group_by('year', 'month').order_by('year', 'month').all()

    return {
        "revenue": [
            {"period": f"{r.year}-{r.month:02d}", "amount": float(r.total)}
            for r in revenue_by_month
        ],
        "deals": [
            {"period": f"{d.year}-{d.month:02d}", "count": d.count, "value": float(d.value or 0)}
            for d in deals_by_month
        ]
    }

