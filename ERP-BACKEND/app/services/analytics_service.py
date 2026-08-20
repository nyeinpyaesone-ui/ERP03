from datetime import datetime, timedelta

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models import (
    ActivityLog,
    Contact,
    Deal,
    Employee,
    Invoice,
    Product,
    Project,
    Task,
)


class AnalyticsQueryService:
    """Read-only aggregation service for ERP dashboard and trend queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> dict:
        """Build the dashboard response from optimized, read-only aggregate queries."""
        total_revenue = (
            self.db.query(func.sum(Invoice.total))
            .filter(Invoice.status == "paid")
            .scalar()
            or 0
        )
        outstanding = (
            self.db.query(func.sum(Invoice.total - Invoice.amount_paid))
            .filter(Invoice.status != "paid")
            .scalar()
            or 0
        )

        total_contacts = self.db.query(func.count(Contact.id)).scalar() or 0
        total_deals = self.db.query(func.count(Deal.id)).scalar() or 0
        pipeline_value = (
            self.db.query(func.sum(Deal.value))
            .filter(Deal.stage != "closed_lost")
            .scalar()
            or 0
        )

        total_employees = self.db.query(func.count(Employee.id)).scalar() or 0
        active_employees = (
            self.db.query(func.count(Employee.id))
            .filter(Employee.status == "active")
            .scalar()
            or 0
        )

        total_products = self.db.query(func.count(Product.id)).scalar() or 0
        low_stock = (
            self.db.query(func.count(Product.id))
            .filter(Product.quantity_in_stock <= Product.reorder_level)
            .scalar()
            or 0
        )

        total_projects = self.db.query(func.count(Project.id)).scalar() or 0
        active_projects = (
            self.db.query(func.count(Project.id))
            .filter(Project.status == "active")
            .scalar()
            or 0
        )
        total_tasks = self.db.query(func.count(Task.id)).scalar() or 0
        completed_tasks = (
            self.db.query(func.count(Task.id))
            .filter(Task.status == "done")
            .scalar()
            or 0
        )

        recent_activity = (
            self.db.query(
                ActivityLog.action,
                ActivityLog.entity_type,
                ActivityLog.created_at,
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(10)
            .all()
        )

        total_revenue_float = float(total_revenue)
        outstanding_float = float(outstanding)
        denominator = total_revenue_float + outstanding_float

        return {
            "revenue": {
                "total": total_revenue_float,
                "outstanding": outstanding_float,
                "collection_rate": (
                    total_revenue_float / denominator * 100 if denominator > 0 else 0
                ),
            },
            "crm": {
                "contacts": total_contacts,
                "deals": total_deals,
                "pipeline_value": float(pipeline_value),
            },
            "hr": {
                "total_employees": total_employees,
                "active_employees": active_employees,
            },
            "inventory": {
                "total_products": total_products,
                "low_stock": low_stock,
            },
            "projects": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "tasks": {"total": total_tasks, "completed": completed_tasks},
            },
            "recent_activity": [
                {
                    "action": action,
                    "entity_type": entity_type,
                    "created_at": created_at.isoformat() if created_at else None,
                }
                for action, entity_type, created_at in recent_activity
            ],
        }

    def get_monthly_trends(self, months_back: int = 6) -> dict:
        """Return monthly revenue and deal aggregates for the requested lookback."""
        start_date = datetime.now() - timedelta(days=30 * months_back)

        revenue_by_month = (
            self.db.query(
                extract("year", Invoice.issue_date).label("year"),
                extract("month", Invoice.issue_date).label("month"),
                func.sum(Invoice.total).label("total"),
            )
            .filter(Invoice.issue_date >= start_date)
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )

        deals_by_month = (
            self.db.query(
                extract("year", Deal.created_at).label("year"),
                extract("month", Deal.created_at).label("month"),
                func.count(Deal.id).label("count"),
                func.sum(Deal.value).label("value"),
            )
            .filter(Deal.created_at >= start_date)
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )

        return {
            "revenue": [
                {"period": f"{r.year}-{int(r.month):02d}", "amount": float(r.total)}
                for r in revenue_by_month
            ],
            "deals": [
                {
                    "period": f"{d.year}-{int(d.month):02d}",
                    "count": d.count,
                    "value": float(d.value or 0),
                }
                for d in deals_by_month
            ],
        }
