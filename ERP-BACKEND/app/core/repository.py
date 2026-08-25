"""
Repository Pattern Base Classes

Provides abstract base classes for data access layer implementing
the Repository pattern for clean separation of concerns.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class RepositoryBase(ABC, Generic[ModelType]):
    """
    Abstract base repository providing CRUD operations.
    
    All repositories should inherit from this class and specify
    their model type via generic parameter.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    @property
    @abstractmethod
    def model(self) -> Type[ModelType]:
        """Return the SQLAlchemy model class for this repository."""
        pass
    
    def get(self, id: int) -> Optional[ModelType]:
        """
        Retrieve a single record by ID.
        
        Args:
            id: Primary key identifier
            
        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_field(self, field: str, value: any) -> Optional[ModelType]:
        """
        Retrieve a single record by arbitrary field.
        
        Args:
            field: Field name to query
            value: Field value to match
            
        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value
        ).first()
    
    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """
        List records with pagination and optional ordering.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            order_by: Field name to order by
            desc: If True, order descending
            
        Returns:
            List of model instances
        """
        query = self.db.query(self.model)
        
        if order_by:
            order_column = getattr(self.model, order_by)
            if desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
        
        return query.offset(skip).limit(limit).all()
    
    def filter(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> List[ModelType]:
        """
        List records with dynamic filtering, pagination, and ordering.
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by
            desc: If True, order descending
            
        Returns:
            List of model instances matching filters
        """
        query = self.db.query(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        if order_by:
            order_column = getattr(self.model, order_by)
            if desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
        
        return query.offset(skip).limit(limit).all()
    
    def search(
        self,
        field: str,
        pattern: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Search records using LIKE pattern matching.
        
        Args:
            field: Field name to search in
            pattern: Search pattern (use % as wildcard)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances matching pattern
        """
        if not hasattr(self.model, field):
            return []
        
        return self.db.query(self.model).filter(
            getattr(self.model, field).ilike(f"%{pattern}%")
        ).offset(skip).limit(limit).all()
    
    def create(self, attributes: dict) -> ModelType:
        """
        Create a new record.
        
        Args:
            attributes: Dictionary of field-value pairs
            
        Returns:
            Created model instance
        """
        obj = self.model(**attributes)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, id: int, attributes: dict) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: Primary key identifier
            attributes: Dictionary of field-value pairs to update
            
        Returns:
            Updated model instance or None if not found
        """
        obj = self.get(id)
        if not obj:
            return None
        
        for field, value in attributes.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, id: int) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Primary key identifier
            
        Returns:
            True if deleted, False if not found
        """
        obj = self.get(id)
        if not obj:
            return False
        
        self.db.delete(obj)
        self.db.commit()
        return True
    
    def count(self, filters: Optional[dict] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Optional dictionary of field-value pairs
            
        Returns:
            Count of matching records
        """
        query = self.db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
    
    def exists(self, id: int) -> bool:
        """
        Check if a record exists.
        
        Args:
            id: Primary key identifier
            
        Returns:
            True if exists, False otherwise
        """
        return self.get(id) is not None
    
    def bulk_create(self, objects: List[dict]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            objects: List of dictionaries with field-value pairs
            
        Returns:
            List of created model instances
        """
        created = []
        try:
            for attrs in objects:
                obj = self.model(**attrs)
                self.db.add(obj)
                created.append(obj)
            
            self.db.commit()
            for obj in created:
                self.db.refresh(obj)
        except Exception:
            self.db.rollback()
            raise
        
        return created
    
    def execute_raw_sql(self, query: str, params: dict = None) -> List[dict]:
        """
        Execute raw SQL query (read-only).
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
            
        Raises:
            ValueError: If query contains write operations
        """
        # Security check: prevent write operations
        query_lower = query.lower().strip()
        if any(query_lower.startswith(op) for op in ['insert', 'update', 'delete', 'drop', 'truncate']):
            raise ValueError("Raw SQL queries must be read-only (SELECT)")
        
        result = self.db.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]
