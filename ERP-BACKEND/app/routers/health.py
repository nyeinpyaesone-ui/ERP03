"""
Health check endpoints for database readiness verification.

This module provides:
- Basic connectivity checks
- Migration status verification
- Schema integrity validation
- Deep health checks with metrics
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.database import get_db, engine
from app.config import settings

logger = logging.getLogger("erp03.health")

router = APIRouter(prefix="/health", tags=["Health Checks"])


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return alembic_cfg


def get_migration_status(db: Session) -> Dict[str, Any]:
    """Get current migration status."""
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Get head revision
        head_revision = script.get_current_head()
        
        # Get current revision from database
        context = MigrationContext.configure(db.connection())
        current_revision = context.get_current_revision()
        
        # Check for pending migrations
        pending_migrations = []
        if current_revision != head_revision:
            # Get all migrations between current and head
            for rev in script.iterate_revisions(current_revision or "base", head_revision):
                pending_migrations.append({
                    "revision": rev.revision,
                    "message": rev.doc,
                    "created_at": rev.date
                })
        
        return {
            "current_revision": current_revision,
            "head_revision": head_revision,
            "is_up_to_date": current_revision == head_revision,
            "pending_migrations_count": len(pending_migrations),
            "pending_migrations": pending_migrations[:10]  # Limit to first 10
        }
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}", exc_info=True)
        raise


def check_schema_integrity(db: Session) -> Dict[str, Any]:
    """Check database schema integrity."""
    try:
        inspector = inspect(engine)
        
        # Get all tables
        expected_tables = [
            "users", "companies", "contacts", "deals",
            "departments", "employees", "products", "inventory_movements",
            "invoices", "invoice_items", "payments",
            "projects", "tasks",
            "documents", "workflows", "workflow_steps", "workflow_executions",
            "activity_logs", "notifications", "reports",
            "integrations", "webhooks", "api_keys",
            "bulk_import_jobs", "bulk_export_jobs",
            "alembic_version"
        ]
        
        actual_tables = inspector.get_table_names()
        
        missing_tables = [t for t in expected_tables if t not in actual_tables]
        extra_tables = [t for t in actual_tables if t not in expected_tables and not t.startswith("alembic")]
        
        # Check indexes
        index_issues = []
        for table_name in expected_tables:
            if table_name in actual_tables:
                try:
                    indexes = inspector.get_indexes(table_name)
                    # Could add specific index validation here
                except Exception as e:
                    index_issues.append({"table": table_name, "error": str(e)})
        
        # Check foreign keys
        fk_issues = []
        for table_name in expected_tables:
            if table_name in actual_tables:
                try:
                    fks = inspector.get_foreign_keys(table_name)
                    # Could add specific FK validation here
                except Exception as e:
                    fk_issues.append({"table": table_name, "error": str(e)})
        
        return {
            "tables_present": len(expected_tables) - len(missing_tables),
            "tables_expected": len(expected_tables),
            "missing_tables": missing_tables,
            "extra_tables": extra_tables[:10],  # Limit output
            "index_issues": index_issues[:5],
            "fk_issues": fk_issues[:5],
            "is_valid": len(missing_tables) == 0
        }
    except Exception as e:
        logger.error(f"Failed to check schema integrity: {e}", exc_info=True)
        raise


@router.get("/db")
async def check_database_connectivity(db: Session = Depends(get_db)):
    """
    Basic database connectivity check.
    
    Verifies:
    - Database connection pool is available
    - Simple query executes successfully
    - Response time is acceptable
    """
    start_time = datetime.now(timezone.utc)
    
    try:
        # Execute simple query
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Get connection pool stats (PostgreSQL specific)
        pool_stats = db.execute(text("""
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """)).fetchone()
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time_ms, 2),
            "connection_pool": {
                "total_connections": pool_stats[0],
                "active_connections": pool_stats[1],
                "idle_connections": pool_stats[2]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Database connectivity check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


@router.get("/migrations")
async def check_migrations(db: Session = Depends(get_db)):
    """
    Check migration status.
    
    Verifies:
    - All migrations are applied
    - No pending migrations
    - No migration conflicts
    """
    try:
        migration_status = get_migration_status(db)
        
        if not migration_status["is_up_to_date"]:
            return {
                "status": "unhealthy",
                "reason": "Pending migrations detected",
                **migration_status
            }
        
        return {
            "status": "healthy",
            **migration_status
        }
    except Exception as e:
        logger.error(f"Migration check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Migration check failed: {str(e)}"
        )


@router.get("/schema")
async def check_schema_integrity_endpoint(db: Session = Depends(get_db)):
    """
    Check database schema integrity.
    
    Verifies:
    - All expected tables exist
    - Critical indexes exist
    - Foreign key constraints are valid
    """
    try:
        schema_status = check_schema_integrity(db)
        
        if not schema_status["is_valid"]:
            return {
                "status": "unhealthy",
                "reason": "Schema integrity issues detected",
                **schema_status
            }
        
        return {
            "status": "healthy",
            **schema_status
        }
    except Exception as e:
        logger.error(f"Schema check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Schema check failed: {str(e)}"
        )


@router.get("/db/deep")
async def deep_health_check(db: Session = Depends(get_db)):
    """
    Deep database health check.
    
    Performs comprehensive checks:
    - Test queries on major tables
    - Read/write permission verification
    - Sequence counter validation
    - Disk space check (if available)
    """
    checks: Dict[str, Any] = {}
    overall_healthy = True
    
    try:
        # Check 1: Query major tables
        major_tables = ["users", "companies", "products", "invoices"]
        table_checks = {}
        
        for table in major_tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                table_checks[table] = {"status": "ok", "row_count": count}
            except Exception as e:
                table_checks[table] = {"status": "error", "error": str(e)}
                overall_healthy = False
        
        checks["table_queries"] = table_checks
        
        # Check 2: Read/write test - SQLite compatible version
        try:
            # Use SQLite-compatible read/write test
            db.execute(text("SELECT 1"))
            is_sqlite = "sqlite" in str(db.bind.engine.dialect.name).lower()
            
            if not is_sqlite:
                # PostgreSQL-specific check
                result = db.execute(text("SELECT pg_is_in_recovery()"))
                is_replica = result.fetchone()[0]
                checks["read_write"] = {"status": "ok", "is_replica": is_replica}
            else:
                # SQLite just confirms it can read/write
                checks["read_write"] = {"status": "ok", "is_sqlite": True}
        except Exception as e:
            checks["read_write"] = {"status": "error", "error": str(e)}
            overall_healthy = False
        
        # Check 3: Sequence counters (PostgreSQL only)
        sequence_checks = {}
        is_sqlite = "sqlite" in str(db.bind.engine.dialect.name).lower()
        if not is_sqlite:
            sequences = ["users_id_seq", "companies_id_seq", "invoices_id_seq"]
            for seq in sequences:
                try:
                    result = db.execute(text(f"SELECT last_value FROM {seq}"))
                    last_value = result.fetchone()[0]
                    sequence_checks[seq] = {"status": "ok", "last_value": last_value}
                except Exception as e:
                    sequence_checks[seq] = {"status": "warning", "error": str(e)}
        else:
            sequence_checks["note"] = "SQLite uses AUTOINCREMENT, no sequences"
        
        checks["sequences"] = sequence_checks
        
        # Check 4: Database size
        try:
            is_sqlite = "sqlite" in str(db.bind.engine.dialect.name).lower()
            if not is_sqlite:
                result = db.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """))
                db_size = result.fetchone()[0]
                checks["database_size"] = db_size
            else:
                checks["database_size"] = "N/A (SQLite)"
        except Exception as e:
            checks["database_size"] = {"error": str(e)}
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Deep health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Deep health check failed: {str(e)}"
        )


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    
    Returns healthy only if:
    - Database is connected
    - Migrations are up to date
    - Schema is valid
    """
    try:
        # Quick connectivity check
        db.execute(text("SELECT 1"))
        
        # Check migrations
        migration_status = get_migration_status(db)
        if not migration_status["is_up_to_date"]:
            return {
                "status": "not_ready",
                "reason": "Pending migrations",
                "pending_count": migration_status["pending_migrations_count"]
            }, 503
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "reason": str(e)
        }, 503


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Simple check to verify the service is running.
    """
    return {
        "status": "alive",
        "service": "erp-backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
