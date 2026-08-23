from datetime import datetime, timedelta, timezone
from decimal import Decimal
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


class TrendQueryStub:
    """Query stub supporting the filter().group_by().order_by().all() chain
    used by AnalyticsQueryService.get_monthly_trends."""

    def __init__(self, *, all_result=None):
        self.all_result = all_result or []
        self.filter_call_args = None

    def filter(self, *args, **kwargs):
        self.filter_call_args = (args, kwargs)
        return self

    def group_by(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.all_result


def test_get_monthly_trends_returns_formatted_revenue_and_deals():
    revenue_row = SimpleNamespace(year=2024, month=1, total=Decimal("1000.00"))
    deal_row = SimpleNamespace(year=2024, month=1, count=3, value=Decimal("5000.00"))

    revenue_query = TrendQueryStub(all_result=[revenue_row])
    deals_query = TrendQueryStub(all_result=[deal_row])

    db = MagicMock()
    db.query.side_effect = [revenue_query, deals_query]

    result = AnalyticsQueryService(db).get_monthly_trends(months_back=3)

    assert result["revenue"] == [{"period": "2024-01", "amount": 1000.0}]
    assert result["deals"] == [{"period": "2024-01", "count": 3, "value": 5000.0}]


def test_get_monthly_trends_deals_value_defaults_to_zero_when_none():
    deal_row = SimpleNamespace(year=2024, month=5, count=2, value=None)

    revenue_query = TrendQueryStub(all_result=[])
    deals_query = TrendQueryStub(all_result=[deal_row])

    db = MagicMock()
    db.query.side_effect = [revenue_query, deals_query]

    result = AnalyticsQueryService(db).get_monthly_trends()

    assert result["deals"] == [{"period": "2024-05", "count": 2, "value": 0.0}]


def test_get_monthly_trends_empty_results():
    revenue_query = TrendQueryStub(all_result=[])
    deals_query = TrendQueryStub(all_result=[])

    db = MagicMock()
    db.query.side_effect = [revenue_query, deals_query]

    result = AnalyticsQueryService(db).get_monthly_trends()

    assert result == {"revenue": [], "deals": []}


def test_get_monthly_trends_filters_using_timezone_aware_start_date():
    """
    Regression test: get_monthly_trends() computes `start_date` using
    datetime.now(timezone.utc) - timedelta(...). This exercises the real
    (unmocked) datetime call so a missing `timezone` import would surface
    here as a NameError, and verifies the lookback window is honored.
    """
    revenue_query = TrendQueryStub(all_result=[])
    deals_query = TrendQueryStub(all_result=[])

    db = MagicMock()
    db.query.side_effect = [revenue_query, deals_query]

    before = datetime.now(timezone.utc)
    AnalyticsQueryService(db).get_monthly_trends(months_back=2)
    after = datetime.now(timezone.utc)

    start_date = revenue_query.filter_call_args[0][0].right.value

    assert start_date.tzinfo is not None
    assert start_date.tzinfo == timezone.utc
    assert before - timedelta(days=60) <= start_date <= after - timedelta(days=60)
