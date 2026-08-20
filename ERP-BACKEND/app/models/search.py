"""Search models: SearchIndex, SearchQuery, SearchSuggestion."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Use JSON for SQLite compatibility in tests, JSONB for PostgreSQL in production
try:
    from sqlalchemy import create_engine
    test_engine = create_engine("sqlite:///:memory:")
    USE_JSONB = False
except:
    USE_JSONB = True

if not USE_JSONB:
    JSONB = type('JSON', (), {})  # Fallback to JSON


class SearchIndex(Base):
    __tablename__ = "search_indexes"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    searchable_text = Column(Text, nullable=False)
    meta_data = Column(JSONB, nullable=True)  # Renamed from metadata (reserved word)
    tags = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', name='uq_search_index_entity'),
    )


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    query = Column(String(500), nullable=False)
    filters = Column(JSONB, nullable=True)
    results_count = Column(Integer, nullable=False, server_default="0")
    execution_time_ms = Column(Integer, nullable=False, server_default="0")
    clicked_results = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class SearchSuggestion(Base):
    __tablename__ = "search_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(500), nullable=False, index=True)
    suggestion_type = Column(String(100), nullable=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    frequency = Column(Integer, nullable=False, server_default="1")
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
