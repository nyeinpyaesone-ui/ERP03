from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import httpx
import json

from app.database import get_db
from app.models import Contact, Company, Deal, Product, Invoice, Project, Task
from app.auth import get_current_user
from app.config import settings
from app.services.activity_log import log_activity

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None

async def query_ollama(prompt: str, model: str = None) -> str:
    model = model or settings.OLLAMA_MODEL
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "No response from AI")
            return f"AI service unavailable (status: {response.status_code})"
    except Exception as e:
        return f"AI service error: {str(e)}"

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Gather business context
    context_data = {}

    # Recent contacts
    context_data["contacts_count"] = db.query(Contact).count()
    context_data["recent_contacts"] = [
        {"name": f"{c.first_name} {c.last_name}", "status": c.status}
        for c in db.query(Contact).order_by(Contact.created_at.desc()).limit(5).all()
    ]

    # Pipeline
    deals = db.query(Deal).all()
    pipeline_value = sum(d.value or 0 for d in deals if d.stage != "closed_lost")
    context_data["pipeline_value"] = float(pipeline_value)
    context_data["deals_by_stage"] = {}
    for stage in ["prospect", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]:
        stage_deals = [d for d in deals if d.stage == stage]
        context_data["deals_by_stage"][stage] = {
            "count": len(stage_deals),
            "value": float(sum(d.value or 0 for d in stage_deals))
        }

    # Inventory
    products = db.query(Product).all()
    low_stock = [p for p in products if p.quantity_in_stock <= p.reorder_level]
    context_data["total_products"] = len(products)
    context_data["low_stock_count"] = len(low_stock)
    context_data["low_stock_items"] = [
        {"name": p.name, "stock": p.quantity_in_stock, "reorder": p.reorder_level}
        for p in low_stock[:5]
    ]

    # Projects
    tasks = db.query(Task).all()
    context_data["total_tasks"] = len(tasks)
    context_data["overdue_tasks"] = len([t for t in tasks if t.due_date and t.status != "done"])

    prompt = f"""You are an AI business assistant for an ERP system. Answer the user's question concisely and helpfully.

Business Context:
{json.dumps(context_data, indent=2, default=str)}

User Question: {message.message}

Provide a helpful, data-driven response. If you don't have specific data, say so."""

    response_text = await query_ollama(prompt)

    log_activity(db, user_id=current_user.id, action="ai_chat", entity_type="ai", details={"query": message.message[:200]})

    return ChatResponse(response=response_text)

@router.get("/insights")
async def get_ai_insights(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Revenue insights
    last_month = datetime.now() - timedelta(days=30)
    invoices = db.query(Invoice).filter(Invoice.created_at >= last_month).all()
    revenue = sum(i.total or 0 for i in invoices)

    # Churn risk
    inactive_contacts = db.query(Contact).filter(
        Contact.last_activity < datetime.now() - timedelta(days=90)
    ).all()

    # Stock alerts
    low_stock = db.query(Product).filter(Product.quantity_in_stock <= Product.reorder_level).all()

    insights = []

    if revenue > 0:
        insights.append({
            "category": "revenue",
            "priority": "medium",
            "message": f"Revenue in last 30 days: ${revenue:,.2f}"
        })

    if inactive_contacts:
        insights.append({
            "category": "growth",
            "priority": "high",
            "message": f"{len(inactive_contacts)} contacts have been inactive for 90+ days. Consider re-engagement campaigns."
        })

    if low_stock:
        insights.append({
            "category": "operations",
            "priority": "high",
            "message": f"{len(low_stock)} products are below reorder level. Restock recommended."
        })

    # Get AI-generated summary
    prompt = f"""Analyze this business data and provide 3-5 actionable insights:
- Revenue last 30 days: ${revenue:,.2f}
- Inactive contacts: {len(inactive_contacts)}
- Low stock products: {len(low_stock)}
- Total deals: {db.query(Deal).count()}
- Active projects: {db.query(Project).filter(Project.status == 'active').count()}

Format as JSON with fields: category, priority, message."""

    ai_response = await query_ollama(prompt)

    return {
        "insights": insights,
        "ai_summary": ai_response,
        "health_score": "good" if len([i for i in insights if i["priority"] == "high"]) < 3 else "fair"
    }

@router.get("/forecast/revenue")
async def forecast_revenue(
    months: int = 3,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # Get last 6 months of paid invoices
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    monthly_data = db.query(
        func.extract('month', Invoice.created_at).label('month'),
        func.extract('year', Invoice.created_at).label('year'),
        func.sum(Invoice.total).label('total')
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.status == "paid"
    ).group_by('year', 'month').order_by('year', 'month').all()

    if not monthly_data:
        return {"forecast": [], "message": "Insufficient data for forecasting"}

    values = [float(m.total) for m in monthly_data]
    avg_growth = sum((values[i] - values[i-1]) / values[i-1] * 100 for i in range(1, len(values))) / max(1, len(values) - 1) if len(values) > 1 else 0

    forecast = []
    last_value = values[-1] if values else 0

    for i in range(1, months + 1):
        predicted = last_value * (1 + avg_growth / 100) ** i
        forecast.append({
            "month": i,
            "predicted_revenue": round(predicted, 2),
            "confidence_low": round(predicted * 0.8, 2),
            "confidence_high": round(predicted * 1.2, 2),
            "growth_rate": round(avg_growth, 2)
        })

    return {
        "historical": [{"month": f"{m.year}-{m.month}", "revenue": float(m.total)} for m in monthly_data],
        "forecast": forecast,
        "trend": "increasing" if avg_growth > 0 else "decreasing" if avg_growth < 0 else "stable",
        "confidence": "medium"
    }

