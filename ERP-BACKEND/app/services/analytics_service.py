from datetime import datetime, timedelta

from sqlalchemy import extract, func, case, select
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
        """Build the dashboard with bounded, read-only aggregate query paths.

        Each domain keeps one aggregate query where practical. CRM contact
        count is folded into the deal aggregate as a scalar subquery so the
        dashboard does not issue a separate contacts round trip.
        """
        invoice_metrics = (
            self.db.query(
                func.coalesce(
                    func.sum(case((Invoice.status == "paid", Invoice.total), else_=0)),
                    0,
                ).label("total_revenue"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Invoice.status != "paid",
                                Invoice.total - Invoice.amount_paid,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("outstanding"),
            )
            .one()
        )

        contact_count = select(func.count(Contact.id)).scalar_subquery()
        deal_metrics = (
            self.db.query(
                contact_count.label("total_contacts"),
                func.count(Deal.id).label("total_deals"),
                func.coalesce(
                    func.sum(
                        case((Deal.stage != "closed_lost", Deal.value), else_=0)
                    ),
                    0,
                ).label("pipeline_value"),
            )
            .one()
        )

        employee_metrics = (
            self.db.query(
                func.count(Employee.id).label("total_employees"),
                func.coalesce(
                    func.sum(case((Employee.status == "active", 1), else_=0)),
                    0,
                ).label("active_employees"),
            )
            .one()
        )

        product_metrics = (
            self.db.query(
                func.count(Product.id).label("total_products"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Product.quantity_in_stock <= Product.reorder_level,
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("low_stock"),
            )
            .one()
        )

        project_metrics = (
            self.db.query(
                func.count(Project.id).label("total_projects"),
                func.coalesce(
                    func.sum(case((Project.status == "active", 1), else_=0)),
                    0,
                ).label("active_projects"),
            )
            .one()
        )

        task_metrics = (
            self.db.query(
                func.count(Task.id).label("total_tasks"),
                func.coalesce(
                    func.sum(case((Task.status == "done", 1), else_=0)),
                    0,
                ).label("completed_tasks"),
            )
            .one()
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

        total_revenue_float = float(invoice_metrics.total_revenue or 0)
        outstanding_float = float(invoice_metrics.outstanding or 0)
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
                "contacts": int(deal_metrics.total_contacts or 0),
                "deals": int(deal_metrics.total_deals or 0),
                "pipeline_value": float(deal_metrics.pipeline_value or 0),
            },
            "hr": {
                "total_employees": int(employee_metrics.total_employees or 0),
                "active_employees": int(employee_metrics.active_employees or 0),
            },
            "inventory": {
                "total_products": int(product_metrics.total_products or 0),
                "low_stock": int(product_metrics.low_stock or 0),
            },
            "projects": {
                "total_projects": int(project_metrics.total_projects or 0),
                "active_projects": int(project_metrics.active_projects or 0),
                "tasks": {
                    "total": int(task_metrics.total_tasks or 0),
                    "completed": int(task_metrics.completed_tasks or 0),
                },
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
