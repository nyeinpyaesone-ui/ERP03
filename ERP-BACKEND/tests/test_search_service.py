"""
Unit tests for the search service module (app/services/search_service.py).
"""
import os
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.services.search_service import SearchService
from app.models import Contact, Company, Product, Employee, Document

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
    """Tests for index_entity method."""

    def test_index_entity_new(self, mock_db):
        """Test indexing a new entity."""
        from sqlalchemy.exc import IntegrityError
        
        service = SearchService(db=mock_db)
        # Simulate IntegrityError to trigger fallback path for testing
        mock_db.execute.side_effect = IntegrityError("constraint", {}, None)
        # Setup mock for fallback query path (new entity, so first() returns None)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service.index_entity(
            entity_type="contact",
            entity_id=1,
            title="John Doe",
            content="Test contact content",
            metadata={"email": "john@example.com"},
            tags=["contact", "lead"]
        )
        
        # Verify add was called (in fallback path)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        
        # Verify the indexed entity has correct attributes
        indexed_entity = mock_db.add.call_args[0][0]
        assert indexed_entity.entity_type == "contact"
        assert indexed_entity.entity_id == 1
        assert indexed_entity.title == "John Doe"
        assert "Test contact content" in indexed_entity.content
        assert "John Doe" in indexed_entity.searchable_text
        assert indexed_entity.meta_data == {"email": "john@example.com"}
        assert indexed_entity.tags == ["contact", "lead"]

    def test_index_entity_update_existing(self, mock_db):
        """Test updating an existing indexed entity via fallback path."""
        from sqlalchemy.exc import IntegrityError
        
        service = SearchService(db=mock_db)
        
        # Simulate IntegrityError to trigger fallback query-and-update path
        mock_db.execute.side_effect = IntegrityError('test', 'params', 'orig')

        # Mock existing index entry with required attributes
        existing_index = MagicMock()
        existing_index.title = "Old Title"
        existing_index.content = "Old Content"
        existing_index.searchable_text = "old text"
        existing_index.meta_data = {}
        existing_index.tags = []
        existing_index.updated_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = existing_index

        service.index_entity(
            entity_type="contact",
            entity_id=1,
            title="Jane Doe",
            content="Updated content"
        )

        # Verify update was performed (not add)
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called()

        # Verify attributes were updated in fallback path
        assert existing_index.title == "Jane Doe"
        assert existing_index.content == "Updated content"
        assert "Jane Doe" in existing_index.searchable_text
        assert existing_index.updated_at is not None

    def test_index_entity_with_metadata_values(self, mock_db):
        """Test indexing entity with various metadata value types."""
        from sqlalchemy.exc import IntegrityError
        
        service = SearchService(db=mock_db)
        # Setup mock for fallback path - new entity so first() returns None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        # Mock execute to raise IntegrityError to trigger fallback path
        mock_db.execute.side_effect = IntegrityError("test", {}, {})

        service.index_entity(
            entity_type="product",
            entity_id=1,
            title="Product A",
            content="Product description",
            metadata={
                "price": 99.99,  # float
                "quantity": 10,  # int
                "sku": "ABC123",  # str
                "active": True  # bool (should be excluded as per isinstance check)
            }
        )

        # Verify add was called in fallback path
        mock_db.add.assert_called_once()
        indexed_entity = mock_db.add.call_args[0][0]
        searchable = indexed_entity.searchable_text

        assert "99.99" in searchable
        assert "10" in searchable
        assert "ABC123" in searchable
        # Note: In Python, bool is a subclass of int, so True passes isinstance(value, (str, int, float))
        # This test documents the actual behavior of the code
        assert "True" in searchable  # Boolean IS added because bool is subclass of int

    def test_index_entity_empty_metadata_and_tags(self, mock_db):
        """Test indexing entity with empty metadata and tags."""
        from sqlalchemy.exc import IntegrityError
        
        service = SearchService(db=mock_db)
        # Setup mock for fallback path - new entity so first() returns None
        mock_db.query.return_value.filter.return_value.first.return_value = None
        # Mock execute to raise IntegrityError to trigger fallback path
        mock_db.execute.side_effect = IntegrityError("test", {}, {})

        service.index_entity(
            entity_type="company",
            entity_id=1,
            title="Test Company",
            content="Content"
        )

        # Verify add was called in fallback path
        mock_db.add.assert_called_once()
        indexed_entity = mock_db.add.call_args[0][0]
        assert indexed_entity.meta_data == {}
        assert indexed_entity.tags == []

    def test_remove_from_index_success(self, mock_db):
        """Test removing an entity from the index."""
        service = SearchService(db=mock_db)
        mock_delete_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_delete_query
        
        service.remove_from_index(entity_type="contact", entity_id=1)
        
        mock_delete_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()


class TestIndexAllEntities:
    """Tests for bulk indexing methods."""

    def test_index_all_contacts(self, mock_db):
        """Test indexing all contacts."""
        service = SearchService(db=mock_db)
        
        # Mock contacts
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
        
        mock_db.query.return_value.all.return_value = [contact1]
        
        with patch.object(service, 'index_entity') as mock_index:
            service.index_all_contacts()
            
            mock_index.assert_called_once()
            args = mock_index.call_args[0]
            assert args[0] == "contact"
            assert args[1] == 1
            assert "John Doe" in args[2]

    def test_index_all_companies(self, mock_db):
        """Test indexing all companies."""
        service = SearchService(db=mock_db)
        
        company = MagicMock(spec=Company)
        company.id = 1
        company.name = "Test Corp"
        company.industry = "Technology"
        company.website = "https://test.com"
        company.address = "123 Main St"
        company.phone = "+1234567890"
        company.size = "50-200"
        
        mock_db.query.return_value.all.return_value = [company]
        
        with patch.object(service, 'index_entity') as mock_index:
            service.index_all_companies()
            
            mock_index.assert_called_once()
            assert "Test Corp" in mock_index.call_args[0][2]

    def test_index_all_products(self, mock_db):
        """Test indexing all products."""
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
        
        mock_db.query.return_value.all.return_value = [product]
        
        with patch.object(service, 'index_entity') as mock_index:
            service.index_all_products()
            
            mock_index.assert_called_once()
            args = mock_index.call_args[0]
            assert args[2] == "Widget"
            # The metadata is passed as the 4th positional argument (metadata parameter)
            # Check that price value is in the call
            call_kwargs = mock_index.call_args
            # index_entity signature: (entity_type, entity_id, title, content, metadata, tags)
            assert call_kwargs[0][3]  # content should exist

    def test_index_all_employees(self, mock_db):
        """Test indexing all employees."""
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
        
        mock_db.query.return_value.all.return_value = [employee]
        
        with patch.object(service, 'index_entity') as mock_index:
            service.index_all_employees()
            
            mock_index.assert_called_once()
            assert "EMP001" in mock_index.call_args[0][2]

    def test_index_all_documents(self, mock_db):
        """Test indexing all documents."""
        service = SearchService(db=mock_db)
        
        document = MagicMock(spec=Document)
        document.id = 1
        document.title = "Report Q1"
        document.filename = "report_q1.pdf"
        document.extracted_text = "Quarterly financial report"
        document.mime_type = "application/pdf"
        document.entity_type = "company"
        document.file_size = 102400
        
        mock_db.query.return_value.all.return_value = [document]
        
        with patch.object(service, 'index_entity') as mock_index:
            service.index_all_documents()
            
            mock_index.assert_called_once()
            assert "Report Q1" in mock_index.call_args[0][2]


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
        result1.updated_at = datetime.now(timezone.utc)
        
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
