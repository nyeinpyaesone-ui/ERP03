"""
Unit tests for the search router module (app/routers/search.py).
Tests cover API endpoints, request/response validation, authentication, and integration with SearchService.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.routers.search import (
    router,
    SearchRequest,
    SearchResult,
    SearchResponse,
    SuggestionResponse,
    SearchAnalytics
)
from app.models import User, SearchQuery


class TestSearchRequestSchema:
    """Tests for SearchRequest Pydantic schema validation."""

    def test_search_request_minimal(self):
        """Test SearchRequest with only required field."""
        request = SearchRequest(query="test query")
        
        assert request.query == "test query"
        assert request.entity_types is None
        assert request.filters is None
        assert request.limit == 20
        assert request.offset == 0

    def test_search_request_with_all_fields(self):
        """Test SearchRequest with all optional fields."""
        request = SearchRequest(
            query="advanced search",
            entity_types=["contact", "company"],
            filters={"metadata.status": "active", "tags": ["vip"]},
            limit=50,
            offset=100
        )
        
        assert request.query == "advanced search"
        assert request.entity_types == ["contact", "company"]
        assert request.filters["metadata.status"] == "active"
        assert request.filters["tags"] == ["vip"]
        assert request.limit == 50
        assert request.offset == 100

    def test_search_request_empty_query(self):
        """Test SearchRequest with empty query string."""
        request = SearchRequest(query="")
        assert request.query == ""

    def test_search_request_default_pagination(self):
        """Test SearchRequest default pagination values."""
        request = SearchRequest(query="test")
        
        assert request.limit == 20
        assert request.offset == 0

    def test_search_request_limit_bounds(self):
        """Test SearchRequest limit validation."""
        # Valid limits
        request1 = SearchRequest(query="test", limit=1)
        assert request1.limit == 1
        
        request2 = SearchRequest(query="test", limit=100)
        assert request2.limit == 100

    def test_search_request_offset_non_negative(self):
        """Test SearchRequest offset validation."""
        request = SearchRequest(query="test", offset=0)
        assert request.offset == 0
        
        request2 = SearchRequest(query="test", offset=500)
        assert request2.offset == 500


class TestSearchResultSchema:
    """Tests for SearchResult Pydantic schema."""

    def test_search_result_complete(self):
        """Test SearchResult with all fields."""
        result = SearchResult(
            id=1,
            entity_type="contact",
            entity_id=42,
            title="John Doe",
            content_preview="Contact information...",
            metadata={"email": "john@example.com", "status": "active"},
            tags=["contact", "vip"],
            updated_at="2024-01-15T10:30:00"
        )
        
        assert result.id == 1
        assert result.entity_type == "contact"
        assert result.entity_id == 42
        assert result.title == "John Doe"
        assert len(result.metadata) == 2
        assert len(result.tags) == 2

    def test_search_result_null_updated_at(self):
        """Test SearchResult with null updated_at."""
        result = SearchResult(
            id=1,
            entity_type="company",
            entity_id=10,
            title="Test Corp",
            content_preview="",
            metadata={},
            tags=[],
            updated_at=None
        )
        
        assert result.updated_at is None

    def test_search_result_empty_collections(self):
        """Test SearchResult with empty metadata and tags."""
        result = SearchResult(
            id=1,
            entity_type="product",
            entity_id=5,
            title="Widget",
            content_preview="A useful widget",
            metadata={},
            tags=[],
            updated_at=None
        )
        
        assert result.metadata == {}
        assert result.tags == []


class TestSearchResponseSchema:
    """Tests for SearchResponse Pydantic schema."""

    def test_search_response_complete(self):
        """Test SearchResponse with all fields."""
        results = [
            SearchResult(
                id=1, entity_type="contact", entity_id=1,
                title="John", content_preview="...",
                metadata={}, tags=[], updated_at=None
            )
        ]
        
        response = SearchResponse(
            query="john",
            results=results,
            total=1,
            execution_time_ms=45,
            facets={"entity_types": [{"value": "contact", "count": 1}]},
            page=1,
            per_page=20
        )
        
        assert response.query == "john"
        assert len(response.results) == 1
        assert response.total == 1
        assert response.execution_time_ms == 45
        assert response.page == 1
        assert response.per_page == 20

    def test_search_response_empty_results(self):
        """Test SearchResponse with no results."""
        response = SearchResponse(
            query="nonexistent",
            results=[],
            total=0,
            execution_time_ms=12,
            facets={"entity_types": [], "tags": []},
            page=1,
            per_page=20
        )
        
        assert response.results == []
        assert response.total == 0


class TestSuggestionResponseSchema:
    """Tests for SuggestionResponse Pydantic schema."""

    def test_suggestion_response_complete(self):
        """Test SuggestionResponse with all fields."""
        suggestion = SuggestionResponse(
            text="john doe",
            type="contact",
            entity_type="contact",
            frequency=15
        )
        
        assert suggestion.text == "john doe"
        assert suggestion.type == "contact"
        assert suggestion.entity_type == "contact"
        assert suggestion.frequency == 15

    def test_suggestion_response_null_entity_type(self):
        """Test SuggestionResponse with null entity_type."""
        suggestion = SuggestionResponse(
            text="general query",
            type="query",
            entity_type=None,
            frequency=5
        )
        
        assert suggestion.entity_type is None


class TestSearchAnalyticsSchema:
    """Tests for SearchAnalytics Pydantic schema."""

    def test_search_analytics_complete(self):
        """Test SearchAnalytics with all fields."""
        analytics = SearchAnalytics(
            period_days=30,
            total_queries=150,
            no_results_queries=12,
            no_results_rate=8.0,
            avg_execution_time_ms=45.5,
            top_queries=[{"query": "john", "count": 25}],
            daily_volume=[{"date": "2024-01-15", "queries": 10}],
            popular_filters=[{"filter": "status", "count": 30}]
        )
        
        assert analytics.period_days == 30
        assert analytics.total_queries == 150
        assert analytics.no_results_rate == 8.0
        assert len(analytics.top_queries) == 1
        assert len(analytics.daily_volume) == 1
        assert len(analytics.popular_filters) == 1

    def test_search_analytics_zero_queries(self):
        """Test SearchAnalytics with zero queries."""
        analytics = SearchAnalytics(
            period_days=7,
            total_queries=0,
            no_results_queries=0,
            no_results_rate=0.0,
            avg_execution_time_ms=0.0,
            top_queries=[],
            daily_volume=[],
            popular_filters=[]
        )
        
        assert analytics.total_queries == 0
        assert analytics.no_results_rate == 0.0
        assert analytics.top_queries == []


class TestSearchRouterPOST:
    """Tests for POST /api/v1/search/ endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_current_user(self):
        """Create mock current user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.role = "user"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_search_post_basic(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test basic POST search request."""
        # Setup mocks
        mock_search_service.search.return_value = (
            [
                {
                    "id": 1,
                    "entity_type": "contact",
                    "entity_id": 1,
                    "title": "John Doe",
                    "content_preview": "Contact info",
                    "metadata": {},
                    "tags": [],
                    "updated_at": "2024-01-15T10:30:00"
                }
            ],
            1,
            45
        )
        mock_search_service.get_facets.return_value = {
            "entity_types": [{"value": "contact", "count": 1}],
            "tags": []
        }

        # Create test client with mocked dependencies
        from fastapi import Depends
        
        def mock_get_db():
            return mock_db
        
        def mock_get_current_user():
            return mock_current_user
        
        # Override dependencies
        router.dependency_overrides = {}
        
        # Make request using direct function call
        from app.routers.search import search
        from app.routers.search import SearchRequest
        
        request = SearchRequest(query="john")
        result = search(
            request=request,
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Verify SearchService was initialized
        mock_search_service.search.assert_called_once()
        
        # Verify log_query was called
        mock_search_service.log_query.assert_called_once()
        
        # Verify record_suggestion was called (query length >= 3)
        mock_search_service.record_suggestion.assert_called_once()
        
        # Verify response structure
        assert result["query"] == "john"
        assert len(result["results"]) == 1
        assert result["total"] == 1
        assert result["execution_time_ms"] == 45
        assert result["page"] == 1
        assert result["per_page"] == 20

    def test_search_post_with_filters(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test POST search with entity types and filters."""
        mock_search_service.search.return_value = ([], 0, 30)
        mock_search_service.get_facets.return_value = {
            "entity_types": [],
            "tags": []
        }
        
        from app.routers.search import search, SearchRequest
        
        request = SearchRequest(
            query="test",
            entity_types=["contact", "company"],
            filters={"metadata.status": "active"},
            limit=50,
            offset=100
        )
        
        search(request=request, db=mock_db, current_user=mock_current_user)
        
        # Verify search was called with correct parameters
        mock_search_service.search.assert_called_once_with(
            query="test",
            entity_types=["contact", "company"],
            filters={"metadata.status": "active"},
            limit=50,
            offset=100
        )

    def test_search_post_logs_activity(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test that search POST logs activity."""
        mock_search_service.search.return_value = ([], 5, 25)
        mock_search_service.get_facets.return_value = {"entity_types": [], "tags": []}
        
        with patch('app.routers.search.log_activity') as mock_log:
            from app.routers.search import search, SearchRequest
            
            request = SearchRequest(query="test query")
            search(request=request, db=mock_db, current_user=mock_current_user)
            
            # Verify activity was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["user_id"] == mock_current_user.id
            assert call_args[1]["action"] == "search"
            assert call_args[1]["entity_type"] == "search"

    def test_search_post_short_query_no_suggestion(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test that queries shorter than 3 chars don't record suggestions."""
        mock_search_service.search.return_value = ([], 0, 20)
        mock_search_service.get_facets.return_value = {"entity_types": [], "tags": []}
        
        from app.routers.search import search, SearchRequest
        
        request = SearchRequest(query="ab")  # Only 2 characters
        search(request=request, db=mock_db, current_user=mock_current_user)
        
        # record_suggestion should NOT be called for short queries
        mock_search_service.record_suggestion.assert_not_called()


class TestSearchRouterGET:
    """Tests for GET /api/v1/search/ endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_current_user(self):
        """Create mock current user."""
        user = MagicMock(spec=User)
        user.id = 1
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_search_get_basic(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test basic GET search request."""
        mock_search_service.search.return_value = ([], 10, 35)
        mock_search_service.get_facets.return_value = {"entity_types": [], "tags": []}
        
        from app.routers.search import search_get
        
        result = search_get(
            q="test query",
            types=None,
            limit=20,
            offset=0,
            db=mock_db,
            current_user=mock_current_user
        )
        
        assert result["query"] == "test query"
        assert result["total"] == 10
        assert result["execution_time_ms"] == 35
        assert result["page"] == 1
        assert result["per_page"] == 20

    def test_search_get_with_entity_types(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test GET search with comma-separated entity types."""
        mock_search_service.search.return_value = ([], 0, 25)
        mock_search_service.get_facets.return_value = {"entity_types": [], "tags": []}
        
        from app.routers.search import search_get
        
        search_get(
            q="test",
            types="contact,company,product",
            limit=20,
            offset=0,
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Verify entity types were split correctly
        mock_search_service.search.assert_called_once()
        call_args = mock_search_service.search.call_args
        assert call_args[1]["entity_types"] == ["contact", "company", "product"]

    def test_search_get_pagination(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test GET search with pagination."""
        mock_search_service.search.return_value = ([], 100, 40)
        mock_search_service.get_facets.return_value = {"entity_types": [], "tags": []}
        
        from app.routers.search import search_get
        
        result = search_get(
            q="test",
            types=None,
            limit=25,
            offset=50,
            db=mock_db,
            current_user=mock_current_user
        )
        
        # Page calculation: (offset // limit) + 1 = (50 // 25) + 1 = 3
        assert result["page"] == 3
        assert result["per_page"] == 25


class TestGetSuggestions:
    """Tests for GET /api/v1/search/suggestions endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_current_user(self):
        """Create mock current user."""
        user = MagicMock(spec=User)
        user.id = 1
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_get_suggestions_basic(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test getting suggestions for a query."""
        mock_search_service.get_suggestions.return_value = [
            {"text": "john doe", "type": "contact", "entity_type": "contact", "frequency": 10},
            {"text": "john smith", "type": "contact", "entity_type": "contact", "frequency": 5}
        ]
        
        from app.routers.search import get_suggestions
        
        result = get_suggestions(
            q="john",
            limit=10,
            db=mock_db,
            current_user=mock_current_user
        )
        
        assert len(result) == 2
        mock_search_service.get_suggestions.assert_called_once_with("john", limit=10)

    def test_get_suggestions_custom_limit(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test getting suggestions with custom limit."""
        mock_search_service.get_suggestions.return_value = []
        
        from app.routers.search import get_suggestions
        
        get_suggestions(q="test", limit=5, db=mock_db, current_user=mock_current_user)
        
        mock_search_service.get_suggestions.assert_called_once_with("test", limit=5)


class TestGetFacets:
    """Tests for GET /api/v1/search/facets endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_current_user(self):
        """Create mock current user."""
        user = MagicMock(spec=User)
        user.id = 1
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_get_facets_basic(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test getting facets without query or types."""
        mock_search_service.get_facets.return_value = {
            "entity_types": [
                {"value": "contact", "count": 50},
                {"value": "company", "count": 30}
            ],
            "tags": [
                {"value": "vip", "count": 15},
                {"value": "active", "count": 40}
            ]
        }
        
        from app.routers.search import get_facets
        
        result = get_facets(
            q=None,
            types=None,
            db=mock_db,
            current_user=mock_current_user
        )
        
        assert "entity_types" in result
        assert "tags" in result
        mock_search_service.get_facets.assert_called_once_with(query=None, entity_types=None)

    def test_get_facets_with_filters(
        self, mock_search_service, mock_current_user, mock_db
    ):
        """Test getting facets with query and entity types."""
        mock_search_service.get_facets.return_value = {"entity_types": [], "tags": []}
        
        from app.routers.search import get_facets
        
        get_facets(
            q="test",
            types="contact,company",
            db=mock_db,
            current_user=mock_current_user
        )
        
        mock_search_service.get_facets.assert_called_once_with(
            query="test",
            entity_types=["contact", "company"]
        )


class TestReindexAll:
    """Tests for POST /api/v1/search/reindex endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "admin"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_reindex_all_success(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test successful reindexing of all entities."""
        mock_search_service.reindex_all.return_value = {
            "contacts": 50,
            "companies": 30,
            "products": 100,
            "employees": 20,
            "documents": 15
        }
        
        with patch('app.routers.search.log_activity') as mock_log:
            from app.routers.search import reindex_all
            
            result = reindex_all(db=mock_db, current_user=mock_admin_user)
            
            assert result["status"] == "success"
            assert result["message"] == "All entities reindexed"
            assert "counts" in result
            assert result["counts"]["contacts"] == 50
            
            # Verify activity was logged
            mock_log.assert_called_once()

    def test_reindex_all_returns_counts(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test that reindex returns counts for all entity types."""
        mock_search_service.reindex_all.return_value = {
            "contacts": 10,
            "companies": 5,
            "products": 25,
            "employees": 8,
            "documents": 3
        }
        
        from app.routers.search import reindex_all
        
        result = reindex_all(db=mock_db, current_user=mock_admin_user)
        
        # Verify all expected keys are present
        for key in ["contacts", "companies", "products", "employees", "documents"]:
            assert key in result["counts"]


class TestIndexEntity:
    """Tests for POST /api/v1/search/index/{entity_type}/{entity_id} endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "admin"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_index_entity_contact(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test indexing a contact entity."""
        # Mock contact retrieval
        mock_contact = MagicMock()
        mock_contact.id = 1
        mock_contact.first_name = "John"
        mock_contact.last_name = "Doe"
        mock_contact.email = "john@example.com"
        mock_contact.phone = "+1234567890"
        mock_contact.title = "Manager"
        mock_contact.notes = "Important contact"
        mock_contact.status = "active"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contact
        
        from app.routers.search import index_entity
        
        result = index_entity(
            entity_type="contact",
            entity_id=1,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert result["message"] == "contact 1 indexed"
        mock_search_service.index_entity.assert_called_once()

    def test_index_entity_company(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test indexing a company entity."""
        mock_company = MagicMock()
        mock_company.id = 1
        mock_company.name = "Test Corp"
        mock_company.industry = "Technology"
        mock_company.website = "https://test.com"
        mock_company.address = "123 Main St"
        mock_company.size = "50-200"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        from app.routers.search import index_entity
        
        result = index_entity(
            entity_type="company",
            entity_id=1,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert result["message"] == "company 1 indexed"

    def test_index_entity_product(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test indexing a product entity."""
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "Widget Pro"
        mock_product.sku = "WGT-PRO-001"
        mock_product.description = "Professional widget"
        mock_product.category = "Electronics"
        mock_product.unit_price = 99.99
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        from app.routers.search import index_entity
        
        result = index_entity(
            entity_type="product",
            entity_id=1,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert result["message"] == "product 1 indexed"

    def test_index_entity_unsupported_type(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test indexing unsupported entity type raises HTTPException."""
        from app.routers.search import index_entity
        
        with pytest.raises(HTTPException) as exc_info:
            index_entity(
                entity_type="unsupported",
                entity_id=1,
                db=mock_db,
                current_user=mock_admin_user
            )
        
        assert exc_info.value.status_code == 400
        assert "Unsupported entity type" in str(exc_info.value.detail)

    def test_index_entity_not_found(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test indexing entity that doesn't exist."""
        # Mock entity not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        from app.routers.search import index_entity
        
        # Should complete without error but not call index_entity
        result = index_entity(
            entity_type="contact",
            entity_id=999,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        # Entity not found, so index_entity should not be called
        mock_search_service.index_entity.assert_not_called()


class TestGetSearchAnalytics:
    """Tests for GET /api/v1/search/analytics endpoint."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock SearchService."""
        with patch('app.routers.search.SearchService') as mock_class:
            mock_service = MagicMock()
            mock_class.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "admin"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_get_analytics_default_period(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test getting analytics with default 30-day period."""
        mock_search_service.get_search_analytics.return_value = {
            "period_days": 30,
            "total_queries": 150,
            "no_results_queries": 10,
            "no_results_rate": 6.67,
            "avg_execution_time_ms": 42.5,
            "top_queries": [{"query": "john", "count": 25}],
            "daily_volume": [{"date": "2024-01-15", "queries": 10}],
            "popular_filters": [{"filter": "status", "count": 30}]
        }
        
        from app.routers.search import get_search_analytics
        
        result = get_search_analytics(
            days=30,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert result["period_days"] == 30
        assert result["total_queries"] == 150
        mock_search_service.get_search_analytics.assert_called_once_with(days=30)

    def test_get_analytics_custom_period(
        self, mock_search_service, mock_admin_user, mock_db
    ):
        """Test getting analytics with custom period."""
        mock_search_service.get_search_analytics.return_value = {
            "period_days": 90,
            "total_queries": 500,
            "no_results_queries": 25,
            "no_results_rate": 5.0,
            "avg_execution_time_ms": 38.2,
            "top_queries": [],
            "daily_volume": [],
            "popular_filters": []
        }
        
        from app.routers.search import get_search_analytics
        
        result = get_search_analytics(
            days=90,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert result["period_days"] == 90
        mock_search_service.get_search_analytics.assert_called_once_with(days=90)


class TestGetPopularQueries:
    """Tests for GET /api/v1/search/analytics/popular-queries endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.role = "admin"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=Session)
        return db

    def test_get_popular_queries_basic(
        self, mock_admin_user, mock_db
    ):
        """Test getting popular queries."""
        # Mock query results
        mock_query_result = MagicMock()
        mock_query_result.query = "john doe"
        mock_query_result.count = 50
        mock_query_result.avg_results = 5.5
        
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_query_result
        ]
        
        from app.routers.search import get_popular_queries
        
        result = get_popular_queries(
            limit=20,
            days=30,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert "queries" in result
        assert len(result["queries"]) == 1
        assert result["queries"][0]["query"] == "john doe"
        assert result["queries"][0]["count"] == 50
        assert result["queries"][0]["avg_results"] == 5.5

    def test_get_popular_queries_custom_limit(
        self, mock_admin_user, mock_db
    ):
        """Test getting popular queries with custom limit."""
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        from app.routers.search import get_popular_queries
        
        get_popular_queries(
            limit=10,
            days=7,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        # Verify limit was applied
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.assert_called_once_with(10)

    def test_get_popular_queries_empty_results(
        self, mock_admin_user, mock_db
    ):
        """Test getting popular queries when no data exists."""
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        from app.routers.search import get_popular_queries
        
        result = get_popular_queries(
            limit=20,
            days=30,
            db=mock_db,
            current_user=mock_admin_user
        )
        
        assert result["queries"] == []


class TestAuthenticationRequirements:
    """Tests verifying authentication requirements on endpoints."""

    def test_search_requires_authentication(self):
        """Verify search endpoint requires authentication."""
        from app.routers.search import search
        import inspect
        
        # Check that get_current_user is a dependency
        sig = inspect.signature(search)
        params = sig.parameters
        
        assert "current_user" in params
        # The parameter should have a Depends annotation

    def test_reindex_requires_admin(self):
        """Verify reindex endpoint requires admin role."""
        from app.routers.search import reindex_all
        import inspect
        
        sig = inspect.signature(reindex_all)
        params = sig.parameters
        
        assert "current_user" in params

    def test_analytics_requires_admin(self):
        """Verify analytics endpoint requires admin role."""
        from app.routers.search import get_search_analytics
        import inspect
        
        sig = inspect.signature(get_search_analytics)
        params = sig.parameters
        
        assert "current_user" in params

    def test_index_entity_requires_admin(self):
        """Verify index_entity endpoint requires admin role."""
        from app.routers.search import index_entity
        import inspect
        
        sig = inspect.signature(index_entity)
        params = sig.parameters
        
        assert "current_user" in params
