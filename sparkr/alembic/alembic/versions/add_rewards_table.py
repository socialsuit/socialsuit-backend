"""Add rewards table and total_points to users

Revision ID: add_rewards_table
Revises: create_campaign_task_submission_tables
Create Date: 2023-06-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'add_rewards_table'
down_revision = 'create_campaign_task_submission_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add total_points column to users table
    op.add_column('users', sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'))
    
    # Create rewards table
    op.create_table(
        'rewards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('submission_id', sa.String(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop rewards table
    op.drop_table('rewards')
    
    # Remove total_points column from users table
    op.drop_column('users', 'total_points')