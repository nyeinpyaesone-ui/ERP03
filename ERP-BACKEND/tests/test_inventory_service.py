from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.inventory_service import InventoryService


class QueryStub:
    def __init__(self, *, one_result=None, all_result=None):
        self.one_result = one_result
        self.all_result = all_result or []

    def one(self):
        return self.one_result

    def group_by(self, *_args, **_kwargs):
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


class TestUpdateProduct:
    """Tests for InventoryService.update_product, including the migration of
    `updated_at` from datetime.utcnow() to datetime.now(timezone.utc)."""

    def _make_product(self, **overrides):
        defaults = dict(
            id=1,
            sku="SKU-1",
            name="Original Name",
            unit_price=Decimal("10.00"),
            cost_price=Decimal("5.00"),
            quantity_in_stock=20,
            updated_at=None,
        )
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_update_product_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = InventoryService(db).update_product(999, {"name": "New Name"})

        assert result is None
        db.commit.assert_not_called()

    def test_update_product_updates_fields_and_sets_timezone_aware_updated_at(self):
        """
        Regression test: `updated_at` must be set to a timezone-aware UTC
        datetime. Prior to this PR, app/services/inventory_service.py only
        imports `datetime` (not `timezone`), so calling
        datetime.now(timezone.utc) raises a NameError unless `timezone` is
        also imported.
        """
        db = MagicMock()
        product = self._make_product()
        db.query.return_value.filter.return_value.first.return_value = product

        before = datetime.now(timezone.utc)
        result = InventoryService(db).update_product(
            1, {"name": "Updated Name", "unit_price": Decimal("25.00")}
        )
        after = datetime.now(timezone.utc)

        assert result is product
        assert product.name == "Updated Name"
        assert product.unit_price == Decimal("25.00")
        assert product.updated_at.tzinfo is not None
        assert product.updated_at.tzinfo == timezone.utc
        assert before <= product.updated_at <= after
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(product)

    def test_update_product_negative_unit_price_raises(self):
        db = MagicMock()
        product = self._make_product()
        db.query.return_value.filter.return_value.first.return_value = product

        with pytest.raises(ValueError, match="Unit price cannot be negative"):
            InventoryService(db).update_product(1, {"unit_price": Decimal("-1.00")})

    def test_update_product_negative_cost_price_raises(self):
        db = MagicMock()
        product = self._make_product()
        db.query.return_value.filter.return_value.first.return_value = product

        with pytest.raises(ValueError, match="Cost price cannot be negative"):
            InventoryService(db).update_product(1, {"cost_price": Decimal("-5.00")})

    def test_update_product_negative_stock_quantity_raises(self):
        db = MagicMock()
        product = self._make_product()
        db.query.return_value.filter.return_value.first.return_value = product

        with pytest.raises(ValueError, match="Stock quantity cannot be negative"):
            InventoryService(db).update_product(1, {"quantity_in_stock": -5})

    def test_update_product_duplicate_sku_raises(self):
        db = MagicMock()
        product = self._make_product()
        conflicting_product = self._make_product(id=2, sku="SKU-2")
        # First call resolves get_product(); second resolves the SKU conflict check.
        db.query.return_value.filter.return_value.first.side_effect = [
            product,
            conflicting_product,
        ]

        with pytest.raises(ValueError, match="already exists"):
            InventoryService(db).update_product(1, {"sku": "SKU-2"})

    def test_update_product_sku_change_without_conflict_succeeds(self):
        db = MagicMock()
        product = self._make_product()
        db.query.return_value.filter.return_value.first.side_effect = [product, None]

        result = InventoryService(db).update_product(1, {"sku": "SKU-NEW"})

        assert result.sku == "SKU-NEW"
        db.commit.assert_called_once()

    def test_update_product_commit_false_uses_flush(self):
        db = MagicMock()
        product = self._make_product()
        db.query.return_value.filter.return_value.first.return_value = product

        InventoryService(db).update_product(1, {"name": "Flushed"}, commit=False)

        db.flush.assert_called_once()
        db.commit.assert_not_called()


class TestCreateStockMovement:
    """Tests for InventoryService.create_stock_movement, including the migration
    of `updated_at` from datetime.utcnow() to datetime.now(timezone.utc)."""

    def _make_product(self, **overrides):
        defaults = dict(id=1, quantity_in_stock=10, updated_at=None)
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def _mock_db_with_product(self, product):
        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = product
        return db

    def test_invalid_movement_type_raises(self):
        db = self._mock_db_with_product(self._make_product())

        with pytest.raises(ValueError, match="Invalid movement type"):
            InventoryService(db).create_stock_movement(1, "bogus", 5)

    def test_negative_quantity_raises(self):
        db = self._mock_db_with_product(self._make_product())

        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            InventoryService(db).create_stock_movement(1, "in", -5)

    def test_product_not_found_raises_and_rolls_back(self):
        db = self._mock_db_with_product(None)

        with pytest.raises(ValueError, match="not found"):
            InventoryService(db).create_stock_movement(999, "in", 5)

        db.rollback.assert_called_once()

    def test_movement_in_increases_stock_and_sets_timezone_aware_updated_at(self):
        """
        Regression test: successful stock movements must set the product's
        `updated_at` to a timezone-aware UTC datetime, guarding against the
        missing `timezone` import causing a NameError.
        """
        product = self._make_product(quantity_in_stock=10)
        db = self._mock_db_with_product(product)

        before = datetime.now(timezone.utc)
        movement = InventoryService(db).create_stock_movement(1, "in", 15)
        after = datetime.now(timezone.utc)

        assert product.quantity_in_stock == 25
        assert product.updated_at.tzinfo == timezone.utc
        assert before <= product.updated_at <= after
        db.add.assert_called_once_with(movement)
        db.commit.assert_called_once()

    def test_movement_out_decreases_stock(self):
        product = self._make_product(quantity_in_stock=10)
        db = self._mock_db_with_product(product)

        InventoryService(db).create_stock_movement(1, "out", 4)

        assert product.quantity_in_stock == 6

    def test_movement_out_insufficient_stock_raises_and_rolls_back(self):
        product = self._make_product(quantity_in_stock=3)
        db = self._mock_db_with_product(product)

        with pytest.raises(ValueError, match="Insufficient stock"):
            InventoryService(db).create_stock_movement(1, "out", 10)

        db.rollback.assert_called_once()

    def test_movement_adjustment_sets_exact_quantity(self):
        product = self._make_product(quantity_in_stock=99)
        db = self._mock_db_with_product(product)

        InventoryService(db).create_stock_movement(1, "adjustment", 42)

        assert product.quantity_in_stock == 42

    def test_movement_transfer_does_not_change_quantity(self):
        product = self._make_product(quantity_in_stock=50)
        db = self._mock_db_with_product(product)

        InventoryService(db).create_stock_movement(1, "transfer", 5)

        assert product.quantity_in_stock == 50

    def test_commit_false_uses_flush(self):
        product = self._make_product(quantity_in_stock=10)
        db = self._mock_db_with_product(product)

        InventoryService(db).create_stock_movement(1, "in", 5, commit=False)

        db.flush.assert_called_once()
        db.commit.assert_not_called()
