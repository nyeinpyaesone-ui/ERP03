from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
import io
import base64

from app.database import get_db
from app.models import Invoice, Deal, Contact, Product, Employee, Project, Task
from app.auth import get_current_user
from app.services.activity_log import log_activity

router = APIRouter()

@router.get("/revenue")
def revenue_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from sqlalchemy import func, extract

    query = db.query(Invoice)
    if start_date:
        query = query.filter(Invoice.issue_date >= start_date)
    if end_date:
        query = query.filter(Invoice.issue_date <= end_date)

    invoices = query.all()
    total = sum(i.total or 0 for i in invoices)
    paid = sum(i.amount_paid or 0 for i in invoices)

    monthly = db.query(
        extract('month', Invoice.issue_date).label('month'),
        extract('year', Invoice.issue_date).label('year'),
        func.sum(Invoice.total).label('total'),
        func.count(Invoice.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()

    return {
        "total_revenue": float(total),
        "total_paid": float(paid),
        "outstanding": float(total - paid),
        "invoice_count": len(invoices),
        "monthly_breakdown": [
            {"month": f"{m.year}-{m.month}", "revenue": float(m.total), "count": m.count}
            for m in monthly
        ]
    }

@router.get("/pipeline")
def pipeline_report(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    stages = ["prospect", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
    result = {}
    for stage in stages:
        deals = db.query(Deal).filter(Deal.stage == stage).all()
        result[stage] = {
            "count": len(deals),
            "value": float(sum(d.value or 0 for d in deals))
        }
    return result

@router.get("/inventory")
def inventory_report(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    products = db.query(Product).all()
    total_value = sum(p.quantity_in_stock * p.unit_price for p in products)
    low_stock = [p for p in products if p.quantity_in_stock <= p.reorder_level]

    return {
        "total_products": len(products),
        "total_stock_value": float(total_value),
        "low_stock_count": len(low_stock),
        "low_stock_items": [
            {"id": p.id, "name": p.name, "sku": p.sku, "stock": p.quantity_in_stock}
            for p in low_stock
        ],
        "categories": {}
    }

@router.get("/chart/revenue")
def revenue_chart(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from sqlalchemy import func, extract

        monthly = db.query(
            extract('month', Invoice.issue_date).label('month'),
            extract('year', Invoice.issue_date).label('year'),
            func.sum(Invoice.total).label('total')
        ).group_by('year', 'month').order_by('year', 'month').all()

        if not monthly:
            return {"chart": None}

        labels = [f"{m.year}-{m.month:02d}" for m in monthly]
        values = [float(m.total) for m in monthly]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(labels, values, color='#4f46e5')
        ax.set_xlabel('Month')
        ax.set_ylabel('Revenue ($)')
        ax.set_title('Monthly Revenue')
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()
        plt.close()

        return {"chart": f"data:image/png;base64,{img_base64}"}
    except Exception as e:
        return {"chart": None, "error": str(e)}

