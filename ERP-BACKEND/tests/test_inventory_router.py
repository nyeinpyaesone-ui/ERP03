"""
Unit tests for the inventory router module (app/routers/inventory.py).

Covers:
- Pydantic request/response schema validation (ProductCreate, ProductUpdate,
  MovementCreate, MovementResponse, ProductResponse, DashboardResponse)
- Endpoint business logic (create/list/get/update/delete products, stock
  movements, dashboard stats, and low/out-of-stock alerts), using a mocked
  InventoryService and database session so endpoint functions can be called
  directly, matching the pattern used in tests/test_search_router.py.
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from pydantic import ValidationError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.routers.inventory import (
    ProductCreate,
    ProductUpdate,
    MovementCreate,
    MovementResponse,
    ProductResponse,
    DashboardResponse,
    get_inventory_service,
    create_product,
    list_products,
    get_product,
    update_product,
    delete_product,
    create_movement,
    list_movements,
    inventory_dashboard,
    get_low_stock_alerts,
    get_out_of_stock_alerts,
)
from app.services.inventory_service import InventoryService


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

class TestProductCreateSchema:
    """Tests for the ProductCreate request schema."""

    def test_minimal_required_fields(self):
        """Only sku, name, and unit_price are required; defaults apply."""
        data = ProductCreate(sku="SKU-1", name="Widget", unit_price=Decimal("9.99"))

        assert data.sku == "SKU-1"
        assert data.name == "Widget"
        assert data.unit_price == Decimal("9.99")
        assert data.status == "active"
        assert data.quantity_in_stock == 0
        assert data.reorder_level == 10
        assert data.reorder_quantity == 50
        assert data.description is None

    def test_all_fields_populated(self):
        data = ProductCreate(
            sku="SKU-2",
            name="Gadget",
            description="A gadget",
            category="Electronics",
            unit_price=Decimal("199.99"),
            cost_price=Decimal("100.00"),
            quantity_in_stock=25,
            reorder_level=5,
            reorder_quantity=20,
            supplier="Acme",
            supplier_contact="acme@example.com",
            status="draft",
            barcode="123456",
            weight=1.5,
            dimensions="10x10x10",
        )

        assert data.category == "Electronics"
        assert data.cost_price == Decimal("100.00")
        assert data.status == "draft"
        assert data.weight == 1.5
        assert data.dimensions == "10x10x10"

    @pytest.mark.parametrize("status", ["active", "discontinued", "draft"])
    def test_valid_status_values_accepted(self, status):
        data = ProductCreate(sku="SKU-3", name="Item", unit_price=Decimal("1"), status=status)
        assert data.status == status

    def test_invalid_status_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-4", name="Item", unit_price=Decimal("1"), status="deleted")

    def test_negative_unit_price_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-5", name="Item", unit_price=Decimal("-1"))

    def test_negative_cost_price_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-6", name="Item", unit_price=Decimal("1"), cost_price=Decimal("-5"))

    def test_negative_quantity_in_stock_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-7", name="Item", unit_price=Decimal("1"), quantity_in_stock=-1)

    def test_negative_reorder_level_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-7b", name="Item", unit_price=Decimal("1"), reorder_level=-5)

    def test_empty_sku_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="", name="Item", unit_price=Decimal("1"))

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-8", name="", unit_price=Decimal("1"))

    def test_zero_weight_raises(self):
        """weight uses gt=0, so zero is rejected."""
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-9", name="Item", unit_price=Decimal("1"), weight=0)

    def test_negative_weight_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(sku="SKU-10", name="Item", unit_price=Decimal("1"), weight=-2.5)

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="Item")

    def test_zero_unit_price_allowed(self):
        """unit_price uses ge=0, so zero should be accepted."""
        data = ProductCreate(sku="SKU-11", name="Free Item", unit_price=Decimal("0"))
        assert data.unit_price == Decimal("0")


class TestProductUpdateSchema:
    """Tests for the ProductUpdate request schema."""

    def test_all_fields_optional(self):
        data = ProductUpdate()
        assert data.sku is None
        assert data.name is None
        assert data.status is None

    def test_partial_update(self):
        data = ProductUpdate(name="New Name", unit_price=Decimal("50.00"))
        assert data.name == "New Name"
        assert data.unit_price == Decimal("50.00")
        assert data.sku is None

    @pytest.mark.parametrize("status", ["active", "discontinued", "draft"])
    def test_valid_status_values_accepted(self, status):
        data = ProductUpdate(status=status)
        assert data.status == status

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            ProductUpdate(status="unknown")

    def test_none_status_short_circuits_validator(self):
        data = ProductUpdate(status=None)
        assert data.status is None

    def test_negative_unit_price_raises(self):
        with pytest.raises(ValidationError):
            ProductUpdate(unit_price=Decimal("-1"))


class TestMovementCreateSchema:
    """Tests for the MovementCreate request schema."""

    @pytest.mark.parametrize("movement_type", ["in", "out", "adjustment", "transfer"])
    def test_valid_movement_types_accepted(self, movement_type):
        data = MovementCreate(product_id=1, movement_type=movement_type, quantity=10)
        assert data.movement_type == movement_type

    def test_invalid_movement_type_raises(self):
        with pytest.raises(ValidationError):
            MovementCreate(product_id=1, movement_type="scrap", quantity=10)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValidationError):
            MovementCreate(product_id=1, movement_type="in", quantity=-5)

    def test_zero_quantity_allowed(self):
        data = MovementCreate(product_id=1, movement_type="in", quantity=0)
        assert data.quantity == 0

    def test_product_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            MovementCreate(product_id=0, movement_type="in", quantity=10)

    def test_optional_fields_default_to_none(self):
        data = MovementCreate(product_id=1, movement_type="in", quantity=10)
        assert data.unit_cost is None
        assert data.reference is None
        assert data.notes is None


class TestProductResponseSchema:
    """Tests for the ProductResponse schema."""

    def _payload(self, **overrides):
        payload = dict(
            id=1,
            sku="SKU-1",
            name="Widget",
            description=None,
            category=None,
            unit_price=Decimal("9.99"),
            cost_price=None,
            quantity_in_stock=10,
            reorder_level=10,
            reorder_quantity=50,
            supplier=None,
            supplier_contact=None,
            status="active",
            barcode=None,
            weight=None,
            dimensions=None,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        payload.update(overrides)
        return payload

    def test_construct_from_dict(self):
        resp = ProductResponse(**self._payload())
        assert resp.id == 1
        assert resp.unit_price == Decimal("9.99")
        assert resp.status == "active"

    def test_missing_required_field_raises(self):
        payload = self._payload()
        del payload["sku"]
        with pytest.raises(ValidationError):
            ProductResponse(**payload)


class TestMovementResponseSchema:
    """Tests for the MovementResponse schema."""

    def test_construct_from_dict(self):
        resp = MovementResponse(
            id=1,
            product_id=2,
            movement_type="in",
            quantity=5,
            unit_cost=None,
            reference=None,
            notes=None,
            created_by=1,
            created_at="2024-01-01T00:00:00",
        )
        assert resp.movement_type == "in"
        assert resp.quantity == 5


class TestDashboardResponseSchema:
    """Tests for the DashboardResponse schema."""

    def test_construct(self):
        resp = DashboardResponse(
            total_products=10,
            total_stock_value=1000.0,
            low_stock_count=2,
            out_of_stock=1,
            categories=[{"category": "A", "product_count": 5, "total_value": 500.0}],
        )
        assert resp.total_products == 10
        assert len(resp.categories) == 1

    def test_empty_categories_allowed(self):
        resp = DashboardResponse(
            total_products=0,
            total_stock_value=0.0,
            low_stock_count=0,
            out_of_stock=0,
            categories=[],
        )
        assert resp.categories == []


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_current_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = 1
    return user


@pytest.fixture
def mock_service():
    """Create a mock InventoryService."""
    return MagicMock(spec=InventoryService)


class TestGetInventoryServiceDependency:
    """Tests for the get_inventory_service dependency provider."""

    def test_returns_inventory_service_bound_to_db(self, mock_db):
        service = get_inventory_service(db=mock_db)

        assert isinstance(service, InventoryService)
        assert service.db is mock_db


class TestCreateProductEndpoint:
    """Tests for POST /products."""

    def test_create_product_success(self, mock_db, mock_current_user, mock_service):
        mock_product = MagicMock(id=42)
        mock_service.create_product.return_value = mock_product
        data = ProductCreate(sku="SKU-100", name="New Product", unit_price=Decimal("10.00"))

        with patch("app.routers.inventory.log_activity") as mock_log:
            result = create_product(
                data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert result is mock_product
        mock_service.create_product.assert_called_once_with(
            sku="SKU-100",
            name="New Product",
            unit_price=Decimal("10.00"),
            description=None,
            category=None,
            cost_price=None,
            quantity_in_stock=0,
            reorder_level=10,
            reorder_quantity=50,
            supplier=None,
            supplier_contact=None,
            status="active",
            barcode=None,
            weight=None,
            dimensions=None,
            created_by=1,
        )
        mock_log.assert_called_once_with(
            mock_db,
            user_id=1,
            action="product_created",
            entity_type="product",
            entity_id=42,
        )

    def test_create_product_value_error_raises_400(self, mock_db, mock_current_user, mock_service):
        mock_service.create_product.side_effect = ValueError("Product with SKU 'SKU-1' already exists")
        data = ProductCreate(sku="SKU-1", name="Dup", unit_price=Decimal("10.00"))

        with pytest.raises(HTTPException) as exc_info:
            create_product(data=data, db=mock_db, current_user=mock_current_user, service=mock_service)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    def test_create_product_does_not_log_on_failure(self, mock_db, mock_current_user, mock_service):
        mock_service.create_product.side_effect = ValueError("Unit price cannot be negative")
        data = ProductCreate(sku="SKU-2", name="Bad Product", unit_price=Decimal("0"))

        with patch("app.routers.inventory.log_activity") as mock_log:
            with pytest.raises(HTTPException):
                create_product(data=data, db=mock_db, current_user=mock_current_user, service=mock_service)

        mock_log.assert_not_called()


class TestListProductsEndpoint:
    """Tests for GET /products."""

    def test_list_products_passes_filters_through(self, mock_db, mock_current_user, mock_service):
        mock_service.list_products.return_value = ["p1", "p2"]

        result = list_products(
            category="Electronics",
            status="active",
            low_stock=True,
            search="widget",
            skip=5,
            limit=10,
            db=mock_db,
            current_user=mock_current_user,
            service=mock_service,
        )

        assert result == ["p1", "p2"]
        mock_service.list_products.assert_called_once_with(
            category="Electronics",
            status="active",
            low_stock=True,
            search="widget",
            skip=5,
            limit=10,
        )

    def test_list_products_uses_defaults(self, mock_db, mock_current_user, mock_service):
        mock_service.list_products.return_value = []

        list_products(
            category=None,
            status=None,
            low_stock=False,
            search=None,
            skip=0,
            limit=100,
            db=mock_db,
            current_user=mock_current_user,
            service=mock_service,
        )

        mock_service.list_products.assert_called_once_with(
            category=None, status=None, low_stock=False, search=None, skip=0, limit=100
        )


class TestGetProductEndpoint:
    """Tests for GET /products/{product_id}."""

    def test_get_product_found(self, mock_db, mock_current_user, mock_service):
        mock_product = MagicMock(id=1)
        mock_service.get_product.return_value = mock_product

        result = get_product(product_id=1, db=mock_db, current_user=mock_current_user, service=mock_service)

        assert result is mock_product
        mock_service.get_product.assert_called_once_with(1)

    def test_get_product_not_found_raises_404(self, mock_db, mock_current_user, mock_service):
        mock_service.get_product.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_product(product_id=999, db=mock_db, current_user=mock_current_user, service=mock_service)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestUpdateProductEndpoint:
    """Tests for PUT /products/{product_id}."""

    def test_update_product_no_fields_raises_400(self, mock_db, mock_current_user, mock_service):
        data = ProductUpdate()

        with pytest.raises(HTTPException) as exc_info:
            update_product(
                product_id=1, data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert exc_info.value.status_code == 400
        assert "No fields to update" in exc_info.value.detail
        mock_service.update_product.assert_not_called()

    def test_update_product_success(self, mock_db, mock_current_user, mock_service):
        mock_product = MagicMock(id=1)
        mock_service.update_product.return_value = mock_product
        data = ProductUpdate(name="Updated Name")

        with patch("app.routers.inventory.log_activity") as mock_log:
            result = update_product(
                product_id=1, data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert result is mock_product
        mock_service.update_product.assert_called_once_with(
            product_id=1, updates={"name": "Updated Name"}, updated_by=1
        )
        mock_log.assert_called_once_with(
            mock_db,
            user_id=1,
            action="product_updated",
            entity_type="product",
            entity_id=1,
        )

    def test_update_product_filters_none_values(self, mock_db, mock_current_user, mock_service):
        mock_product = MagicMock(id=1)
        mock_service.update_product.return_value = mock_product
        data = ProductUpdate(name="Only Name", category=None, unit_price=Decimal("25.00"))

        with patch("app.routers.inventory.log_activity"):
            update_product(
                product_id=1, data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        called_updates = mock_service.update_product.call_args.kwargs["updates"]
        assert "category" not in called_updates
        assert called_updates == {"name": "Only Name", "unit_price": Decimal("25.00")}

    def test_update_product_not_found_raises_404(self, mock_db, mock_current_user, mock_service):
        mock_service.update_product.return_value = None
        data = ProductUpdate(name="Updated Name")

        with pytest.raises(HTTPException) as exc_info:
            update_product(
                product_id=999, data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert exc_info.value.status_code == 404

    def test_update_product_value_error_raises_400(self, mock_db, mock_current_user, mock_service):
        mock_service.update_product.side_effect = ValueError("Product with SKU 'X' already exists")
        data = ProductUpdate(sku="X")

        with pytest.raises(HTTPException) as exc_info:
            update_product(
                product_id=1, data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


class TestDeleteProductEndpoint:
    """Tests for DELETE /products/{product_id}."""

    def test_delete_product_success(self, mock_db, mock_current_user, mock_service):
        mock_service.delete_product.return_value = True

        with patch("app.routers.inventory.log_activity") as mock_log:
            result = delete_product(
                product_id=1, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert result == {"message": "Product deleted successfully"}
        mock_log.assert_called_once_with(
            mock_db,
            user_id=1,
            action="product_deleted",
            entity_type="product",
            entity_id=1,
        )

    def test_delete_product_not_found_raises_404(self, mock_db, mock_current_user, mock_service):
        mock_service.delete_product.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            delete_product(
                product_id=999, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert exc_info.value.status_code == 404

    def test_delete_product_not_found_does_not_log(self, mock_db, mock_current_user, mock_service):
        mock_service.delete_product.return_value = False

        with patch("app.routers.inventory.log_activity") as mock_log:
            with pytest.raises(HTTPException):
                delete_product(
                    product_id=999, db=mock_db, current_user=mock_current_user, service=mock_service
                )

        mock_log.assert_not_called()


class TestCreateMovementEndpoint:
    """Tests for POST /movements."""

    def test_create_movement_success(self, mock_db, mock_current_user, mock_service):
        mock_movement = MagicMock(id=10)
        mock_service.create_stock_movement.return_value = mock_movement
        data = MovementCreate(product_id=1, movement_type="in", quantity=5)

        with patch("app.routers.inventory.log_activity") as mock_log:
            result = create_movement(
                data=data, db=mock_db, current_user=mock_current_user, service=mock_service
            )

        assert result is mock_movement
        mock_service.create_stock_movement.assert_called_once_with(
            product_id=1,
            movement_type="in",
            quantity=5,
            unit_cost=None,
            reference=None,
            notes=None,
            created_by=1,
        )
        mock_log.assert_called_once_with(
            mock_db,
            user_id=1,
            action="inventory_moved",
            entity_type="inventory_movement",
            entity_id=10,
        )

    def test_create_movement_value_error_raises_400(self, mock_db, mock_current_user, mock_service):
        mock_service.create_stock_movement.side_effect = ValueError("Insufficient stock")
        data = MovementCreate(product_id=1, movement_type="out", quantity=1000)

        with pytest.raises(HTTPException) as exc_info:
            create_movement(data=data, db=mock_db, current_user=mock_current_user, service=mock_service)

        assert exc_info.value.status_code == 400
        assert "Insufficient stock" in exc_info.value.detail


class TestListMovementsEndpoint:
    """Tests for GET /movements."""

    def test_list_movements_passes_filters_through(self, mock_db, mock_current_user, mock_service):
        mock_service.get_movements.return_value = ["m1"]

        result = list_movements(
            product_id=1,
            movement_type="in",
            skip=0,
            limit=50,
            db=mock_db,
            current_user=mock_current_user,
            service=mock_service,
        )

        assert result == ["m1"]
        mock_service.get_movements.assert_called_once_with(
            product_id=1, movement_type="in", skip=0, limit=50
        )

    def test_list_movements_uses_defaults(self, mock_db, mock_current_user, mock_service):
        mock_service.get_movements.return_value = []

        list_movements(
            product_id=None,
            movement_type=None,
            skip=0,
            limit=100,
            db=mock_db,
            current_user=mock_current_user,
            service=mock_service,
        )

        mock_service.get_movements.assert_called_once_with(
            product_id=None, movement_type=None, skip=0, limit=100
        )


class TestInventoryDashboardEndpoint:
    """Tests for GET /dashboard."""

    def test_dashboard_returns_service_stats(self, mock_db, mock_current_user, mock_service):
        stats = {
            "total_products": 5,
            "total_stock_value": 100.0,
            "low_stock_count": 1,
            "out_of_stock": 0,
            "categories": [],
        }
        mock_service.get_dashboard_stats.return_value = stats

        result = inventory_dashboard(db=mock_db, current_user=mock_current_user, service=mock_service)

        assert result == stats
        mock_service.get_dashboard_stats.assert_called_once_with()


class TestLowStockAlertsEndpoint:
    """Tests for GET /alerts/low-stock."""

    def test_low_stock_alerts_default_limit(self, mock_db, mock_current_user, mock_service):
        mock_service.get_low_stock_products.return_value = ["p1"]

        result = get_low_stock_alerts(
            limit=50, db=mock_db, current_user=mock_current_user, service=mock_service
        )

        assert result == ["p1"]
        mock_service.get_low_stock_products.assert_called_once_with(limit=50)

    def test_low_stock_alerts_custom_limit(self, mock_db, mock_current_user, mock_service):
        mock_service.get_low_stock_products.return_value = []

        get_low_stock_alerts(limit=5, db=mock_db, current_user=mock_current_user, service=mock_service)

        mock_service.get_low_stock_products.assert_called_once_with(limit=5)


class TestOutOfStockAlertsEndpoint:
    """Tests for GET /alerts/out-of-stock."""

    def test_out_of_stock_alerts(self, mock_db, mock_current_user, mock_service):
        mock_service.get_out_of_stock_products.return_value = ["p2"]

        result = get_out_of_stock_alerts(db=mock_db, current_user=mock_current_user, service=mock_service)

        assert result == ["p2"]
        mock_service.get_out_of_stock_products.assert_called_once_with()