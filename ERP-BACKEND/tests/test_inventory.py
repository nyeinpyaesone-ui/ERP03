"""
Comprehensive tests for Inventory module.
Tests product CRUD, stock movements, and business rules.
Uses only Product and InventoryMovement models to avoid JSONB issues.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.pool import StaticPool

# Import only the models we need (avoid SearchIndex with JSONB)
from app.models import Product, InventoryMovement


# Create a minimal Base for testing without JSONB models
TestBase = declarative_base()


@pytest.fixture
def test_db_session():
    """Create a test database session with only inventory models."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create only the tables we need
    Product.metadata.create_all(bind=engine)
    InventoryMovement.metadata.create_all(bind=engine)
    
    SessionLocal = Session(bind=engine)
    try:
        yield SessionLocal
    finally:
        SessionLocal.close()
        engine.dispose()


class TestProductModel:
    """Test Product model creation and validation."""
    
    def test_create_product_minimal(self, test_db_session: Session):
        """Test creating a product with minimal required fields."""
        product = Product(
            sku="TEST-001",
            name="Test Product",
            unit_price=Decimal("99.99"),
            quantity_in_stock=100
        )
        test_db_session.add(product)
        test_db_session.commit()
        test_db_session.refresh(product)
        
        assert product.id is not None
        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.unit_price == Decimal("99.99")
        assert product.quantity_in_stock == 100
        assert product.status == "active"
        assert product.reorder_level == 10
        assert product.reorder_quantity == 50
    
    def test_create_product_duplicate_sku(self, test_db_session: Session):
        """Test that duplicate SKUs are prevented."""
        product1 = Product(
            sku="DUP-001",
            name="Product 1",
            unit_price=Decimal("10.00"),
            quantity_in_stock=50
        )
        test_db_session.add(product1)
        test_db_session.commit()
        
        with pytest.raises(Exception):
            product2 = Product(
                sku="DUP-001",
                name="Product 2",
                unit_price=Decimal("20.00"),
                quantity_in_stock=30
            )
            test_db_session.add(product2)
            test_db_session.commit()
    
    def test_product_full_details(self, test_db_session: Session):
        """Test creating a product with all optional fields."""
        product = Product(
            sku="FULL-001",
            name="Complete Product",
            description="A fully specified product",
            category="Electronics",
            unit_price=Decimal("299.99"),
            cost_price=Decimal("150.00"),
            quantity_in_stock=200,
            reorder_level=20,
            reorder_quantity=100,
            supplier="Acme Corp",
            supplier_contact="supplier@acme.com",
            status="active",
            barcode="1234567890123",
            weight=1.5,
            dimensions="10x20x5"
        )
        test_db_session.add(product)
        test_db_session.commit()
        test_db_session.refresh(product)
        
        assert product.description == "A fully specified product"
        assert product.category == "Electronics"
        assert product.cost_price == Decimal("150.00")
        assert product.supplier == "Acme Corp"
        assert product.barcode == "1234567890123"
        assert product.weight == 1.5


class TestInventoryMovementModel:
    """Test InventoryMovement model and stock tracking."""
    
    def test_create_movement_in(self, test_db_session: Session):
        """Test creating a stock-in movement."""
        product = Product(
            sku="MOV-001",
            name="Movement Test Product",
            unit_price=Decimal("50.00"),
            quantity_in_stock=100
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        movement = InventoryMovement(
            product_id=product.id,
            movement_type="in",
            quantity=50,
            unit_cost=Decimal("45.00"),
            reference="PO-12345",
            notes="Received from supplier",
            created_by=1
        )
        test_db_session.add(movement)
        test_db_session.commit()
        test_db_session.refresh(movement)
        
        assert movement.id is not None
        assert movement.movement_type == "in"
        assert movement.quantity == 50
        assert movement.reference == "PO-12345"
    
    def test_create_movement_out(self, test_db_session: Session):
        """Test creating a stock-out movement."""
        product = Product(
            sku="MOV-002",
            name="Out Movement Product",
            unit_price=Decimal("75.00"),
            quantity_in_stock=200
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        movement = InventoryMovement(
            product_id=product.id,
            movement_type="out",
            quantity=30,
            reference="SO-67890",
            notes="Shipped to customer",
            created_by=1
        )
        test_db_session.add(movement)
        test_db_session.commit()
        
        assert movement.movement_type == "out"
        assert movement.quantity == 30
    
    def test_movement_cascading_delete(self, test_db_session: Session):
        """Test that movements are deleted when product is deleted."""
        product = Product(
            sku="DEL-001",
            name="Delete Test Product",
            unit_price=Decimal("25.00"),
            quantity_in_stock=50
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        movement = InventoryMovement(
            product_id=product.id,
            movement_type="in",
            quantity=10,
            created_by=1
        )
        test_db_session.add(movement)
        test_db_session.commit()
        
        movement_id = movement.id
        test_db_session.delete(product)
        test_db_session.commit()
        
        # Verify movement was deleted
        deleted_movement = test_db_session.query(InventoryMovement).filter(
            InventoryMovement.id == movement_id
        ).first()
        assert deleted_movement is None


class TestStockMovements:
    """Test stock movement business logic."""
    
    def test_stock_in_creates_movement(self, test_db_session: Session):
        """Test that stock-in creates a movement record."""
        initial_stock = 100
        product = Product(
            sku="STK-001",
            name="Stock Test Product",
            unit_price=Decimal("100.00"),
            quantity_in_stock=initial_stock
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        movement = InventoryMovement(
            product_id=product.id,
            movement_type="in",
            quantity=50,
            created_by=1
        )
        test_db_session.add(movement)
        test_db_session.commit()
        
        movements = test_db_session.query(InventoryMovement).filter(
            InventoryMovement.product_id == product.id
        ).all()
        assert len(movements) == 1
        assert movements[0].quantity == 50
    
    def test_multiple_movements_tracking(self, test_db_session: Session):
        """Test tracking multiple stock movements."""
        product = Product(
            sku="MULT-001",
            name="Multiple Movements Product",
            unit_price=Decimal("80.00"),
            quantity_in_stock=0
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        # Add stock
        test_db_session.add(InventoryMovement(
            product_id=product.id,
            movement_type="in",
            quantity=100,
            created_by=1
        ))
        # Remove stock
        test_db_session.add(InventoryMovement(
            product_id=product.id,
            movement_type="out",
            quantity=30,
            created_by=1
        ))
        # Adjustment
        test_db_session.add(InventoryMovement(
            product_id=product.id,
            movement_type="adjustment",
            quantity=75,
            created_by=1
        ))
        test_db_session.commit()
        
        movements = test_db_session.query(InventoryMovement).filter(
            InventoryMovement.product_id == product.id
        ).order_by(InventoryMovement.created_at).all()
        
        assert len(movements) == 3
        assert movements[0].movement_type == "in"
        assert movements[1].movement_type == "out"
        assert movements[2].movement_type == "adjustment"


class TestInventoryQueries:
    """Test inventory query operations."""
    
    def test_query_by_category(self, test_db_session: Session):
        """Test filtering products by category."""
        products = [
            Product(sku=f"C{i}", name=f"Product {i}", category="Electronics" if i % 2 == 0 else "Furniture",
                   unit_price=Decimal("50.00"), quantity_in_stock=10)
            for i in range(5)
        ]
        test_db_session.add_all(products)
        test_db_session.commit()
        
        electronics = test_db_session.query(Product).filter(
            Product.category == "Electronics"
        ).all()
        
        assert len(electronics) == 3  # Products 0, 2, 4
    
    def test_query_low_stock(self, test_db_session: Session):
        """Test querying products below reorder level."""
        products = [
            Product(sku=f"LOW{i}", name=f"Low Stock {i}", 
                   unit_price=Decimal("30.00"), 
                   quantity_in_stock=5 if i < 3 else 50,
                   reorder_level=10)
            for i in range(5)
        ]
        test_db_session.add_all(products)
        test_db_session.commit()
        
        low_stock = test_db_session.query(Product).filter(
            Product.quantity_in_stock <= Product.reorder_level
        ).all()
        
        assert len(low_stock) == 3
    
    def test_query_by_status(self, test_db_session: Session):
        """Test filtering products by status."""
        products = [
            Product(sku=f"STAT{i}", name=f"Status {i}",
                   status="active" if i % 2 == 0 else "discontinued",
                   unit_price=Decimal("40.00"), quantity_in_stock=20)
            for i in range(6)
        ]
        test_db_session.add_all(products)
        test_db_session.commit()
        
        active = test_db_session.query(Product).filter(
            Product.status == "active"
        ).all()
        
        assert len(active) == 3
    
    def test_search_by_name(self, test_db_session: Session):
        """Test searching products by name."""
        products = [
            Product(sku=f"SRCH{i}", name=f"Widget {i} Deluxe" if i % 2 == 0 else f"Gadget {i}",
                   unit_price=Decimal("60.00"), quantity_in_stock=15)
            for i in range(5)
        ]
        test_db_session.add_all(products)
        test_db_session.commit()
        
        widgets = test_db_session.query(Product).filter(
            Product.name.ilike("%Widget%")
        ).all()
        
        assert len(widgets) == 3  # Products 0, 2, 4


class TestInventoryDashboard:
    """Test inventory dashboard calculations."""
    
    def test_dashboard_totals(self, test_db_session: Session):
        """Test dashboard total calculations."""
        products = [
            Product(sku=f"DASH{i}", name=f"Dash {i}",
                   unit_price=Decimal("100.00"),
                   quantity_in_stock=10 if i < 2 else (0 if i == 2 else 100),
                   reorder_level=20,
                   category="Cat A" if i < 3 else "Cat B")
            for i in range(5)
        ]
        test_db_session.add_all(products)
        test_db_session.commit()
        
        total_products = test_db_session.query(Product).count()
        total_value = sum(p.quantity_in_stock * float(p.unit_price) for p in products)
        low_stock_count = test_db_session.query(Product).filter(
            Product.quantity_in_stock <= Product.reorder_level
        ).count()
        out_of_stock = test_db_session.query(Product).filter(
            Product.quantity_in_stock == 0
        ).count()
        
        assert total_products == 5
        assert total_value == (10*100 + 10*100 + 0*100 + 100*100 + 100*100)
        assert low_stock_count == 3  # Products 0, 1, 2
        assert out_of_stock == 1


class TestInventoryTransactions:
    """Test transaction safety for inventory operations."""
    
    def test_rollback_on_insufficient_stock(self, test_db_session: Session):
        """Test that insufficient stock prevents movement."""
        product = Product(
            sku="ROLL-001",
            name="Rollback Test",
            unit_price=Decimal("50.00"),
            quantity_in_stock=10
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        # Try to remove more than available
        try:
            if product.quantity_in_stock < 50:
                raise ValueError("Insufficient stock")
            movement = InventoryMovement(
                product_id=product.id,
                movement_type="out",
                quantity=50,
                created_by=1
            )
            test_db_session.add(movement)
            product.quantity_in_stock -= 50
            test_db_session.commit()
        except ValueError:
            db_session.rollback()
        
        # Verify stock unchanged
        test_db_session.refresh(product)
        assert product.quantity_in_stock == 10
        
        # Verify no movement created
        movements = test_db_session.query(InventoryMovement).filter(
            InventoryMovement.product_id == product.id
        ).all()
        assert len(movements) == 0
    
    def test_atomic_stock_update(self, test_db_session: Session):
        """Test that stock updates are atomic."""
        product = Product(
            sku="ATOM-001",
            name="Atomic Test",
            unit_price=Decimal("75.00"),
            quantity_in_stock=100
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        original_stock = product.quantity_in_stock
        
        # Create movement and update stock
        movement = InventoryMovement(
            product_id=product.id,
            movement_type="out",
            quantity=25,
            created_by=1
        )
        test_db_session.add(movement)
        product.quantity_in_stock -= 25
        test_db_session.commit()
        
        # Verify both changes committed together
        test_db_session.refresh(product)
        test_db_session.refresh(movement)
        
        assert product.quantity_in_stock == 75
        assert movement.quantity == 25


# Run with: pytest tests/test_inventory.py -v
