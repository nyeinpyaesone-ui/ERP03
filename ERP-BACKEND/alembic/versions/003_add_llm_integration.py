"""Add LLM integration tables

Revision ID: 003
Revises: 002
Create Date: 2024-06-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # LLM Models table
    op.create_table(
        'llm_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='ollama'),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('supports_streaming', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('supports_tools', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('context_window', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id')
    )

    # AI Conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('context', postgresql.JSONB(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'], unique=False)

    # AI Messages table
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('tool_calls', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'], unique=False)

    # LLM Usage Analytics table
    op.create_table(
        'llm_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(length=100), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_llm_usage_created_at', 'llm_usage', ['created_at'], unique=False)

    # AI Prompt Templates table
    op.create_table(
        'ai_prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=True),
        sa.Column('variables', postgresql.JSONB(), nullable=True),
        sa.Column('model_id', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Insert default LLM models
    op.execute("""
        INSERT INTO llm_models (name, provider, model_id, display_name, description, parameters, is_active, is_default, supports_streaming, supports_tools, context_window) VALUES
        ('qwen3.6', 'ollama', 'qwen3.6', 'Qwen 3.6', 'Alibaba Qwen 3.6 - General purpose business AI', '{"temperature": 0.7, "top_p": 0.9}', true, true, true, true, 32768),
        ('llama3.1', 'ollama', 'llama3.1', 'Llama 3.1', 'Meta Llama 3.1 - Open source LLM', '{"temperature": 0.7, "top_p": 0.9}', true, false, true, true, 128000),
        ('mistral', 'ollama', 'mistral', 'Mistral', 'Mistral AI - Fast and efficient', '{"temperature": 0.7, "top_p": 0.9}', true, false, true, false, 32768),
        ('codellama', 'ollama', 'codellama', 'Code Llama', 'Meta Code Llama - Code generation specialist', '{"temperature": 0.2, "top_p": 0.95}', true, false, true, false, 16384)
    """)

    # Insert default prompt templates
    op.execute("""
        INSERT INTO ai_prompt_templates (name, display_name, description, system_prompt, category, is_active) VALUES
        ('business_analyst', 'Business Analyst', 'Analyze business data and provide insights', 'You are a senior business analyst. Analyze the provided data and give actionable insights with specific numbers and trends. Be concise and data-driven.', 'analytics', true),
        ('email_writer', 'Email Writer', 'Draft professional business emails', 'You are a professional business communications specialist. Draft clear, concise, and professional emails. Maintain a friendly but professional tone.', 'communication', true),
        ('proposal_generator', 'Proposal Generator', 'Generate business proposals and quotes', 'You are a business development expert. Create compelling proposals that highlight value, include pricing structure, and address client needs. Use professional formatting.', 'sales', true),
        ('report_summarizer', 'Report Summarizer', 'Summarize long reports and documents', 'You are an executive assistant. Summarize reports into key points, action items, and recommendations. Use bullet points and keep it to one page.', 'productivity', true),
        ('data_extractor', 'Data Extractor', 'Extract structured data from unstructured text', 'You are a data extraction specialist. Extract structured information from text and return it in a clear format. Identify key entities, dates, amounts, and relationships.', 'data', true)
    """)

def downgrade() -> None:
    op.drop_table('ai_prompt_templates')
    op.drop_index('ix_llm_usage_created_at', table_name='llm_usage')
    op.drop_table('llm_usage')
    op.drop_index('ix_ai_messages_conversation_id', table_name='ai_messages')
    op.drop_table('ai_messages')
    op.drop_index('ix_ai_conversations_user_id', table_name='ai_conversations')
    op.drop_table('ai_conversations')
    op.drop_table('llm_models')

