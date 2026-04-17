"""Initial migration - create users and line_users tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Create line_users table
    op.create_table(
        'line_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('line_user_id', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('picture_url', sa.String(512), nullable=True),
        sa.Column('status_message', sa.String(512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_line_users_line_user_id', 'line_users', ['line_user_id'])


def downgrade() -> None:
    op.drop_index('ix_line_users_line_user_id', table_name='line_users')
    op.drop_table('line_users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')