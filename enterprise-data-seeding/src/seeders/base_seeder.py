"""
Base seeder class providing common functionality for all seeders.

Implements enterprise patterns:
- Idempotency (check before insert)
- Transaction safety
- Audit logging
- Error handling and rollback
- Batch processing
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class SeederResult:
    """Result of a seeding operation."""
    
    success: bool
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_processed(self) -> int:
        """Total records processed (created + updated + skipped)."""
        return self.records_created + self.records_updated + self.records_skipped
    
    def merge(self, other: "SeederResult") -> "SeederResult":
        """
        Combine this result with another seeding result.
        
        Parameters:
            other (SeederResult): The result to combine with this result.
        
        Returns:
            SeederResult: A combined result with aggregated counts, messages, and duration.
        """
        return SeederResult(
            success=self.success and other.success,
            records_created=self.records_created + other.records_created,
            records_updated=self.records_updated + other.records_updated,
            records_skipped=self.records_skipped + other.records_skipped,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            duration_seconds=self.duration_seconds + other.duration_seconds,
            timestamp=min(self.timestamp, other.timestamp),
        )


class BaseSeeder(ABC):
    """
    Abstract base class for all seeders.
    
    Provides:
    - Idempotent operations
    - Transaction management
    - Logging and audit trail
    - Error handling
    - Progress tracking
    """
    
    def __init__(
        self,
        session: AsyncSession,
        dry_run: bool = False,
        batch_size: int = 100,
    ):
        """
        Initialize a seeder with a database session and processing options.
        
        Parameters:
            session (AsyncSession): Database session used for seeding operations.
            dry_run (bool): Whether to preview changes without applying them.
            batch_size (int): Number of records processed in each batch.
        """
        self.session = session
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def seed(self) -> SeederResult:
        """
        Perform the seeding operation.
        
        Returns:
            SeederResult: The operation's status and statistics.
        """
        pass
    
    @abstractmethod
    async def get_seed_data(self) -> list[dict[str, Any]]:
        """
        Provide the records to seed.
        
        Returns:
            list[dict[str, Any]]: Seed records represented as dictionaries.
        """
        pass
    
    async def check_exists(
        self,
        model: Any,
        unique_field: str,
        value: Any,
    ) -> Optional[Any]:
        """
        Finds a record whose unique field matches the specified value.
        
        Parameters:
            model (Any): SQLAlchemy model class to query.
            unique_field (str): Name of the field to match.
            value (Any): Value to compare against the field.
        
        Returns:
            Optional[Any]: The matching record, or `None` if no record is found.
        """
        from sqlalchemy import select
        
        stmt = select(model).where(getattr(model, unique_field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def upsert(
        self,
        model: Any,
        data: dict[str, Any],
        unique_field: str,
    ) -> tuple[Any, bool]:
        """
        Insert a record or update the existing record identified by a unique field.
        
        Parameters:
            model (Any): SQLAlchemy model class.
            data (dict[str, Any]): Field values for the record.
            unique_field (str): Name of the field used to identify an existing record.
        
        Returns:
            tuple[Any, bool]: The record and `true` if it was created, `false` if an existing record was updated.
        """
        existing = await self.check_exists(model, unique_field, data.get(unique_field))
        
        if existing:
            # Update existing record
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            self.logger.debug(f"Updated {model.__tablename__}: {unique_field}={data[unique_field]}")
            return existing, False
        else:
            # Create new record
            record = model(**data)
            self.session.add(record)
            await self.session.flush()
            self.logger.debug(f"Created {model.__tablename__}: {unique_field}={data[unique_field]}")
            return record, True
    
    async def bulk_insert(
        self,
        model: Any,
        records: list[dict[str, Any]],
    ) -> int:
        """
        Insert records in batches, optionally applying them to the database.
        
        Parameters:
            model (Any): SQLAlchemy model class for the records.
            records (list[dict[str, Any]]): Record values to process.
        
        Returns:
            int: Number of records processed, including dry-run records.
        """
        from sqlalchemy import insert
        
        inserted_count = 0
        
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            if not self.dry_run:
                stmt = insert(model).values(batch)
                await self.session.execute(stmt)
                await self.session.flush()
            
            inserted_count += len(batch)
            self.logger.info(f"Inserted batch {i // self.batch_size + 1}/{(len(records) - 1) // self.batch_size + 1}")
        
        return inserted_count
    
    def log_info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, extra=kwargs)
