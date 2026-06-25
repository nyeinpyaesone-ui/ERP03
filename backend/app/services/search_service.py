import os
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, text
from sqlalchemy.dialects.postgresql import array
import httpx

from app.models import SearchIndex, SearchQuery, SearchSuggestion, Contact, Company, Product, Employee, Project, Invoice, Document
from app.config import settings

class SearchService:
    """Advanced search service with PostgreSQL full-text search and Elasticsearch support."""

    def __init__(self, db: Session, use_elasticsearch: bool = False):
        self.db = db
        self.use_elasticsearch = use_elasticsearch
        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # ==================== INDEXING ====================

    def index_entity(self, entity_type: str, entity_id: int, title: str, content: str, metadata: Dict[str, Any] = None, tags: List[str] = None):
        """Index or update an entity in the search index."""
        # Build searchable text
        searchable = f"{title} {content}"
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float)):
                    searchable += f" {value}"

        # Check if already indexed
        existing = self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).first()

        if existing:
            existing.title = title
            existing.content = content
            existing.searchable_text = searchable
            existing.metadata = metadata or {}
            existing.tags = tags or []
            existing.updated_at = datetime.utcnow()
        else:
            index = SearchIndex(
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                content=content,
                searchable_text=searchable,
                metadata=metadata or {},
                tags=tags or []
            )
            self.db.add(index)

        self.db.commit()

    def remove_from_index(self, entity_type: str, entity_id: int):
        """Remove an entity from the search index."""
        self.db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).delete()
        self.db.commit()

    def index_all_contacts(self):
        """Index all contacts."""
        contacts = self.db.query(Contact).all()
        for c in contacts:
            self.index_entity(
                "contact",
                c.id,
                f"{c.first_name} {c.last_name}",
                f"{c.email or ''} {c.phone or ''} {c.title or ''} {c.notes or ''}",
                metadata={
                    "email": c.email,
                    "phone": c.phone,
                    "status": c.status,
                    "company_id": c.company_id,
                    "assigned_to": c.assigned_to
                },
                tags=[c.status, "contact"]
            )

    def index_all_companies(self):
        """Index all companies."""
        companies = self.db.query(Company).all()
        for c in companies:
            self.index_entity(
                "company",
                c.id,
                c.name,
                f"{c.industry or ''} {c.website or ''} {c.address or ''} {c.phone or ''}",
                metadata={
                    "industry": c.industry,
                    "size": c.size,
                    "website": c.website
                },
                tags=[c.industry, "company"] if c.industry else ["company"]
            )

    def index_all_products(self):
        """Index all products."""
        products = self.db.query(Product).all()
        for p in products:
            self.index_entity(
                "product",
                p.id,
                p.name,
                f"{p.sku} {p.description or ''} {p.category or ''} {p.supplier or ''}",
                metadata={
                    "sku": p.sku,
                    "category": p.category,
                    "price": float(p.unit_price) if p.unit_price else 0,
                    "stock": p.quantity_in_stock,
                    "status": p.status
                },
                tags=[p.category, p.status, "product"] if p.category else [p.status, "product"]
            )

    def index_all_employees(self):
        """Index all employees."""
        employees = self.db.query(Employee).all()
        for e in employees:
            self.index_entity(
                "employee",
                e.id,
                e.employee_code,
                f"{e.job_title or ''} {e.address or ''} {e.emergency_contact or ''}",
                metadata={
                    "code": e.employee_code,
                    "department_id": e.department_id,
                    "status": e.status,
                    "employment_type": e.employment_type
                },
                tags=[e.status, e.employment_type, "employee"]
            )

    def index_all_documents(self):
        """Index all documents."""
        documents = self.db.query(Document).all()
        for d in documents:
            self.index_entity(
                "document",
                d.id,
                d.title,
                f"{d.filename} {d.extracted_text or ''} {d.mime_type or ''}",
                metadata={
                    "filename": d.filename,
                    "mime_type": d.mime_type,
                    "entity_type": d.entity_type,
                    "file_size": d.file_size
                },
                tags=[d.mime_type, d.entity_type, "document"] if d.mime_type else ["document"]
            )

    def reindex_all(self):
        """Reindex all entities."""
        # Clear existing index
        self.db.query(SearchIndex).delete()
        self.db.commit()

        # Index all entities
        self.index_all_contacts()
        self.index_all_companies()
        self.index_all_products()
        self.index_all_employees()
        self.index_all_documents()

        return {
            "contacts": self.db.query(SearchIndex).filter(SearchIndex.entity_type == "contact").count(),
            "companies": self.db.query(SearchIndex).filter(SearchIndex.entity_type == "company").count(),
            "products": self.db.query(SearchIndex).filter(SearchIndex.entity_type == "product").count(),
            "employees": self.db.query(SearchIndex).filter(SearchIndex.entity_type == "employee").count(),
            "documents": self.db.query(SearchIndex).filter(SearchIndex.entity_type == "document").count(),
        }

    # ==================== SEARCH ====================

    def search(
        self,
        query: str,
        entity_types: List[str] = None,
        filters: Dict[str, Any] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Full-text search with PostgreSQL."""
        start_time = datetime.utcnow()

        # Build base query
        base_query = self.db.query(SearchIndex)

        # Apply text search
        if query and query.strip():
            # Normalize query for PostgreSQL tsvector search
            search_terms = query.strip().split()
            tsquery = " & ".join([f"{term}:*" for term in search_terms])

            base_query = base_query.filter(
                text("to_tsvector('english', searchable_text) @@ to_tsquery('english', :query)")
                .bindparams(query=tsquery)
            )

        # Filter by entity types
        if entity_types:
            base_query = base_query.filter(SearchIndex.entity_type.in_(entity_types))

        # Apply metadata filters
        if filters:
            for key, value in filters.items():
                if key == "tags" and isinstance(value, list):
                    base_query = base_query.filter(
                        SearchIndex.tags.op("&&")(array(value))
                    )
                elif key.startswith("metadata."):
                    meta_key = key.replace("metadata.", "")
                    base_query = base_query.filter(
                        SearchIndex.metadata[meta_key].astext == str(value)
                    )

        # Get total count
        total = base_query.count()

        # Get results with ordering
        results = base_query.order_by(
            SearchIndex.updated_at.desc()
        ).offset(offset).limit(limit).all()

        # Format results
        formatted = []
        for r in results:
            formatted.append({
                "id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "title": r.title,
                "content_preview": r.content[:200] if r.content else "",
                "metadata": r.metadata or {},
                "tags": r.tags or [],
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            })

        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return formatted, total, execution_time

    def get_facets(self, query: str = None, entity_types: List[str] = None) -> Dict[str, Any]:
        """Get facet counts for search results."""
        base_query = self.db.query(SearchIndex)

        if query and query.strip():
            search_terms = query.strip().split()
            tsquery = " & ".join([f"{term}:*" for term in search_terms])
            base_query = base_query.filter(
                text("to_tsvector('english', searchable_text) @@ to_tsquery('english', :query)")
                .bindparams(query=tsquery)
            )

        if entity_types:
            base_query = base_query.filter(SearchIndex.entity_type.in_(entity_types))

        # Entity type facets
        type_counts = self.db.query(
            SearchIndex.entity_type,
            func.count(SearchIndex.id).label("count")
        ).filter(
            SearchIndex.id.in_(base_query.with_entities(SearchIndex.id))
        ).group_by(SearchIndex.entity_type).all()

        # Tag facets
        tag_counts = {}
        all_tags = self.db.query(SearchIndex.tags).filter(
            SearchIndex.id.in_(base_query.with_entities(SearchIndex.id))
        ).all()
        for tags_row in all_tags:
            if tags_row[0]:
                for tag in tags_row[0]:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "entity_types": [
                {"value": t.entity_type, "count": t.count}
                for t in type_counts
            ],
            "tags": [
                {"value": tag, "count": count}
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            ]
        }

    # ==================== SUGGESTIONS ====================

    def get_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions."""
        if not query or len(query) < 2:
            return []

        # Search in suggestions table
        suggestions = self.db.query(SearchSuggestion).filter(
            SearchSuggestion.query_text.ilike(f"%{query}%")
        ).order_by(
            SearchSuggestion.frequency.desc()
        ).limit(limit).all()

        # Also search in indexed titles
        title_matches = self.db.query(SearchIndex).filter(
            SearchIndex.title.ilike(f"%{query}%")
        ).distinct(SearchIndex.title).limit(5).all()

        result = []
        seen = set()

        for s in suggestions:
            if s.query_text not in seen:
                seen.add(s.query_text)
                result.append({
                    "text": s.query_text,
                    "type": s.suggestion_type,
                    "entity_type": s.entity_type,
                    "frequency": s.frequency
                })

        for t in title_matches:
            if t.title and t.title not in seen:
                seen.add(t.title)
                result.append({
                    "text": t.title,
                    "type": "title",
                    "entity_type": t.entity_type,
                    "frequency": 0
                })

        return result[:limit]

    def record_suggestion(self, query: str, entity_type: str = None, entity_id: int = None):
        """Record a search query for suggestion building."""
        existing = self.db.query(SearchSuggestion).filter(
            SearchSuggestion.query_text == query.lower().strip(),
            SearchSuggestion.entity_type == entity_type
        ).first()

        if existing:
            existing.frequency += 1
            existing.last_used = datetime.utcnow()
        else:
            suggestion = SearchSuggestion(
                query_text=query.lower().strip(),
                entity_type=entity_type,
                entity_id=entity_id,
                frequency=1
            )
            self.db.add(suggestion)

        self.db.commit()

    # ==================== ANALYTICS ====================

    def log_query(self, user_id: int, query: str, filters: Dict[str, Any] = None, results_count: int = 0, execution_time_ms: int = 0, clicked_results: List[int] = None):
        """Log a search query for analytics."""
        sq = SearchQuery(
            user_id=user_id,
            query=query,
            filters=filters or {},
            results_count=results_count,
            execution_time_ms=execution_time_ms,
            clicked_results=clicked_results or []
        )
        self.db.add(sq)
        self.db.commit()

    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics."""
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        # Total queries
        total_queries = self.db.query(SearchQuery).filter(
            SearchQuery.created_at >= start_date
        ).count()

        # Top queries
        top_queries = self.db.query(
            SearchQuery.query,
            func.count(SearchQuery.id).label("count")
        ).filter(
            SearchQuery.created_at >= start_date
        ).group_by(SearchQuery.query).order_by(func.count(SearchQuery.id).desc()).limit(20).all()

        # Queries with no results
        no_results = self.db.query(SearchQuery).filter(
            SearchQuery.created_at >= start_date,
            SearchQuery.results_count == 0
        ).count()

        # Average execution time
        avg_time = self.db.query(func.avg(SearchQuery.execution_time_ms)).filter(
            SearchQuery.created_at >= start_date
        ).scalar() or 0

        # Daily query volume
        daily = self.db.query(
            func.date(SearchQuery.created_at).label("date"),
            func.count(SearchQuery.id).label("count")
        ).filter(
            SearchQuery.created_at >= start_date
        ).group_by(func.date(SearchQuery.created_at)).order_by("date").all()

        # Popular filters
        filter_usage = {}
        queries_with_filters = self.db.query(SearchQuery).filter(
            SearchQuery.created_at >= start_date,
            SearchQuery.filters != None
        ).all()
        for q in queries_with_filters:
            if q.filters:
                for key in q.filters.keys():
                    filter_usage[key] = filter_usage.get(key, 0) + 1

        return {
            "period_days": days,
            "total_queries": total_queries,
            "no_results_queries": no_results,
            "no_results_rate": (no_results / total_queries * 100) if total_queries > 0 else 0,
            "avg_execution_time_ms": round(float(avg_time), 2),
            "top_queries": [
                {"query": q.query, "count": q.count}
                for q in top_queries
            ],
            "daily_volume": [
                {"date": str(d.date), "queries": d.count}
                for d in daily
            ],
            "popular_filters": [
                {"filter": k, "count": v}
                for k, v in sorted(filter_usage.items(), key=lambda x: x[1], reverse=True)
            ]
        }

