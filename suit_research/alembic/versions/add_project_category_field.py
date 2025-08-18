"""Add category field to projects table

Revision ID: add_project_category
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_project_category'
down_revision = None  # Update this with the latest revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add category field to projects table."""
    # Add category column to projects table
    op.add_column('projects', sa.Column('category', sa.Text(), nullable=True))
    
    # Create index for better query performance on category filtering
    op.create_index('ix_projects_category', 'projects', ['category'])


def downgrade() -> None:
    """Remove category field from projects table."""
    # Drop index first
    op.drop_index('ix_projects_category', table_name='projects')
    
    # Drop category column
    op.drop_column('projects', 'category')