from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.services.analytics_service import AnalyticsQueryService

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the aggregated ERP dashboard through the read/query service."""
    return AnalyticsQueryService(db).get_dashboard()


@router.get("/monthly-trends")
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return monthly revenue and deal trends through the read/query service."""
    return AnalyticsQueryService(db).get_monthly_trends()
