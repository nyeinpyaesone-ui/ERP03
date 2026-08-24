from unittest.mock import MagicMock

import app.services.activity_log as activity_log
import app.services.inventory_service as inventory_module
from app.models import ActivityLog, Product


def test_inventory_mutation_can_join_caller_transaction(monkeypatch):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    product = MagicMock()
    monkeypatch.setattr(inventory_module, "Product", MagicMock(return_value=product))

    service = inventory_module.InventoryService(db)
    result = service.create_product(
        sku="SKU-001",
        name="Rice",
        unit_price=100,
        commit=False,
    )

    assert result is product
    db.flush.assert_called_once()
    db.commit.assert_not_called()
    db.refresh.assert_called_once_with(product)


def test_audit_log_can_join_caller_transaction(monkeypatch):
    db = MagicMock()
    audit_model = MagicMock()
    monkeypatch.setattr(activity_log, "ActivityLog", audit_model)

    result = activity_log.log_activity(
        db,
        user_id=1,
        action="product_created",
        entity_type="product",
        entity_id=10,
        commit=False,
    )

    assert result is audit_model.return_value
    db.add.assert_called_once_with(result)
    db.flush.assert_called_once()
    db.commit.assert_not_called()


def test_inventory_and_audit_rollback_together(db_session):
    service = inventory_module.InventoryService(db_session)

    product = service.create_product(
        sku="TX-ROLLBACK-001",
        name="Rollback Rice",
        unit_price=100,
        commit=False,
    )
    activity_log.log_activity(
        db_session,
        action="product_created",
        entity_type="product",
        entity_id=product.id,
        commit=False,
    )

    db_session.rollback()

    assert db_session.query(Product).filter(Product.sku == "TX-ROLLBACK-001").one_or_none() is None
    assert db_session.query(ActivityLog).filter(
        ActivityLog.action == "product_created",
        ActivityLog.entity_type == "product",
        ActivityLog.entity_id == product.id,
    ).one_or_none() is None


def test_inventory_and_audit_commit_together(db_session):
    service = inventory_module.InventoryService(db_session)

    product = service.create_product(
        sku="TX-COMMIT-001",
        name="Commit Rice",
        unit_price=100,
        commit=False,
    )
    activity_log.log_activity(
        db_session,
        action="product_created",
        entity_type="product",
        entity_id=product.id,
        commit=False,
    )

    db_session.commit()

    assert db_session.query(Product).filter(Product.sku == "TX-COMMIT-001").one_or_none() is not None
    assert db_session.query(ActivityLog).filter(
        ActivityLog.action == "product_created",
        ActivityLog.entity_type == "product",
        ActivityLog.entity_id == product.id,
    ).one_or_none() is not None
