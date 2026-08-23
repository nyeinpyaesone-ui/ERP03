from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.analytics_service import AnalyticsQueryService


class QueryStub:
    def __init__(self, *, one_result=None, scalar_result=None, all_result=None):
        """Initialize the query stub with optional results for each query method.
        
        Parameters:
        	one_result: Value returned by the stub's ``one()`` method.
        	scalar_result: Value returned by the stub's ``scalar()`` method.
        	all_result: Values returned by the stub's ``all()`` method; defaults to an empty list.
        """
        self.one_result = one_result
        self.scalar_result = scalar_result
        self.all_result = all_result or []

    def one(self):
        return self.one_result

    def scalar(self):
        return self.scalar_result

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.all_result


def test_dashboard_uses_bounded_aggregate_query_paths():
    db = MagicMock()
    db.query.side_effect = [
        QueryStub(one_result=SimpleNamespace(total_revenue=1000, outstanding=250)),
        QueryStub(
            one_result=SimpleNamespace(
                total_contacts=12,
                total_deals=7,
                pipeline_value=5000,
            )
        ),
        QueryStub(one_result=SimpleNamespace(total_employees=20, active_employees=18)),
        QueryStub(one_result=SimpleNamespace(total_products=100, low_stock=8)),
        QueryStub(one_result=SimpleNamespace(total_projects=9, active_projects=4)),
        QueryStub(one_result=SimpleNamespace(total_tasks=30, completed_tasks=21)),
        QueryStub(
            all_result=[
                ("invoice.created", "invoice", None),
            ]
        ),
    ]

    result = AnalyticsQueryService(db).get_dashboard()

    assert result["revenue"]["total"] == 1000.0
    assert result["revenue"]["outstanding"] == 250.0
    assert result["revenue"]["collection_rate"] == 80.0
    assert result["crm"] == {
        "contacts": 12,
        "deals": 7,
        "pipeline_value": 5000.0,
    }
    assert result["hr"] == {"total_employees": 20, "active_employees": 18}
    assert result["inventory"] == {"total_products": 100, "low_stock": 8}
    assert result["projects"] == {
        "total_projects": 9,
        "active_projects": 4,
        "tasks": {"total": 30, "completed": 21},
    }
    assert result["recent_activity"] == [
        {"action": "invoice.created", "entity_type": "invoice", "created_at": None}
    ]

    # Dashboard execution is bounded to one query per aggregate/read path.
    # CRM contacts are included through a scalar subquery in the CRM aggregate.
    assert db.query.call_count == 7
