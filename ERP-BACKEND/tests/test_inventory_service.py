from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.inventory_service import InventoryService


class QueryStub:
    def __init__(self, *, one_result=None, all_result=None):
        self.one_result = one_result
        self.all_result = all_result or []

    def one(self):
        """Return the configured single query result."""
        return self.one_result

    def group_by(self, *_args, **_kwargs):
        """
        Support query chaining by returning this query stub unchanged.
        """
        return self

    def all(self):
        return self.all_result


def test_inventory_dashboard_uses_two_bounded_query_paths():
    db = MagicMock()
    db.query.side_effect = [
        QueryStub(
            one_result=SimpleNamespace(
                total_products=100,
                total_stock_value=250000,
                low_stock_count=8,
                out_of_stock=3,
            )
        ),
        QueryStub(
            all_result=[
                ("Rice", 60, 150000),
                ("Oil", 40, 100000),
            ]
        ),
    ]

    result = InventoryService(db).get_dashboard_stats()

    assert result == {
        "total_products": 100,
        "total_stock_value": 250000.0,
        "low_stock_count": 8,
        "out_of_stock": 3,
        "categories": [
            {"category": "Rice", "product_count": 60, "total_value": 150000.0},
            {"category": "Oil", "product_count": 40, "total_value": 100000.0},
        ],
    }
    assert db.query.call_count == 2
