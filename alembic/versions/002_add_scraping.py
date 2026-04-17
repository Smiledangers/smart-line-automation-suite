"""Add scraping tables."""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scraping_jobs table
    op.create_table(
        'scraping_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('website_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, default='pending'),
        sa.Column('priority', sa.Integer(), nullable=True, default=0),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=True, default=3),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_scraping_jobs_status', 'scraping_jobs', ['status'])
    op.create_index('ix_scraping_jobs_scheduled_at', 'scraping_jobs', ['scheduled_at'])

    # Create scraping_results table
    op.create_table(
        'scraping_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(2048), nullable=True),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['scraping_jobs.id'], ondelete='CASCADE')
    )
    op.create_index('ix_scraping_results_job_id', 'scraping_results', ['job_id'])


def downgrade() -> None:
    op.drop_index('ix_scraping_results_job_id', table_name='scraping_results')
    op.drop_table('scraping_results')
    op.drop_index('ix_scraping_jobs_scheduled_at', table_name='scraping_jobs')
    op.drop_index('ix_scraping_jobs_status', table_name='scraping_jobs')
    op.drop_table('scraping_jobs')