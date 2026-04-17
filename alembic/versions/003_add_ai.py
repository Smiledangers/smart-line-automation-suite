"""Add AI conversation tables."""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_conversations table
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('model', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'])

    # Create ai_messages table
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE')
    )
    op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_ai_messages_conversation_id', table_name='ai_messages')
    op.drop_table('ai_messages')
    op.drop_index('ix_ai_conversations_user_id', table_name='ai_conversations')
    op.drop_table('ai_conversations')