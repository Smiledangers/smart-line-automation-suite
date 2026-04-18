"""Add api_keys and webhooks tables

Revision ID: 005_add_api_keys_webhooks
Revises: 004_add_ai_tables
Create Date: 2026-04-18 19:10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '005_add_api_keys_webhooks'
down_revision: Union[str, None] = '004_add_ai_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('can_send_message', sa.Boolean(), nullable=True, default=True),
        sa.Column('can_read_conversation', sa.Boolean(), nullable=True, default=True),
        sa.Column('can_read_stats', sa.Boolean(), nullable=True, default=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True, default=60),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_key'), 'api_keys', ['key'], unique=True)
    
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=64), nullable=True),
        sa.Column('event_message_received', sa.Boolean(), nullable=True, default=True),
        sa.Column('event_message_sent', sa.Boolean(), nullable=True, default=False),
        sa.Column('event_conversation_started', sa.Boolean(), nullable=True, default=False),
        sa.Column('event_conversation_ended', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('last_status_code', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_webhooks_id'), 'webhooks', ['id'], unique=False)
    
    # Add new columns to ai_conversations table
    op.add_column('ai_conversations', sa.Column('agent_type', sa.String(length=20), nullable=True, default='ai'))
    op.add_column('ai_conversations', sa.Column('status', sa.String(length=20), nullable=True, default='active'))
    op.add_column('ai_conversations', sa.Column('assigned_agent_id', sa.Integer(), nullable=True))
    op.add_column('ai_conversations', sa.Column('platform', sa.String(length=20), nullable=True))
    op.add_column('ai_conversations', sa.Column('platform_user_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Drop columns from ai_conversations
    op.drop_column('ai_conversations', 'platform_user_id')
    op.drop_column('ai_conversations', 'platform')
    op.drop_column('ai_conversations', 'assigned_agent_id')
    op.drop_column('ai_conversations', 'status')
    op.drop_column('ai_conversations', 'agent_type')
    
    # Drop tables
    op.drop_table('webhooks')
    op.drop_index(op.f('ix_webhooks_id'), table_name='webhooks')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_api_keys_key'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')