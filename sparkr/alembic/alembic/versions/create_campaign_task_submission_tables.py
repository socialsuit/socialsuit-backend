"""create campaign, task, and submission tables

Revision ID: 01a2b3c4d5e6
Revises: 
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from enum import Enum

# revision identifiers, used by Alembic
revision = '01a2b3c4d5e6'
down_revision = None
branch_labels = None
depends_on = None


# Define enums for migration
class StatusEnum(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PlatformEnum(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    OTHER = "other"


class VerificationStatusEnum(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


def upgrade() -> None:
    # Create users table if it doesn't exist
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('submission_url', sa.String(), nullable=False),
        sa.Column('tweet_id', sa.String(), nullable=True),
        sa.Column('ig_post_id', sa.String(), nullable=True),
        sa.Column('proof_url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('points_awarded', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_campaigns_name'), 'campaigns', ['name'], unique=False)
    op.create_index(op.f('ix_tasks_campaign_id'), 'tasks', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_submissions_task_id'), 'submissions', ['task_id'], unique=False)
    op.create_index(op.f('ix_submissions_user_id'), 'submissions', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('submissions')
    op.drop_table('tasks')
    op.drop_table('campaigns')
    # Don't drop users table as it might be used by other parts of the application