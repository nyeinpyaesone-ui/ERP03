"""
Unit tests for the finance domain package (app/domains/finance/).

Covers:
- domain.py: pure business logic (InvoiceLine, calculate_invoice_totals, is_overdue, validate_payment)
- infrastructure.py: FinanceRepository
- application.py: create_invoice, record_payment, get_invoice, list_invoices, dashboard
- interface.py: FastAPI router built by build_router()
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.database import get_db
from app.core.module_registry import ModuleRegistry
from app.domains.finance import application
import app.domains.finance.interface as finance_interface
from app.domains.finance.domain import (
    InvoiceLine,
    InvoiceTotals,
    calculate_invoice_totals,
    is_overdue,
    validate_payment,
)
from app.domains.finance.infrastructure import FinanceRepository
from app.models import Invoice, InvoiceItem, Payment


# ---------------------------------------------------------------------------
# domain.py
# ---------------------------------------------------------------------------

class TestInvoiceLine:
    def test_line_total_multiplies_quantity_and_unit_price(self):
        line = InvoiceLine(description="Widget", quantity=3, unit_price=10.5)
        assert line.line_total == 31.5

    def test_line_total_with_zero_quantity(self):
        line = InvoiceLine(description="Widget", quantity=0, unit_price=10.5)
        assert line.line_total == 0


class TestCalculateInvoiceTotals:
    def test_calculates_subtotal_tax_and_total(self):
        lines = [
            InvoiceLine(description="A", quantity=2, unit_price=10),
            InvoiceLine(description="B", quantity=1, unit_price=5),
        ]

        totals = calculate_invoice_totals(lines, tax_rate=10)

        assert isinstance(totals, InvoiceTotals)
        assert totals.subtotal == 25
        assert totals.tax_amount == 2.5
        assert totals.total == 27.5

    def test_zero_tax_rate(self):
        lines = [InvoiceLine(description="A", quantity=1, unit_price=100)]

        totals = calculate_invoice_totals(lines, tax_rate=0)

        assert totals.subtotal == 100
        assert totals.tax_amount == 0
        assert totals.total == 100

    def test_empty_lines_returns_zero_totals(self):
        totals = calculate_invoice_totals([], tax_rate=10)

        assert totals.subtotal == 0
        assert totals.tax_amount == 0
        assert totals.total == 0

    def test_negative_tax_rate_raises_value_error(self):
        lines = [InvoiceLine(description="A", quantity=1, unit_price=10)]

        with pytest.raises(ValueError, match="tax_rate cannot be negative"):
            calculate_invoice_totals(lines, tax_rate=-1)


class TestIsOverdue:
    def test_overdue_when_due_date_in_past_and_not_paid(self):
        today = date(2026, 1, 15)
        assert is_overdue(date(2026, 1, 1), "sent", today=today) is True

    def test_not_overdue_when_paid_even_if_due_date_in_past(self):
        today = date(2026, 1, 15)
        assert is_overdue(date(2026, 1, 1), "paid", today=today) is False

    def test_not_overdue_when_due_date_in_future(self):
        today = date(2026, 1, 15)
        assert is_overdue(date(2026, 2, 1), "sent", today=today) is False

    def test_not_overdue_when_due_date_is_today(self):
        today = date(2026, 1, 15)
        assert is_overdue(today, "sent", today=today) is False


class TestValidatePayment:
    def test_valid_payment_does_not_raise(self):
        validate_payment(50, 100, 0)

    def test_zero_amount_raises_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_payment(0, 100, 0)

    def test_negative_amount_raises_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_payment(-10, 100, 0)

    def test_payment_exceeding_total_raises_value_error(self):
        with pytest.raises(ValueError, match="exceed invoice total"):
            validate_payment(60, 100, 50)

    def test_payment_exactly_reaching_total_is_allowed(self):
        validate_payment(50, 100, 50)

    def test_handles_decimal_invoice_values_from_db(self):
        # Simulates values returned from a Numeric DB column
        validate_payment(25.0, Decimal("100.00"), Decimal("75.00"))

    def test_decimal_payment_exceeding_total_raises(self):
        with pytest.raises(ValueError, match="exceed invoice total"):
            validate_payment(30.0, Decimal("100.00"), Decimal("75.00"))


# ---------------------------------------------------------------------------
# infrastructure.py
# ---------------------------------------------------------------------------

class TestFinanceRepository:
    def test_invoice_number_exists_true(self, db_session):
        db_session.add(Invoice(
            invoice_number="INV-1", issue_date=date.today(), due_date=date.today(),
            subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft",
        ))
        db_session.commit()

        repo = FinanceRepository(db_session)
        assert repo.invoice_number_exists("INV-1") is True

    def test_invoice_number_exists_false(self, db_session):
        repo = FinanceRepository(db_session)
        assert repo.invoice_number_exists("DOES-NOT-EXIST") is False

    def test_next_invoice_number_formatting(self, db_session):
        repo = FinanceRepository(db_session)
        assert repo.next_invoice_number() == "INV-000001"

        db_session.add(Invoice(
            invoice_number="INV-existing", issue_date=date.today(), due_date=date.today(),
            subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft",
        ))
        db_session.commit()

        assert repo.next_invoice_number() == "INV-000002"

    def test_save_invoice_persists_invoice_and_items(self, db_session):
        repo = FinanceRepository(db_session)
        invoice = Invoice(
            invoice_number="INV-2", issue_date=date.today(), due_date=date.today(),
            subtotal=100, tax_rate=0, tax_amount=0, total=100, amount_paid=0, status="draft",
        )
        item = InvoiceItem(description="Widget", quantity=1, unit_price=100, total=100)

        saved = repo.save_invoice(invoice, [item])

        assert saved.id is not None
        assert item.invoice_id == saved.id
        assert db_session.query(InvoiceItem).filter(InvoiceItem.invoice_id == saved.id).count() == 1

    def test_get_invoice_returns_none_when_missing(self, db_session):
        repo = FinanceRepository(db_session)
        assert repo.get_invoice(999) is None

    def test_get_invoice_returns_saved_invoice(self, db_session):
        repo = FinanceRepository(db_session)
        invoice = Invoice(
            invoice_number="INV-3", issue_date=date.today(), due_date=date.today(),
            subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft",
        )
        db_session.add(invoice)
        db_session.commit()

        result = repo.get_invoice(invoice.id)
        assert result is not None
        assert result.invoice_number == "INV-3"

    def test_list_invoices_filters_by_status(self, db_session):
        db_session.add_all([
            Invoice(invoice_number="A", issue_date=date.today(), due_date=date.today(),
                    subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft"),
            Invoice(invoice_number="B", issue_date=date.today(), due_date=date.today(),
                    subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="paid"),
        ])
        db_session.commit()

        repo = FinanceRepository(db_session)
        result = repo.list_invoices(status="paid")

        assert len(result) == 1
        assert result[0].invoice_number == "B"

    def test_list_invoices_filters_by_contact_id(self, db_session):
        db_session.add_all([
            Invoice(invoice_number="A", contact_id=1, issue_date=date.today(), due_date=date.today(),
                    subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft"),
            Invoice(invoice_number="B", contact_id=2, issue_date=date.today(), due_date=date.today(),
                    subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft"),
        ])
        db_session.commit()

        repo = FinanceRepository(db_session)
        result = repo.list_invoices(contact_id=1)

        assert len(result) == 1
        assert result[0].invoice_number == "A"

    def test_list_invoices_no_filters_returns_all(self, db_session):
        db_session.add_all([
            Invoice(invoice_number="A", issue_date=date.today(), due_date=date.today(),
                    subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft"),
            Invoice(invoice_number="B", issue_date=date.today(), due_date=date.today(),
                    subtotal=0, tax_rate=0, tax_amount=0, total=0, amount_paid=0, status="draft"),
        ])
        db_session.commit()

        repo = FinanceRepository(db_session)
        assert len(repo.list_invoices()) == 2

    def test_save_payment_persists_payment(self, db_session):
        invoice = Invoice(
            invoice_number="INV-4", issue_date=date.today(), due_date=date.today(),
            subtotal=100, tax_rate=0, tax_amount=0, total=100, amount_paid=0, status="draft",
        )
        db_session.add(invoice)
        db_session.commit()

        repo = FinanceRepository(db_session)
        payment = Payment(invoice_id=invoice.id, amount=50, payment_method="cash", payment_date=date.today())

        saved = repo.save_payment(payment)

        assert saved.id is not None

    def test_dashboard_metrics_counts_overdue_invoices(self, db_session):
        past_due = date.today() - timedelta(days=5)
        db_session.add_all([
            Invoice(invoice_number="OVERDUE", issue_date=past_due, due_date=past_due,
                    subtotal=100, tax_rate=0, tax_amount=0, total=100, amount_paid=0, status="sent"),
            Invoice(invoice_number="PAID", issue_date=past_due, due_date=past_due,
                    subtotal=100, tax_rate=0, tax_amount=0, total=100, amount_paid=100, status="paid"),
        ])
        db_session.commit()

        repo = FinanceRepository(db_session)
        metrics = repo.dashboard_metrics(today=date.today())

        assert metrics["total_invoices"] == 2
        assert metrics["overdue"] == 1
        assert float(metrics["total_revenue"]) == 100.0
        assert float(metrics["outstanding"]) == 100.0

    def test_dashboard_metrics_with_no_invoices(self, db_session):
        repo = FinanceRepository(db_session)
        metrics = repo.dashboard_metrics(today=date.today())

        assert metrics["total_invoices"] == 0
        assert metrics["total_revenue"] == 0
        assert metrics["outstanding"] == 0
        assert metrics["overdue"] == 0


# ---------------------------------------------------------------------------
# application.py
# ---------------------------------------------------------------------------

class TestCreateInvoice:
    def test_creates_invoice_with_calculated_totals(self, db_session):
        invoice = application.create_invoice(
            db_session,
            invoice_number="INV-100",
            contact_id=None,
            company_id=None,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            tax_rate=10,
            notes=None,
            terms=None,
            items=[{"description": "Widget", "quantity": 2, "unit_price": 10}],
        )

        assert invoice.id is not None
        assert float(invoice.subtotal) == 20.0
        assert float(invoice.tax_amount) == 2.0
        assert float(invoice.total) == 22.0
        assert invoice.status == "draft"
        assert float(invoice.amount_paid) == 0.0

    def test_creates_associated_invoice_items(self, db_session):
        invoice = application.create_invoice(
            db_session,
            invoice_number="INV-101",
            contact_id=None,
            company_id=None,
            issue_date=date.today(),
            due_date=date.today(),
            tax_rate=0,
            notes=None,
            terms=None,
            items=[
                {"description": "Widget", "quantity": 2, "unit_price": 10},
                {"description": "Gadget", "quantity": 1, "unit_price": 5, "product_id": None},
            ],
        )

        items = db_session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).all()
        assert len(items) == 2

    def test_duplicate_invoice_number_raises_value_error(self, db_session):
        application.create_invoice(
            db_session, invoice_number="DUPLICATE", contact_id=None, company_id=None,
            issue_date=date.today(), due_date=date.today(), tax_rate=0, notes=None, terms=None,
            items=[{"description": "A", "quantity": 1, "unit_price": 1}],
        )

        with pytest.raises(ValueError, match="already exists"):
            application.create_invoice(
                db_session, invoice_number="DUPLICATE", contact_id=None, company_id=None,
                issue_date=date.today(), due_date=date.today(), tax_rate=0, notes=None, terms=None,
                items=[{"description": "B", "quantity": 1, "unit_price": 1}],
            )


class TestRecordPayment:
    def _create_invoice(self, db_session, total=100):
        return application.create_invoice(
            db_session, invoice_number=f"INV-{total}-{id(db_session)}", contact_id=None, company_id=None,
            issue_date=date.today(), due_date=date.today(), tax_rate=0, notes=None, terms=None,
            items=[{"description": "A", "quantity": 1, "unit_price": total}],
        )

    def test_partial_payment_sets_status_partial(self, db_session):
        invoice = self._create_invoice(db_session, total=100)

        payment = application.record_payment(
            db_session, invoice_id=invoice.id, amount=40, payment_method="cash", payment_date=date.today(),
        )

        db_session.refresh(invoice)
        assert payment.id is not None
        assert float(invoice.amount_paid) == 40.0
        assert invoice.status == "partial"

    def test_full_payment_sets_status_paid(self, db_session):
        invoice = self._create_invoice(db_session, total=100)

        application.record_payment(
            db_session, invoice_id=invoice.id, amount=100, payment_method="cash", payment_date=date.today(),
        )

        db_session.refresh(invoice)
        assert invoice.status == "paid"

    def test_payment_for_missing_invoice_raises_value_error(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            application.record_payment(
                db_session, invoice_id=999999, amount=10, payment_method="cash", payment_date=date.today(),
            )

    def test_payment_exceeding_total_raises_value_error(self, db_session):
        invoice = self._create_invoice(db_session, total=100)

        with pytest.raises(ValueError, match="exceed invoice total"):
            application.record_payment(
                db_session, invoice_id=invoice.id, amount=200, payment_method="cash", payment_date=date.today(),
            )


class TestGetAndListInvoices:
    def test_get_invoice_returns_none_when_missing(self, db_session):
        assert application.get_invoice(db_session, invoice_id=999999) is None

    def test_get_invoice_returns_created_invoice(self, db_session):
        created = application.create_invoice(
            db_session, invoice_number="INV-GET", contact_id=None, company_id=None,
            issue_date=date.today(), due_date=date.today(), tax_rate=0, notes=None, terms=None,
            items=[{"description": "A", "quantity": 1, "unit_price": 1}],
        )

        found = application.get_invoice(db_session, invoice_id=created.id)
        assert found.invoice_number == "INV-GET"

    def test_list_invoices_filters_by_status(self, db_session):
        application.create_invoice(
            db_session, invoice_number="INV-LIST-1", contact_id=None, company_id=None,
            issue_date=date.today(), due_date=date.today(), tax_rate=0, notes=None, terms=None,
            items=[{"description": "A", "quantity": 1, "unit_price": 1}],
        )

        results = application.list_invoices(db_session, status="draft")
        assert len(results) == 1
        assert results[0].invoice_number == "INV-LIST-1"


class TestApplicationDashboard:
    def test_dashboard_returns_metrics_dict(self, db_session):
        application.create_invoice(
            db_session, invoice_number="INV-DASH", contact_id=None, company_id=None,
            issue_date=date.today(), due_date=date.today(), tax_rate=0, notes=None, terms=None,
            items=[{"description": "A", "quantity": 1, "unit_price": 50}],
        )

        result = application.dashboard(db_session)

        assert result["total_invoices"] == 1


# ---------------------------------------------------------------------------
# interface.py
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_registry(monkeypatch):
    """Prevent interface.build_router() from mutating the global module registry."""
    fresh_registry = ModuleRegistry()
    monkeypatch.setattr(finance_interface, "registry", fresh_registry)
    return fresh_registry


@pytest.fixture
def finance_app(isolated_registry):
    app = FastAPI()
    router = finance_interface.build_router()
    app.include_router(router, prefix="/api/v1/finance")

    def override_get_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id=1)
    yield app
    app.dependency_overrides.clear()


class TestFinanceInterfaceRegistration:
    def test_build_router_registers_finance_module(self, isolated_registry):
        finance_interface.build_router()

        desc = isolated_registry.get("finance")
        assert desc.name == "finance"
        assert desc.version == "1.0.0"

    def test_build_router_called_twice_raises_value_error(self, isolated_registry):
        finance_interface.build_router()

        with pytest.raises(ValueError, match="already registered"):
            finance_interface.build_router()


class TestFinanceInterfaceEndpoints:
    def test_create_invoice_endpoint_success(self, finance_app):
        fake_invoice = MagicMock(id=10, invoice_number="INV-1")
        payload = {
            "invoice_number": "INV-1",
            "issue_date": "2026-01-01",
            "due_date": "2026-01-31",
            "items": [{"description": "Widget", "quantity": 2, "unit_price": 10.0}],
        }

        with patch.object(finance_interface.application, "create_invoice", return_value=fake_invoice) as mock_create:
            client = TestClient(finance_app)
            response = client.post("/api/v1/finance/invoices", json=payload)

        assert response.status_code == 200
        assert response.json() == {"id": 10, "invoice_number": "INV-1"}
        mock_create.assert_called_once()

    def test_create_invoice_endpoint_value_error_returns_400(self, finance_app):
        payload = {
            "invoice_number": "INV-1",
            "issue_date": "2026-01-01",
            "due_date": "2026-01-31",
            "items": [{"description": "Widget", "quantity": 1, "unit_price": 5.0}],
        }

        with patch.object(finance_interface.application, "create_invoice", side_effect=ValueError("dup")):
            client = TestClient(finance_app)
            response = client.post("/api/v1/finance/invoices", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "dup"

    def test_record_payment_endpoint_success(self, finance_app):
        fake_payment = MagicMock(id=5, amount=50.0)
        payload = {
            "invoice_id": 1, "amount": 50.0, "payment_method": "cash", "payment_date": "2026-01-01",
        }

        with patch.object(finance_interface.application, "record_payment", return_value=fake_payment):
            client = TestClient(finance_app)
            response = client.post("/api/v1/finance/payments", json=payload)

        assert response.status_code == 200
        assert response.json() == {"id": 5, "amount": 50.0}

    def test_record_payment_endpoint_value_error_returns_400(self, finance_app):
        payload = {
            "invoice_id": 1, "amount": 999.0, "payment_method": "cash", "payment_date": "2026-01-01",
        }

        with patch.object(finance_interface.application, "record_payment", side_effect=ValueError("too much")):
            client = TestClient(finance_app)
            response = client.post("/api/v1/finance/payments", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "too much"

    def test_get_invoice_endpoint_not_found_returns_404(self, finance_app):
        with patch.object(finance_interface.application, "get_invoice", return_value=None):
            client = TestClient(finance_app)
            response = client.get("/api/v1/finance/invoices/999")

        assert response.status_code == 404

    def test_get_invoice_endpoint_found_returns_invoice(self, finance_app):
        with patch.object(finance_interface.application, "get_invoice", return_value={"id": 5, "invoice_number": "INV-5"}):
            client = TestClient(finance_app)
            response = client.get("/api/v1/finance/invoices/5")

        assert response.status_code == 200
        assert response.json() == {"id": 5, "invoice_number": "INV-5"}

    def test_list_invoices_endpoint_passes_filters(self, finance_app):
        with patch.object(finance_interface.application, "list_invoices", return_value=[]) as mock_list:
            client = TestClient(finance_app)
            response = client.get("/api/v1/finance/invoices?status=paid&contact_id=3")

        assert response.status_code == 200
        assert response.json() == []
        _, kwargs = mock_list.call_args
        assert kwargs["status"] == "paid"
        assert kwargs["contact_id"] == 3

    def test_dashboard_endpoint_returns_metrics(self, finance_app):
        with patch.object(finance_interface.application, "dashboard", return_value={"total_invoices": 4}):
            client = TestClient(finance_app)
            response = client.get("/api/v1/finance/dashboard")

        assert response.status_code == 200
        assert response.json() == {"total_invoices": 4}