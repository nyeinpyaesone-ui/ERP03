from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.auth import get_current_user, require_admin
from app.services.search_service import SearchService
from app.services.activity_log import log_activity

router = APIRouter(prefix="/api/v1/search", tags=["Advanced Search"])

# Schemas
class SearchRequest(BaseModel):
    query: str
    entity_types: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 20
    offset: int = 0

class SearchResult(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    title: str
    content_preview: str
    metadata: Dict[str, Any]
    tags: List[str]
    updated_at: Optional[str]

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    execution_time_ms: int
    facets: Dict[str, Any]
    page: int
    per_page: int

class SuggestionResponse(BaseModel):
    text: str
    type: str
    entity_type: Optional[str]
    frequency: int

class SearchAnalytics(BaseModel):
    period_days: int
    total_queries: int
    no_results_queries: int
    no_results_rate: float
    avg_execution_time_ms: float
    top_queries: List[Dict[str, Any]]
    daily_volume: List[Dict[str, Any]]
    popular_filters: List[Dict[str, Any]]

# ==================== SEARCH ====================

@router.post("/", response_model=SearchResponse)
def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Advanced full-text search across all indexed entities.
    Supports entity type filtering, metadata filters, and faceted results.
    """
    service = SearchService(db)

    results, total, execution_time = service.search(
        query=request.query,
        entity_types=request.entity_types,
        filters=request.filters,
        limit=request.limit,
        offset=request.offset
    )

    facets = service.get_facets(
        query=request.query,
        entity_types=request.entity_types
    )

    # Log query for analytics
    service.log_query(
        user_id=current_user.id,
        query=request.query,
        filters=request.filters,
        results_count=total,
        execution_time_ms=execution_time
    )

    # Record suggestion
    if request.query and len(request.query) >= 3:
        service.record_suggestion(request.query)

    log_activity(db, user_id=current_user.id, action="search", entity_type="search", details={"query": request.query, "results": total})

    return {
        "query": request.query,
        "results": results,
        "total": total,
        "execution_time_ms": execution_time,
        "facets": facets,
        "page": (request.offset // request.limit) + 1,
        "per_page": request.limit
    }

@router.get("/")
def search_get(
    q: str = Query(..., description="Search query"),
    types: Optional[str] = Query(None, description="Comma-separated entity types"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """GET endpoint for search (useful for browser/search engine integration)."""
    service = SearchService(db)

    entity_types = types.split(",") if types else None

    results, total, execution_time = service.search(
        query=q,
        entity_types=entity_types,
        limit=limit,
        offset=offset
    )

    facets = service.get_facets(query=q, entity_types=entity_types)

    service.log_query(
        user_id=current_user.id,
        query=q,
        results_count=total,
        execution_time_ms=execution_time
    )

    return {
        "query": q,
        "results": results,
        "total": total,
        "execution_time_ms": execution_time,
        "facets": facets,
        "page": (offset // limit) + 1,
        "per_page": limit
    }

# ==================== SUGGESTIONS ====================

@router.get("/suggestions", response_model=List[SuggestionResponse])
def get_suggestions(
    q: str = Query(..., min_length=2, description="Query prefix for suggestions"),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get autocomplete suggestions for search queries."""
    service = SearchService(db)
    suggestions = service.get_suggestions(q, limit=limit)
    return suggestions

# ==================== FACETS ====================

@router.get("/facets")
def get_facets(
    q: Optional[str] = Query(None, description="Optional query to filter facets"),
    types: Optional[str] = Query(None, description="Comma-separated entity types"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get facet counts for search results."""
    service = SearchService(db)
    entity_types = types.split(",") if types else None
    return service.get_facets(query=q, entity_types=entity_types)

# ==================== INDEXING ====================

@router.post("/reindex")
def reindex_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reindex all entities for search. Admin only."""
    service = SearchService(db)
    counts = service.reindex_all()

    log_activity(db, user_id=current_user.id, action="search_reindex", entity_type="search", details=counts)

    return {
        "status": "success",
        "message": "All entities reindexed",
        "counts": counts
    }

@router.post("/index/{entity_type}/{entity_id}")
def index_entity(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Index a specific entity. Admin only."""
    service = SearchService(db)

    # Fetch entity based on type
    if entity_type == "contact":
        from app.models import Contact
        entity = db.query(Contact).filter(Contact.id == entity_id).first()
        if entity:
            service.index_entity("contact", entity.id, f"{entity.first_name} {entity.last_name}",
                f"{entity.email or ''} {entity.phone or ''} {entity.title or ''} {entity.notes or ''}",
                metadata={"email": entity.email, "status": entity.status})
    elif entity_type == "company":
        from app.models import Company
        entity = db.query(Company).filter(Company.id == entity_id).first()
        if entity:
            service.index_entity("company", entity.id, entity.name,
                f"{entity.industry or ''} {entity.website or ''} {entity.address or ''}",
                metadata={"industry": entity.industry, "size": entity.size})
    elif entity_type == "product":
        from app.models import Product
        entity = db.query(Product).filter(Product.id == entity_id).first()
        if entity:
            service.index_entity("product", entity.id, entity.name,
                f"{entity.sku} {entity.description or ''} {entity.category or ''}",
                metadata={"sku": entity.sku, "category": entity.category, "price": float(entity.unit_price) if entity.unit_price else 0})
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported entity type: {entity_type}")

    return {"message": f"{entity_type} {entity_id} indexed"}

# ==================== ANALYTICS ====================

@router.get("/analytics")
def get_search_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get search analytics. Admin only."""
    service = SearchService(db)
    return service.get_search_analytics(days=days)

@router.get("/analytics/popular-queries")
def get_popular_queries(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get most popular search queries. Admin only."""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    start_date = datetime.utcnow() - timedelta(days=days)

    queries = db.query(
        SearchQuery.query,
        func.count(SearchQuery.id).label("count"),
        func.avg(SearchQuery.results_count).label("avg_results")
    ).filter(
        SearchQuery.created_at >= start_date
    ).group_by(SearchQuery.query).order_by(func.count(SearchQuery.id).desc()).limit(limit).all()

    return {
        "queries": [
            {"query": q.query, "count": q.count, "avg_results": round(float(q.avg_results or 0), 1)}
            for q in queries
        ]
    }

from app.models import SearchQuery

