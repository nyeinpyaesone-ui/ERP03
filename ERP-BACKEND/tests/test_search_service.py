"""
Unit tests for the search service module (app/services/search_service.py).
"""
import os
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.search_service import SearchService
from app.models import Contact, Company, Product, Employee, Document, SearchIndex as SearchIndexModel

# Mock the missing models for testing
class MockSearchIndex:
    pass

class MockSearchQuery:
    pass

class MockSearchSuggestion:
    pass


class TestSearchServiceInit:
    """Tests for SearchService initialization."""

    def test_init_default_settings(self, mock_db):
        """Test SearchService initialization with default settings."""
        service = SearchService(db=mock_db)
        
        assert service.db == mock_db
        assert service.use_elasticsearch is False
        assert service.es_url == "http://localhost:9200"

    def test_init_with_elasticsearch_enabled(self, mock_db):
        """Test SearchService initialization with Elasticsearch enabled."""
        service = SearchService(db=mock_db, use_elasticsearch=True)
        
        assert service.use_elasticsearch is True

    @patch.dict(os.environ, {"ELASTICSEARCH_URL": "http://es-server:9200"})
    def test_init_custom_elasticsearch_url(self, mock_db):
        """Test SearchService initialization with custom Elasticsearch URL."""
        import os
        service = SearchService(db=mock_db, use_elasticsearch=True)
        
        assert service.es_url == "http://es-server:9200"


class TestIndexEntity:
    """Tests for index_entity method.

    As of this revision, ``index_entity`` no longer falls back to a
    query-and-update approach on ``IntegrityError``: it now rolls back and
    re-raises the exception, relying entirely on the PostgreSQL
    ``ON CONFLICT`` upsert statement for both insert and update semantics.
    """

    @patch("app.services.search_service.postgresql_insert")
    def test_index_entity_builds_upsert_statement_and_executes(self, mock_pg_insert, mock_db):
        """Test that a well-formed upsert statement is built and executed."""
        mock_values_stmt = MagicMock()
        mock_final_stmt = MagicMock()
        mock_pg_insert.return_value.values.return_value = mock_values_stmt
        mock_values_stmt.on_conflict_do_update.return_value = mock_final_stmt

        service = SearchService(db=mock_db)
        service.index_entity(
            entity_type="contact",
            entity_id=1,
            title="John Doe",
            content="Test contact content",
            metadata={"email": "john@example.com"},
            tags=["contact", "lead"]
        )

        mock_pg_insert.assert_called_once_with(SearchIndexModel)

        values_kwargs = mock_pg_insert.return_value.values.call_args.kwargs
        assert values_kwargs["entity_type"] == "contact"
        assert values_kwargs["entity_id"] == 1
        assert values_kwargs["title"] == "John Doe"
        assert values_kwargs["content"] == "Test contact content"
        assert "John Doe" in values_kwargs["searchable_text"]
        assert "Test contact content" in values_kwargs["searchable_text"]
        assert "john@example.com" in values_kwargs["searchable_text"]
        assert values_kwargs["meta_data"] == {"email": "john@example.com"}
        assert values_kwargs["tags"] == ["contact", "lead"]

        on_conflict_kwargs = mock_values_stmt.on_conflict_do_update.call_args.kwargs
        assert on_conflict_kwargs["index_elements"] == ["entity_type", "entity_id"]
        assert on_conflict_kwargs["set_"]["title"] == "John Doe"
        assert on_conflict_kwargs["set_"]["content"] == "Test contact content"

        mock_db.execute.assert_called_once_with(mock_final_stmt)
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_index_entity_integrity_error_rolls_back_and_reraises(self, mock_db):
        """IntegrityError from the upsert must roll back and propagate, with
        no fallback query-and-update behavior (regression for removed
        fallback logic)."""
        from sqlalchemy.exc import IntegrityError

        service = SearchService(db=mock_db)
        mock_db.execute.side_effect = IntegrityError("stmt", {}, BaseException("orig"))

        with pytest.raises(IntegrityError):
            service.index_entity(
                entity_type="contact",
                entity_id=1,
                title="John Doe",
                content="Test contact content",
            )

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()
        # No fallback add/query should ever occur now that the fallback was removed
        mock_db.add.assert_not_called()

    @patch("app.services.search_service.postgresql_insert")
    def test_index_entity_metadata_value_types_included_in_searchable_text(self, mock_pg_insert, mock_db):
        """Test that str/int/float metadata values are appended to the
        searchable text, and that bool values are included too because
        ``bool`` is a subclass of ``int`` in Python."""
        mock_values_stmt = MagicMock()
        mock_pg_insert.return_value.values.return_value = mock_values_stmt
        mock_values_stmt.on_conflict_do_update.return_value = MagicMock()

        service = SearchService(db=mock_db)
        service.index_entity(
            entity_type="product",
            entity_id=1,
            title="Product A",
            content="Product description",
            metadata={
                "price": 99.99,  # float
                "quantity": 10,  # int
                "sku": "ABC123",  # str
                "active": True,  # bool (subclass of int, so it IS included)
            }
        )

        values_kwargs = mock_pg_insert.return_value.values.call_args.kwargs
        searchable = values_kwargs["searchable_text"]

        assert "99.99" in searchable
        assert "10" in searchable
        assert "ABC123" in searchable
        # Note: In Python, bool is a subclass of int, so True passes isinstance(value, (str, int, float))
        # This test documents the actual behavior of the code
        assert "True" in searchable

    def test_index_entity_empty_metadata_and_tags_default_to_empty_containers(self, mock_db):
        """Test indexing entity with no metadata/tags results in {} and []
        being passed to the upsert statement."""
        with patch("app.services.search_service.postgresql_insert") as mock_pg_insert:
            mock_values_stmt = MagicMock()
            mock_pg_insert.return_value.values.return_value = mock_values_stmt
            mock_values_stmt.on_conflict_do_update.return_value = MagicMock()

            service = SearchService(db=mock_db)
            service.index_entity(
                entity_type="company",
                entity_id=1,
                title="Test Company",
                content="Content"
            )

            values_kwargs = mock_pg_insert.return_value.values.call_args.kwargs
            assert values_kwargs["meta_data"] == {}
            assert values_kwargs["tags"] == []
            assert values_kwargs["searchable_text"] == "Test Company Content"

        mock_db.commit.assert_called_once()

    def test_remove_from_index_success(self, mock_db):
        """Test removing an entity from the index."""
        service = SearchService(db=mock_db)
        mock_delete_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_delete_query
        
        service.remove_from_index(entity_type="contact", entity_id=1)
        
        mock_delete_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()


class TestBulkIndex:
    """Tests for the ``_bulk_index`` method introduced for batch indexing."""

    def test_bulk_index_empty_batch_returns_immediately(self, mock_db):
        """Test that an empty batch is a no-op and never touches the DB."""
        service = SearchService(db=mock_db)

        service._bulk_index([])

        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()

    def test_bulk_index_with_data_raises_unbound_local_error(self, mock_db):
        """Regression test documenting a real bug in ``_bulk_index``:
        the ``on_conflict_do_update`` ``set_`` dict references
        ``stmt.excluded.*`` while ``stmt`` is still being assigned on the
        left-hand side of the same statement. This makes ``stmt`` an
        as-yet-unbound local variable at the point it is referenced,
        causing an ``UnboundLocalError`` for any non-empty batch. Because
        this error is not an ``IntegrityError``, it is NOT caught by the
        surrounding ``except IntegrityError`` clause and propagates out of
        ``_bulk_index`` untouched, meaning the "fallback to individual
        indexing" behavior is unreachable in practice.
        """
        service = SearchService(db=mock_db)
        batch_data = [{
            "entity_type": "contact",
            "entity_id": 1,
            "title": "John Doe",
            "content": "Some content",
        }]

        with pytest.raises(UnboundLocalError):
            service._bulk_index(batch_data)

        # The crash happens while building `stmt`, before execute/commit run
        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_bulk_index_with_multiple_items_still_raises(self, mock_db):
        """The bug reproduces regardless of batch size."""
        service = SearchService(db=mock_db)
        batch_data = [
            {"entity_type": "contact", "entity_id": 1, "title": "A", "content": "a"},
            {"entity_type": "contact", "entity_id": 2, "title": "B", "content": "b"},
        ]

        with pytest.raises(UnboundLocalError):
            service._bulk_index(batch_data)


class TestIndexAllEntities:
    """Tests for bulk indexing methods.

    These methods now paginate through the table in ``batch_size`` chunks
    (via ``.limit().offset()``) and delegate to ``_bulk_index`` (rather than
    calling ``index_entity`` per row directly), stopping once a page comes
    back empty. ``_bulk_index`` itself is patched out in these tests so we
    can verify the batching/mapping logic in isolation without hitting the
    ``UnboundLocalError`` bug covered in ``TestBulkIndex``.
    """

    def _paginated_query(self, mock_db, pages):
        """Configure mock_db.query(...).limit(...).offset(...).all() to
        return successive pages, ending the loop once an empty page is
        returned."""
        mock_db.query.return_value.limit.return_value.offset.return_value.all.side_effect = pages

    def test_index_all_contacts_maps_fields_and_calls_bulk_index(self, mock_db):
        """Test indexing all contacts builds correct batch_data dicts."""
        service = SearchService(db=mock_db)

        contact1 = MagicMock(spec=Contact)
        contact1.id = 1
        contact1.first_name = "John"
        contact1.last_name = "Doe"
        contact1.email = "john@example.com"
        contact1.phone = "+1234567890"
        contact1.title = "Manager"
        contact1.notes = "Important contact"
        contact1.status = "active"
        contact1.company_id = 1
        contact1.assigned_to = 2

        self._paginated_query(mock_db, [[contact1], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_contacts()

            mock_bulk_index.assert_called_once()
            batch_data = mock_bulk_index.call_args[0][0]
            assert len(batch_data) == 1
            item = batch_data[0]
            assert item["entity_type"] == "contact"
            assert item["entity_id"] == 1
            assert item["title"] == "John Doe"
            assert "john@example.com" in item["content"]
            assert item["meta_data"]["email"] == "john@example.com"
            assert item["meta_data"]["company_id"] == 1
            assert item["tags"] == ["active", "contact"]
            assert "John Doe" in item["searchable_text"]

    def test_index_all_contacts_stops_when_first_page_is_empty(self, mock_db):
        """Test that no bulk indexing happens when there is no data."""
        service = SearchService(db=mock_db)
        self._paginated_query(mock_db, [[]])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_contacts()
            mock_bulk_index.assert_not_called()

    def test_index_all_contacts_paginates_across_multiple_batches(self, mock_db):
        """Test that pagination advances the offset by batch_size on each
        iteration and stops once an empty page is returned."""
        service = SearchService(db=mock_db)

        contact_a = MagicMock(spec=Contact, id=1, first_name="A", last_name="A",
                               email=None, phone=None, title=None, notes=None,
                               status="active", company_id=None, assigned_to=None)
        contact_b = MagicMock(spec=Contact, id=2, first_name="B", last_name="B",
                               email=None, phone=None, title=None, notes=None,
                               status="active", company_id=None, assigned_to=None)
        self._paginated_query(mock_db, [[contact_a], [contact_b], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_contacts(batch_size=1)

            assert mock_bulk_index.call_count == 2
            offset_calls = mock_db.query.return_value.limit.return_value.offset.call_args_list
            assert offset_calls == [call(0), call(1), call(2)]

    def test_index_all_contacts_passes_batch_size_to_query_limit(self, mock_db):
        """Test that a custom batch_size is forwarded to .limit()."""
        service = SearchService(db=mock_db)
        self._paginated_query(mock_db, [[]])

        service.index_all_contacts(batch_size=250)

        mock_db.query.return_value.limit.assert_called_with(250)

    def test_index_all_companies_maps_fields_and_calls_bulk_index(self, mock_db):
        """Test indexing all companies builds correct batch_data dicts."""
        service = SearchService(db=mock_db)

        company = MagicMock(spec=Company)
        company.id = 1
        company.name = "Test Corp"
        company.industry = "Technology"
        company.website = "https://test.com"
        company.address = "123 Main St"
        company.phone = "+1234567890"
        company.size = "50-200"

        self._paginated_query(mock_db, [[company], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_companies()

            mock_bulk_index.assert_called_once()
            item = mock_bulk_index.call_args[0][0][0]
            assert item["entity_type"] == "company"
            assert item["entity_id"] == 1
            assert item["title"] == "Test Corp"
            assert "Technology" in item["content"]
            assert item["tags"] == ["Technology", "company"]
            assert "Test Corp" in item["searchable_text"]

    def test_index_all_companies_without_industry_uses_default_tag(self, mock_db):
        """Test that companies with no industry only get the 'company' tag."""
        service = SearchService(db=mock_db)

        company = MagicMock(spec=Company)
        company.id = 2
        company.name = "No Industry Co"
        company.industry = None
        company.website = None
        company.address = None
        company.phone = None
        company.size = None

        self._paginated_query(mock_db, [[company], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_companies()

            item = mock_bulk_index.call_args[0][0][0]
            assert item["tags"] == ["company"]

    def test_index_all_products_maps_fields_and_calls_bulk_index(self, mock_db):
        """Test indexing all products builds correct batch_data dicts."""
        service = SearchService(db=mock_db)

        product = MagicMock(spec=Product)
        product.id = 1
        product.name = "Widget"
        product.sku = "WGT-001"
        product.description = "A useful widget"
        product.category = "Electronics"
        product.supplier = "Supplier Co"
        product.unit_price = 29.99
        product.quantity_in_stock = 100
        product.status = "active"

        self._paginated_query(mock_db, [[product], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_products()

            item = mock_bulk_index.call_args[0][0][0]
            assert item["entity_type"] == "product"
            assert item["entity_id"] == 1
            assert item["title"] == "Widget"
            assert item["meta_data"]["price"] == 29.99
            assert item["meta_data"]["stock"] == 100
            assert item["tags"] == ["Electronics", "active", "product"]
            assert "WGT-001" in item["searchable_text"]

    def test_index_all_products_without_unit_price_defaults_price_to_zero(self, mock_db):
        """Test that a falsy unit_price maps to a price of 0 in metadata."""
        service = SearchService(db=mock_db)

        product = MagicMock(spec=Product)
        product.id = 2
        product.name = "Freebie"
        product.sku = "FREE-001"
        product.description = None
        product.category = None
        product.supplier = None
        product.unit_price = None
        product.quantity_in_stock = 0
        product.status = "inactive"

        self._paginated_query(mock_db, [[product], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_products()

            item = mock_bulk_index.call_args[0][0][0]
            assert item["meta_data"]["price"] == 0
            assert item["tags"] == ["inactive", "product"]

    def test_index_all_employees_maps_fields_and_calls_bulk_index(self, mock_db):
        """Test indexing all employees builds correct batch_data dicts."""
        service = SearchService(db=mock_db)

        employee = MagicMock(spec=Employee)
        employee.id = 1
        employee.employee_code = "EMP001"
        employee.job_title = "Developer"
        employee.address = "456 Oak Ave"
        employee.emergency_contact = "Jane Doe - +1234567890"
        employee.department_id = 1
        employee.status = "active"
        employee.employment_type = "full-time"

        self._paginated_query(mock_db, [[employee], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_employees()

            item = mock_bulk_index.call_args[0][0][0]
            assert item["entity_type"] == "employee"
            assert item["entity_id"] == 1
            assert item["title"] == "EMP001"
            assert item["tags"] == ["active", "full-time", "employee"]
            assert "EMP001" in item["searchable_text"]

    def test_index_all_documents_maps_fields_and_calls_bulk_index(self, mock_db):
        """Test indexing all documents builds correct batch_data dicts."""
        service = SearchService(db=mock_db)

        document = MagicMock(spec=Document)
        document.id = 1
        document.title = "Report Q1"
        document.filename = "report_q1.pdf"
        document.extracted_text = "Quarterly financial report"
        document.mime_type = "application/pdf"
        document.entity_type = "company"
        document.file_size = 102400

        self._paginated_query(mock_db, [[document], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_documents()

            item = mock_bulk_index.call_args[0][0][0]
            assert item["entity_type"] == "document"
            assert item["entity_id"] == 1
            assert item["title"] == "Report Q1"
            assert item["tags"] == ["application/pdf", "company", "document"]
            assert "report_q1.pdf" in item["searchable_text"]

    def test_index_all_documents_without_mime_type_uses_default_tag(self, mock_db):
        """Test that documents without a mime type only get the 'document' tag."""
        service = SearchService(db=mock_db)

        document = MagicMock(spec=Document)
        document.id = 2
        document.title = "Unknown"
        document.filename = "unknown.bin"
        document.extracted_text = None
        document.mime_type = None
        document.entity_type = "contact"
        document.file_size = 10

        self._paginated_query(mock_db, [[document], []])

        with patch.object(service, "_bulk_index") as mock_bulk_index:
            service.index_all_documents()

            item = mock_bulk_index.call_args[0][0][0]
            assert item["tags"] == ["document"]


class TestReindexAll:
    """Tests for reindex_all method."""

    def test_reindex_all(self, mock_db):
        """Test reindexing all entities."""
        service = SearchService(db=mock_db)
        
        # Mock clearing the index
        mock_db.query.return_value.delete.return_value = None
        
        # Mock individual indexing methods
        with patch.object(service, 'index_all_contacts') as mock_contacts, \
             patch.object(service, 'index_all_companies') as mock_companies, \
             patch.object(service, 'index_all_products') as mock_products, \
             patch.object(service, 'index_all_employees') as mock_employees, \
             patch.object(service, 'index_all_documents') as mock_documents:
            
            # Mock count queries
            mock_db.query.return_value.filter.return_value.count.side_effect = [5, 3, 10, 20, 15]
            
            result = service.reindex_all()
            
            # Verify index was cleared
            mock_db.query.return_value.delete.assert_called_once()
            mock_db.commit.assert_called()
            
            # Verify all indexing methods were called
            mock_contacts.assert_called_once()
            mock_companies.assert_called_once()
            mock_products.assert_called_once()
            mock_employees.assert_called_once()
            mock_documents.assert_called_once()
            
            # Verify result structure
            assert "contacts" in result
            assert "companies" in result
            assert "products" in result
            assert "employees" in result
            assert "documents" in result


class TestSearch:
    """Tests for search method."""

    def test_search_basic(self, mock_db):
        """Test basic search functionality."""
        service = SearchService(db=mock_db)
        
        # Mock search results
        result1 = MagicMock(spec=MockSearchIndex)
        result1.id = 1
        result1.entity_type = "contact"
        result1.entity_id = 1
        result1.title = "John Doe"
        result1.content = "Contact information" * 10  # Long content for preview truncation
        result1.meta_data = {"email": "john@example.com"}
        result1.tags = ["contact"]
        result1.updated_at = datetime(2024, 1, 15, 10, 30, 0)
        
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [result1]
        
        results, total, execution_time = service.search(query="john")
        
        assert len(results) == 1
        assert total == 1
        assert results[0]["entity_type"] == "contact"
        assert results[0]["title"] == "John Doe"
        assert len(results[0]["content_preview"]) <= 200
        assert isinstance(execution_time, int)

    def test_search_empty_query(self, mock_db):
        """Test search with empty query."""
        service = SearchService(db=mock_db)
        
        # When query is empty and no filters, the search method doesn't apply text filter
        # So we need to mock the base query without filter chain
        mock_base_query = MagicMock()
        mock_base_query.count.return_value = 0
        mock_base_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Mock db.query(SearchIndex) to return the base query directly
        mock_db.query.return_value = mock_base_query
        
        results, total, execution_time = service.search(query="")
        
        assert results == []
        assert total == 0

    def test_search_with_entity_types_filter(self, mock_db):
        """Test search filtered by entity types."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        service.search(query="test", entity_types=["contact", "company"])
        
        # Verify entity type filter was applied
        mock_db.query.return_value.filter.return_value.filter.assert_called()

    def test_search_with_metadata_filters(self, mock_db):
        """Test search with metadata filters."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        service.search(query="test", filters={"metadata.status": "active"})
        
        # Verify metadata filter was applied - check the second filter call
        filter_calls = mock_db.query.return_value.filter.return_value.filter.call_args_list
        assert len(filter_calls) >= 1
        # The filter should contain meta_data status check

    def test_search_with_tags_filter(self, mock_db):
        """Test search with tags filter."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        service.search(query="test", filters={"tags": ["contact", "lead"]})
        
        # Verify tags filter was applied - check for && operator call
        filter_calls = mock_db.query.return_value.filter.return_value.filter.call_args_list
        assert len(filter_calls) >= 1

    def test_search_pagination(self, mock_db):
        """Test search with pagination."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.count.return_value = 50
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        service.search(query="test", limit=10, offset=20)
        
        # Verify pagination parameters were used
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.assert_called_with(20)
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(10)

    def test_search_content_preview_truncation(self, mock_db):
        """Test that content preview is properly truncated."""
        service = SearchService(db=mock_db)
        
        long_content = "A" * 500
        result1 = MagicMock(spec=MockSearchIndex)
        result1.id = 1
        result1.entity_type = "document"
        result1.entity_id = 1
        result1.title = "Long Document"
        result1.content = long_content
        result1.meta_data = {}
        result1.tags = []
        result1.updated_at = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [result1]
        
        results, _, _ = service.search(query="test")
        
        assert len(results[0]["content_preview"]) == 200
        assert results[0]["content_preview"] == "A" * 200

    def test_search_null_content_handling(self, mock_db):
        """Test search handles null content gracefully."""
        service = SearchService(db=mock_db)
        
        result1 = MagicMock(spec=MockSearchIndex)
        result1.id = 1
        result1.entity_type = "contact"
        result1.entity_id = 1
        result1.title = "No Content"
        result1.content = None
        result1.meta_data = None
        result1.tags = None
        result1.updated_at = None
        
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [result1]
        
        results, _, _ = service.search(query="test")
        
        assert results[0]["content_preview"] == ""
        assert results[0]["metadata"] == {}
        assert results[0]["tags"] == []
        assert results[0]["updated_at"] is None


class TestGetFacets:
    """Tests for get_facets method."""

    def test_get_facets_basic(self, mock_db):
        """Test getting basic facets."""
        service = SearchService(db=mock_db)
        
        # Mock type counts
        type_result1 = MagicMock()
        type_result1.entity_type = "contact"
        type_result1.count = 10
        
        type_result2 = MagicMock()
        type_result2.entity_type = "company"
        type_result2.count = 5
        
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [type_result1, type_result2]
        
        # Mock tag results
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (["contact", "lead"],),
            (["company", "technology"],),
            (["contact"],)
        ]
        
        facets = service.get_facets(query="test")
        
        assert "entity_types" in facets
        assert "tags" in facets
        assert len(facets["entity_types"]) == 2
        assert any(t["value"] == "contact" and t["count"] == 10 for t in facets["entity_types"])

    def test_get_facets_empty_results(self, mock_db):
        """Test facets with no results."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        facets = service.get_facets()
        
        assert facets["entity_types"] == []
        assert facets["tags"] == []

    def test_get_facets_tag_limit(self, mock_db):
        """Test that facets returns only top 20 tags."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        
        # Create 30 unique tags
        tag_data = [([f"tag{i}"],) for i in range(30)]
        mock_db.query.return_value.filter.return_value.all.return_value = tag_data
        
        facets = service.get_facets()
        
        assert len(facets["tags"]) <= 20


class TestGetSuggestions:
    """Tests for get_suggestions method."""

    def test_get_suggestions_basic(self, mock_db):
        """Test getting suggestions."""
        service = SearchService(db=mock_db)
        
        # Mock suggestion results
        sugg1 = MagicMock(spec=MockSearchSuggestion)
        sugg1.query_text = "john doe"
        sugg1.suggestion_type = "contact"
        sugg1.entity_type = "contact"
        sugg1.frequency = 5
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sugg1]
        mock_db.query.return_value.filter.return_value.distinct.return_value.limit.return_value.all.return_value = []
        
        suggestions = service.get_suggestions(query="john")
        
        assert len(suggestions) == 1
        assert suggestions[0]["text"] == "john doe"
        assert suggestions[0]["frequency"] == 5

    def test_get_suggestions_short_query(self, mock_db):
        """Test suggestions with query too short."""
        service = SearchService(db=mock_db)
        
        suggestions = service.get_suggestions(query="a")
        
        assert suggestions == []
        mock_db.query.assert_not_called()

    def test_get_suggestions_empty_query(self, mock_db):
        """Test suggestions with empty query."""
        service = SearchService(db=mock_db)
        
        suggestions = service.get_suggestions(query="")
        
        assert suggestions == []

    def test_get_suggestions_no_duplicates(self, mock_db):
        """Test that suggestions don't contain duplicates."""
        service = SearchService(db=mock_db)
        
        sugg1 = MagicMock(spec=MockSearchSuggestion)
        sugg1.query_text = "duplicate"
        sugg1.suggestion_type = "contact"
        sugg1.entity_type = "contact"
        sugg1.frequency = 5
        
        title_match = MagicMock(spec=MockSearchIndex)
        title_match.title = "duplicate"
        title_match.entity_type = "contact"
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [sugg1]
        mock_db.query.return_value.filter.return_value.distinct.return_value.limit.return_value.all.return_value = [title_match]
        
        suggestions = service.get_suggestions(query="dup")
        
        # Should only appear once
        texts = [s["text"] for s in suggestions]
        assert texts.count("duplicate") == 1

    def test_get_suggestions_limit(self, mock_db):
        """Test suggestions respect limit parameter."""
        service = SearchService(db=mock_db)
        
        suggestions_list = []
        for i in range(15):
            sugg = MagicMock(spec=MockSearchSuggestion)
            sugg.query_text = f"suggestion{i}"
            sugg.suggestion_type = "contact"
            sugg.entity_type = "contact"
            sugg.frequency = i
            suggestions_list.append(sugg)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = suggestions_list
        mock_db.query.return_value.filter.return_value.distinct.return_value.limit.return_value.all.return_value = []
        
        suggestions = service.get_suggestions(query="test", limit=10)
        
        assert len(suggestions) <= 10


class TestRecordSuggestion:
    """Tests for record_suggestion method."""

    def test_record_suggestion_new(self, mock_db):
        """Test recording a new suggestion."""
        service = SearchService(db=mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service.record_suggestion(query="new search", entity_type="contact", entity_id=1)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        recorded = mock_db.add.call_args[0][0]
        assert recorded.query_text == "new search"
        assert recorded.frequency == 1

    def test_record_suggestion_existing(self, mock_db):
        """Test recording an existing suggestion increments frequency."""
        service = SearchService(db=mock_db)
        
        existing_suggestion = MagicMock(spec=MockSearchSuggestion)
        existing_suggestion.frequency = 5
        mock_db.query.return_value.filter.return_value.first.return_value = existing_suggestion
        
        service.record_suggestion(query="existing search", entity_type="contact")
        
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
        assert existing_suggestion.frequency == 6
        assert existing_suggestion.last_used is not None

    def test_record_suggestion_normalized_query(self, mock_db):
        """Test that query is normalized (lowercase and stripped)."""
        service = SearchService(db=mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service.record_suggestion(query="  SEARCH TERM  ", entity_type="contact")
        
        recorded = mock_db.add.call_args[0][0]
        assert recorded.query_text == "search term"


class TestLogQuery:
    """Tests for log_query method."""

    def test_log_query_basic(self, mock_db):
        """Test logging a search query."""
        service = SearchService(db=mock_db)
        
        service.log_query(
            user_id=1,
            query="test search",
            filters={"status": "active"},
            results_count=10,
            execution_time_ms=150,
            clicked_results=[1, 3]
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        logged_query = mock_db.add.call_args[0][0]
        # Verify it's a SearchQuery object (imported from models, not MockSearchQuery)
        from app.models import SearchQuery as RealSearchQuery
        assert isinstance(logged_query, RealSearchQuery)
        assert logged_query.user_id == 1
        assert logged_query.query == "test search"
        assert logged_query.results_count == 10
        assert logged_query.execution_time_ms == 150
        assert logged_query.clicked_results == [1, 3]

    def test_log_query_defaults(self, mock_db):
        """Test logging query with default values."""
        service = SearchService(db=mock_db)
        
        service.log_query(user_id=1, query="simple search")
        
        logged_query = mock_db.add.call_args[0][0]
        assert logged_query.filters == {}
        assert logged_query.results_count == 0
        assert logged_query.execution_time_ms == 0
        assert logged_query.clicked_results == []


class TestGetSearchAnalytics:
    """Tests for get_search_analytics method."""

    def test_get_search_analytics_basic(self, mock_db):
        """Test getting search analytics."""
        service = SearchService(db=mock_db)
        
        # Use side_effect for count since it's called multiple times with different queries
        count_calls = [0]
        def count_side_effect():
            count_calls[0] += 1
            if count_calls[0] == 1:
                return 100  # total_queries
            else:
                return 5    # no_results
        
        mock_db.query.return_value.filter.return_value.count.side_effect = count_side_effect
        
        # Mock top queries
        top_query = MagicMock()
        top_query.query = "popular search"
        top_query.count = 25
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [top_query]
        
        # Mock average execution time
        mock_db.query.return_value.filter.return_value.scalar.return_value = 125.5
        
        # Mock daily volume
        daily_result = MagicMock()
        daily_result.date = datetime(2024, 1, 15).date()
        daily_result.count = 10
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [daily_result]
        
        # Mock queries with filters - separate query chain
        query_with_filters = MagicMock()
        query_with_filters.filters = {"status": "active"}
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [query_with_filters]
        
        analytics = service.get_search_analytics(days=30)
        
        assert analytics["period_days"] == 30
        assert analytics["total_queries"] == 100
        assert analytics["no_results_queries"] == 5
        assert analytics["no_results_rate"] == 5.0  # 5/100 * 100
        assert analytics["avg_execution_time_ms"] == 125.5
        assert len(analytics["top_queries"]) == 1
        assert analytics["top_queries"][0]["query"] == "popular search"
        assert "popular_filters" in analytics

    def test_get_search_analytics_no_queries(self, mock_db):
        """Test analytics when there are no queries."""
        service = SearchService(db=mock_db)
        
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        analytics = service.get_search_analytics()
        
        assert analytics["total_queries"] == 0
        assert analytics["no_results_rate"] == 0
        assert analytics["avg_execution_time_ms"] == 0.0

    def test_get_search_analytics_filter_usage(self, mock_db):
        """Test analytics calculates filter usage correctly."""
        from app.models import SearchQuery as RealSearchQuery
        
        service = SearchService(db=mock_db)
        
        # Mock multiple queries with different filters for popular filters calculation
        q1 = MagicMock()
        q1.filters = {"status": "active", "type": "contact"}
        q2 = MagicMock()
        q2.filters = {"status": "active"}
        
        # The code queries SearchQuery with filters != None, then iterates over results
        # We need to mock the specific query chain for popular filters
        mock_query_with_filters = MagicMock()
        mock_query_with_filters.all.return_value = [q1, q2]
        
        # Set up the mock to return our mock query when SearchQuery is queried with the specific filter
        def query_side_effect(*args, **kwargs):
            mock_query_obj = MagicMock()
            if args:
                # Check if first arg is the SearchQuery class (by name to avoid SQLAlchemy comparison issues)
                if hasattr(args[0], '__name__') and args[0].__name__ == 'SearchQuery':
                    # For the popular filters query chain
                    mock_query_obj.filter.return_value = mock_query_with_filters
                    # Also set up other chains for this model
                    mock_query_obj.filter.return_value.count.return_value = 10
                    mock_query_obj.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
                    mock_query_obj.filter.return_value.filter.return_value.count.return_value = 2
                    mock_query_obj.filter.return_value.scalar.return_value = 150.5
                    mock_query_obj.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
            return mock_query_obj
        
        mock_db.query.side_effect = query_side_effect
        
        analytics = service.get_search_analytics()
        
        assert "popular_filters" in analytics
        # Check that filter counts are correct
        popular_filters = analytics["popular_filters"]
        status_filter = next((f for f in popular_filters if f["filter"] == "status"), None)
        type_filter = next((f for f in popular_filters if f["filter"] == "type"), None)
        assert status_filter is not None
        assert status_filter["count"] == 2
        assert type_filter is not None
        assert type_filter["count"] == 1
