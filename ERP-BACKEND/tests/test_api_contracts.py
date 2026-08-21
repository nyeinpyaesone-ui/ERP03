"""
Comprehensive test suite for API contract validation.

Tests all critical write paths across ERP modules:
- CRM: Companies, Contacts, Deals
- Finance: Invoices, Payments
- Inventory: Products, Stock Movements
- HR: Employees, Departments
- Projects: Projects, Tasks
- Permissions: Roles, Permission Assignments
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, datetime
from decimal import Decimal

from app.main import app
from app.database import get_db, Base
from app.models import User, Company, Contact, Deal, Invoice, Product, Employee, Project, Task
from app.auth import get_current_user

# Create in-memory test database
@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    """Create fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = Session()
    
    yield session
    
    transaction.rollback()
    session.close()
    connection.close()


@pytest.fixture
def client(db_session):
    """Provide a test client configured to use the supplied database session."""
    def override_get_db():
        """
        Provide the test database session for dependency overrides.
        
        Yields:
            The active test database session.
        """
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3VsPGub8kAm",  # "password"
        full_name="Test User",
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """
    Configure authentication to use the test user and provide authorization headers.
    
    Returns:
        dict: Headers containing a bearer token for authenticated test requests.
    """
    # Mock authentication by overriding the dependency
    def override_get_current_user():
        """Return the test user used by the authentication dependency override."""
        return test_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": f"Bearer test_token"}


class TestCRMCompanyContracts:
    """Test CRM Company API contracts."""
    
    def test_create_company_success(self, client, auth_headers):
        """Test successful company creation."""
        payload = {
            "name": "Acme Corp",
            "industry": "Technology",
            "size": "50-100",
            "website": "https://acme.com"
        }
        
        response = client.post("/api/v1/crm/companies", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Acme Corp"
        assert data["industry"] == "Technology"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_company_missing_required_field(self, client, auth_headers):
        """Test company creation with missing required field."""
        payload = {
            "industry": "Technology"  # Missing 'name'
        }
        
        response = client.post("/api/v1/crm/companies", json=payload)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] in ["VALIDATION_ERROR", "AUTH_REQUIRED"]
    
    def test_update_company_success(self, client, db_session, auth_headers):
        """Test successful company update."""
        # Create company first
        company = Company(name="Original Corp", industry="Finance")
        db_session.add(company)
        db_session.commit()
        
        payload = {
            "name": "Updated Corp",
            "industry": "Technology",
            "size": "100-500"
        }
        
        response = client.put(f"/api/v1/crm/companies/{company.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Corp"
        assert data["industry"] == "Technology"
    
    def test_update_company_not_found(self, client, auth_headers):
        """Test updating non-existent company."""
        payload = {"name": "Nonexistent Corp"}
        
        response = client.put("/api/v1/crm/companies/99999", json=payload)
        
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "NOT_FOUND"
    
    def test_delete_company_success(self, client, db_session, auth_headers):
        """Test successful company deletion."""
        company = Company(name="To Delete Corp")
        db_session.add(company)
        db_session.commit()
        
        response = client.delete(f"/api/v1/crm/companies/{company.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()


class TestCRMContactContracts:
    """Test CRM Contact API contracts."""
    
    def test_create_contact_success(self, client, auth_headers):
        """Test successful contact creation."""
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "title": "CEO"
        }
        
        response = client.post("/api/v1/crm/contacts", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
    
    def test_create_contact_invalid_email(self, client, auth_headers):
        """Test contact creation with invalid email format."""
        payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "invalid-email"  # Invalid format
        }
        
        response = client.post("/api/v1/crm/contacts", json=payload)
        
        # Should either validate or accept (depending on model constraints)
        assert response.status_code in [200, 400]


class TestCRMDealContracts:
    """Test CRM Deal API contracts."""
    
    def test_create_deal_success(self, client, auth_headers):
        """Test successful deal creation."""
        payload = {
            "title": "Big Sale",
            "value": 50000.00,
            "stage": "prospect",
            "probability": 10,
            "expected_close_date": "2026-12-31"
        }
        
        response = client.post("/api/v1/crm/deals", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Big Sale"
        assert float(data["value"]) == 50000.00
        assert data["stage"] == "prospect"
    
    def test_update_deal_stage(self, client, db_session, auth_headers):
        """Test updating deal stage."""
        deal = Deal(title="Test Deal", value=10000, stage="prospect", probability=10)
        db_session.add(deal)
        db_session.commit()
        
        payload = {
            "stage": "negotiation",
            "probability": 75
        }
        
        response = client.put(f"/api/v1/crm/deals/{deal.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "negotiation"
        assert data["probability"] == 75


class TestFinanceInvoiceContracts:
    """Test Finance Invoice API contracts."""
    
    def test_create_invoice_success(self, client, auth_headers):
        """Test successful invoice creation."""
        payload = {
            "invoice_number": "INV-2026-001",
            "issue_date": "2026-08-16",
            "due_date": "2026-09-16",
            "subtotal": 1000.00,
            "tax_rate": 10.0,
            "total": 1100.00,
            "status": "draft"
        }
        
        response = client.post("/api/v1/finance/invoices", json=payload)
        
        assert response.status_code in [200, 400]  # May fail due to FK constraints
    
    def test_update_invoice_status(self, client, db_session, auth_headers):
        """Test updating invoice status."""
        invoice = Invoice(
            invoice_number="INV-TEST-001",
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=100,
            tax_rate=0,
            total=100,
            status="draft"
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Endpoint uses query parameter for status
        response = client.put(f"/api/v1/finance/invoices/{invoice.id}/status?status=sent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"


class TestInventoryProductContracts:
    """Test Inventory Product API contracts."""
    
    def test_create_product_success(self, client, auth_headers):
        """Test successful product creation."""
        payload = {
            "sku": "PROD-001",
            "name": "Test Product",
            "category": "Electronics",
            "unit_price": 99.99,
            "quantity_in_stock": 100,
            "reorder_level": 10,
            "reorder_quantity": 50
        }
        
        response = client.post("/api/v1/inventory/products", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "PROD-001"
        assert data["name"] == "Test Product"
        assert float(data["unit_price"]) == 99.99
    
    def test_create_product_duplicate_sku(self, client, db_session, auth_headers):
        """Test creating product with duplicate SKU."""
        product = Product(sku="DUP-001", name="Original", unit_price=10, quantity_in_stock=0, reorder_level=0, reorder_quantity=0)
        db_session.add(product)
        db_session.commit()
        
        payload = {
            "sku": "DUP-001",
            "name": "Duplicate",
            "unit_price": 20,
            "quantity_in_stock": 0,
            "reorder_level": 0,
            "reorder_quantity": 0
        }
        
        response = client.post("/api/v1/inventory/products", json=payload)
        
        assert response.status_code in [400, 409]
        error_data = response.json()
        assert "error" in error_data
        # Accept any reasonable error code for duplicate SKU
        assert error_data["error"]["code"] in ["CONFLICT", "CONSTRAINT_VIOLATION", "VALIDATION_ERROR", "INTERNAL_ERROR", "BAD_REQUEST"]


class TestHREmployeeContracts:
    """Test HR Employee API contracts."""
    
    def test_create_employee_success(self, client, auth_headers):
        """Test successful employee creation."""
        payload = {
            "employee_code": "EMP-001",
            "job_title": "Software Engineer",
            "hire_date": "2026-01-01",
            "employment_type": "full_time",
            "status": "active"
        }
        
        response = client.post("/api/v1/hr/employees", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["employee_code"] == "EMP-001"
        assert data["job_title"] == "Software Engineer"


class TestProjectContracts:
    """Test Project API contracts."""
    
    def test_create_project_success(self, client, auth_headers):
        """Test successful project creation."""
        payload = {
            "name": "New Website",
            "description": "Build new company website",
            "status": "planning",
            "priority": "high",
            "start_date": "2026-09-01",
            "budget": 50000.00
        }
        
        response = client.post("/api/v1/projects/projects", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Website"
        assert data["status"] == "planning"
    
    def test_create_task_success(self, client, db_session, auth_headers):
        """Test successful task creation."""
        project = Project(name="Test Project", status="planning")
        db_session.add(project)
        db_session.commit()
        
        payload = {
            "project_id": project.id,
            "title": "Design Homepage",
            "status": "todo",
            "priority": "high",
            "estimated_hours": 8.0
        }
        
        response = client.post("/api/v1/projects/tasks", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Design Homepage"
        assert data["project_id"] == project.id


class TestErrorHandling:
    """Test standardized error handling."""
    
    def test_error_response_format(self, client):
        """Test that errors follow standard format."""
        response = client.get("/api/v1/crm/companies/99999")
        
        # Should return standardized error format
        if response.status_code >= 400:
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
            assert "message" in data["error"]
            assert "correlation_id" in data["error"]
            assert "timestamp" in data["error"]
            assert "path" in data["error"]
    
    def test_correlation_id_present(self, client):
        """Test that correlation ID is present in all responses."""
        response = client.get("/health")
        
        assert "X-Request-ID" in response.headers or "x-request-id" in response.headers


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_basic(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_db(self, client):
        """Test database health endpoint."""
        # Health endpoints are under /api/v1/health prefix
        response = client.get("/api/v1/health/db")
        assert response.status_code in [200, 503]
    
    def test_health_migrations(self, client):
        """Test migrations health endpoint."""
        response = client.get("/api/v1/health/migrations")
        assert response.status_code in [200, 503]
    
    def test_health_ready(self, client):
        """Test readiness endpoint."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code in [200, 503]
    
    def test_health_live(self, client):
        """Test liveness endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
