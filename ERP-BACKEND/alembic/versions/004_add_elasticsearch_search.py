"""Add Elasticsearch search integration tables

Revision ID: 004
Revises: 003
Create Date: 2024-06-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Search indexes table
    op.create_table(
        'search_indexes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('searchable_text', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_type', 'entity_id', name='uq_search_index_entity')
    )
    op.create_index('ix_search_indexes_entity_type', 'search_indexes', ['entity_type'], unique=False)
    op.create_index('ix_search_indexes_searchable_text', 'search_indexes', ['searchable_text'], unique=False, postgresql_using='gin')

    # Search queries analytics table
    op.create_table(
        'search_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('filters', postgresql.JSONB(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('clicked_results', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_queries_created_at', 'search_queries', ['created_at'], unique=False)
    op.create_index('ix_search_queries_query', 'search_queries', ['query'], unique=False)

    # Search suggestions table
    op.create_table(
        'search_suggestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.String(length=255), nullable=False),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False, server_default='autocomplete'),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_used', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('query_text', 'suggestion_type', 'entity_type', name='uq_search_suggestion')
    )

def downgrade() -> None:
    op.drop_table('search_suggestions')
    op.drop_index('ix_search_queries_query', table_name='search_queries')
    op.drop_index('ix_search_queries_created_at', table_name='search_queries')
    op.drop_table('search_queries')
    op.drop_index('ix_search_indexes_searchable_text', table_name='search_indexes')
    op.drop_index('ix_search_indexes_entity_type', table_name='search_indexes')
    op.drop_table('search_indexes')

