"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('token_symbol', sa.String(length=20), nullable=True),
        sa.Column('score', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_score'), 'projects', ['score'], unique=False)
    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=True)
    op.create_index(op.f('ix_projects_token_symbol'), 'projects', ['token_symbol'], unique=False)

    # Create investors table
    op.create_table('investors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('profile', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investors_id'), 'investors', ['id'], unique=False)
    op.create_index(op.f('ix_investors_name'), 'investors', ['name'], unique=False)
    op.create_index(op.f('ix_investors_slug'), 'investors', ['slug'], unique=True)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)

    # Create webhooks table
    op.create_table('webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('events', sa.JSON(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhooks_id'), 'webhooks', ['id'], unique=False)

    # Create research_categories table
    op.create_table('research_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_categories_id'), 'research_categories', ['id'], unique=False)
    op.create_index(op.f('ix_research_categories_name'), 'research_categories', ['name'], unique=True)

    # Create funding_rounds table (depends on projects)
    op.create_table('funding_rounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('round_type', sa.String(length=50), nullable=False),
        sa.Column('amount_usd', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('announced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('investors', sa.JSON(), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_funding_rounds_amount_usd'), 'funding_rounds', ['amount_usd'], unique=False)
    op.create_index(op.f('ix_funding_rounds_announced_at'), 'funding_rounds', ['announced_at'], unique=False)
    op.create_index(op.f('ix_funding_rounds_id'), 'funding_rounds', ['id'], unique=False)
    op.create_index(op.f('ix_funding_rounds_project_id'), 'funding_rounds', ['project_id'], unique=False)
    op.create_index(op.f('ix_funding_rounds_round_type'), 'funding_rounds', ['round_type'], unique=False)

    # Create investors_portfolio table (depends on investors and projects)
    op.create_table('investors_portfolio',
        sa.Column('investor_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('first_invested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['investor_id'], ['investors.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('investor_id', 'project_id')
    )

    # Create research table (depends on users)
    op.create_table('research',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_id'), 'research', ['id'], unique=False)
    op.create_index(op.f('ix_research_status'), 'research', ['status'], unique=False)
    op.create_index(op.f('ix_research_title'), 'research', ['title'], unique=False)

    # Create alerts table (depends on users and projects)
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('threshold', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_alert_type'), 'alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_project_id'), 'alerts', ['project_id'], unique=False)
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)

    # Create watchlists table (depends on users and projects)
    op.create_table('watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watchlists_id'), 'watchlists', ['id'], unique=False)
    op.create_index(op.f('ix_watchlists_project_id'), 'watchlists', ['project_id'], unique=False)
    op.create_index(op.f('ix_watchlists_user_id'), 'watchlists', ['user_id'], unique=False)

    # Create unique constraint for user_id + project_id in watchlists
    op.create_unique_constraint('uq_watchlists_user_project', 'watchlists', ['user_id', 'project_id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('watchlists')
    op.drop_table('alerts')
    op.drop_table('research')
    op.drop_table('investors_portfolio')
    op.drop_table('funding_rounds')
    op.drop_table('research_categories')
    op.drop_table('webhooks')
    op.drop_table('api_keys')
    op.drop_table('investors')
    op.drop_table('projects')
    op.drop_table('users')