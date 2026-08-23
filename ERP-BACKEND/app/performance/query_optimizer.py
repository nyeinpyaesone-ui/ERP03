"""
Query Optimizer Module for Database Performance
================================================

This module provides query optimization utilities including:
- Index management and recommendations
- Query analysis and slow query detection
- Connection pooling configuration helpers
- Query plan analysis

Usage Example:
--------------
    optimizer = QueryOptimizer(db_session)
    
    # Get index recommendations for search performance
    recommendations = optimizer.get_index_recommendations()
    
    # Analyze slow queries
    slow_queries = optimizer.analyze_slow_queries(threshold_ms=100)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utility class for database query optimization and index management."""

    def __init__(self, db: Session):
        """
        Initialize query optimizer.
        
        Parameters:
            db (Session): SQLAlchemy database session
        """
        self.db = db

    def get_index_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate index recommendations based on common query patterns.
        
        Returns:
            Dict containing recommended indexes for each table
        """
        recommendations = {
            "search_index": [
                {
                    "name": "idx_search_entity_type_id",
                    "table": "search_indices",
                    "columns": ["entity_type", "entity_id"],
                    "unique": True,
                    "reason": "Composite unique index for upsert operations"
                },
                {
                    "name": "idx_search_searchable_text_gin",
                    "table": "search_indices", 
                    "columns": ["searchable_text"],
                    "unique": False,
                    "using": "gin",
                    "reason": "GIN index for full-text search performance"
                },
                {
                    "name": "idx_search_updated_at",
                    "table": "search_indices",
                    "columns": ["updated_at"],
                    "unique": False,
                    "reason": "Index for ordering by update time"
                },
                {
                    "name": "idx_search_tags_gin",
                    "table": "search_indices",
                    "columns": ["tags"],
                    "unique": False,
                    "using": "gin",
                    "reason": "GIN index for array tag filtering"
                }
            ],
            "invoices": [
                {
                    "name": "idx_invoice_status_issue_date",
                    "table": "invoices",
                    "columns": ["status", "issue_date"],
                    "unique": False,
                    "reason": "Composite index for revenue analytics queries"
                },
                {
                    "name": "idx_invoice_issue_date",
                    "table": "invoices",
                    "columns": ["issue_date"],
                    "unique": False,
                    "reason": "Index for monthly trend analysis"
                }
            ],
            "contacts": [
                {
                    "name": "idx_contact_status",
                    "table": "contacts",
                    "columns": ["status"],
                    "unique": False,
                    "reason": "Index for status-based filtering"
                },
                {
                    "name": "idx_contact_company_id",
                    "table": "contacts",
                    "columns": ["company_id"],
                    "unique": False,
                    "reason": "Index for company-contact joins"
                }
            ],
            "deals": [
                {
                    "name": "idx_deal_created_at",
                    "table": "deals",
                    "columns": ["created_at"],
                    "unique": False,
                    "reason": "Index for monthly deal trend analysis"
                },
                {
                    "name": "idx_deal_stage",
                    "table": "deals",
                    "columns": ["stage"],
                    "unique": False,
                    "reason": "Index for pipeline value calculations"
                }
            ],
            "products": [
                {
                    "name": "idx_product_stock_reorder",
                    "table": "products",
                    "columns": ["quantity_in_stock", "reorder_level"],
                    "unique": False,
                    "reason": "Index for low stock detection queries"
                },
                {
                    "name": "idx_product_category",
                    "table": "products",
                    "columns": ["category"],
                    "unique": False,
                    "reason": "Index for category-based filtering"
                }
            ],
            "employees": [
                {
                    "name": "idx_employee_status",
                    "table": "employees",
                    "columns": ["status"],
                    "unique": False,
                    "reason": "Index for active employee counts"
                },
                {
                    "name": "idx_employee_department",
                    "table": "employees",
                    "columns": ["department_id"],
                    "unique": False,
                    "reason": "Index for department-based queries"
                }
            ],
            "projects": [
                {
                    "name": "idx_project_status",
                    "table": "projects",
                    "columns": ["status"],
                    "unique": False,
                    "reason": "Index for active project counts"
                }
            ],
            "tasks": [
                {
                    "name": "idx_task_status",
                    "table": "tasks",
                    "columns": ["status"],
                    "unique": False,
                    "reason": "Index for completed task counts"
                },
                {
                    "name": "idx_task_project_id",
                    "table": "tasks",
                    "columns": ["project_id"],
                    "unique": False,
                    "reason": "Index for project-task relationships"
                }
            ],
            "activity_logs": [
                {
                    "name": "idx_activity_created_at",
                    "table": "activity_logs",
                    "columns": ["created_at"],
                    "unique": False,
                    "reason": "Index for recent activity queries"
                }
            ]
        }
        
        return recommendations

    def create_recommended_indexes(self, dry_run: bool = True) -> List[str]:
        """
        Generate SQL statements to create recommended indexes.
        
        Parameters:
            dry_run (bool): If True, only generate SQL without executing
            
        Returns:
            List of SQL statements or executed results
        """
        recommendations = self.get_index_recommendations()
        statements = []
        
        for table, indexes in recommendations.items():
            for idx in indexes:
                using_clause = f" USING {idx.get('using', 'btree')}" if idx.get('using') else ""
                columns = ", ".join(idx["columns"])
                
                sql = f"CREATE {'UNIQUE ' if idx.get('unique') else ''}INDEX CONCURRENTLY IF NOT EXISTS {idx['name']} ON {idx['table']}{using_clause} ({columns});"
                statements.append(sql)
                
                if not dry_run:
                    try:
                        self.db.execute(text(sql))
                        self.db.commit()
                        logger.info(f"Created index: {idx['name']}")
                    except Exception as e:
                        logger.error(f"Failed to create index {idx['name']}: {e}")
                        self.db.rollback()
        
        return statements

    def analyze_query_performance(self, query_sql: str) -> Dict[str, Any]:
        """
        Analyze a query's execution plan.
        
        Parameters:
            query_sql (str): SQL query to analyze
            
        Returns:
            Dict containing query plan analysis
        """
        try:
            # Use EXPLAIN ANALYZE for PostgreSQL
            explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_sql}"
            result = self.db.execute(text(explain_sql)).fetchone()
            
            if result and result[0]:
                plan = result[0][0] if isinstance(result[0], list) else result[0]
                return {
                    "success": True,
                    "plan": plan,
                    "analyzed_at": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
        
        return {"success": False, "error": "No plan returned", "analyzed_at": datetime.now().isoformat()}

    def get_table_statistics(self, table_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics about table sizes and row counts.
        
        Parameters:
            table_names (Optional[List[str]]): Specific tables to analyze, or all if None
            
        Returns:
            Dict with table statistics
        """
        stats_query = """
            SELECT 
                relname as table_name,
                n_live_tup as row_count,
                pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                pg_size_pretty(pg_indexes_size(relid)) as index_size
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC;
        """
        
        try:
            result = self.db.execute(text(stats_query)).fetchall()
            statistics = {}
            
            for row in result:
                if table_names is None or row.table_name in table_names:
                    statistics[row.table_name] = {
                        "row_count": row.row_count or 0,
                        "total_size": row.total_size,
                        "index_size": row.index_size
                    }
            
            return statistics
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}

    def detect_n_plus_one_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect potential N+1 query patterns in the codebase.
        
        Returns:
            List of detected patterns with recommendations
        """
        # This would typically integrate with query logging
        # For now, return known patterns based on code analysis
        patterns = [
            {
                "location": "search_service.py:index_all_* methods",
                "pattern": "Loop calling index_entity() for each record",
                "impact": "High - causes N+1 INSERT/UPDATE queries",
                "recommendation": "Use bulk_insert_search_index() from performance.bulk_operations"
            },
            {
                "location": "analytics_service.py:get_dashboard()",
                "pattern": "Multiple separate COUNT queries",
                "impact": "Medium - 6 separate database round trips",
                "recommendation": "Combine into single query using UNION ALL or CTEs"
            },
            {
                "location": "search_service.py:search()",
                "pattern": "Separate count() then fetch query",
                "impact": "Medium - doubles query execution for pagination",
                "recommendation": "Use window functions or cache count separately"
            }
        ]
        
        return patterns
