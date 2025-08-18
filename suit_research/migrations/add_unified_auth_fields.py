"""Add unified authentication fields to users table.

Revision ID: unified_auth_001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid

# revision identifiers
revision = 'unified_auth_001'
down_revision = None
branches = None
depends_on = None


def upgrade():
    """Add unified authentication fields to users table."""
    
    # Create AuthType enum
    auth_type_enum = postgresql.ENUM('email', 'wallet', 'hybrid', name='authtype')
    auth_type_enum.create(op.get_bind())
    
    # Add new columns for unified authentication
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Change id from Integer to UUID
        batch_op.alter_column('id',
                            existing_type=sa.Integer(),
                            type_=postgresql.UUID(as_uuid=True),
                            existing_nullable=False,
                            postgresql_using='gen_random_uuid()')
        
        # Make email nullable for wallet-only users
        batch_op.alter_column('email',
                            existing_type=sa.String(255),
                            nullable=True)
        
        # Rename password_hash to hashed_password and make nullable
        batch_op.alter_column('password_hash',
                            new_column_name='hashed_password',
                            existing_type=sa.String(255),
                            nullable=True)
        
        # Add wallet authentication fields
        batch_op.add_column(sa.Column('wallet_address', sa.String(42), nullable=True))
        batch_op.add_column(sa.Column('network', sa.String(50), nullable=True, default='ethereum'))
        
        # Add authentication type tracking
        batch_op.add_column(sa.Column('auth_type', auth_type_enum, nullable=False, server_default='email'))
        
        # Add verification fields
        batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('wallet_verified', sa.Boolean(), nullable=False, server_default='false'))
        
        # Add last_login timestamp
        batch_op.add_column(sa.Column('last_login', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        
        # Create indexes
        batch_op.create_index('idx_wallet_network', ['wallet_address', 'network'])
        batch_op.create_index('idx_auth_type', ['auth_type'])
        batch_op.create_index('idx_role', ['role'])
        
        # Create unique constraints
        batch_op.create_unique_constraint('uq_user_email', ['email'])
        batch_op.create_unique_constraint('uq_user_wallet', ['wallet_address'])
    
    # Update existing users' auth_type based on their data
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE users 
        SET auth_type = CASE 
            WHEN email IS NOT NULL AND hashed_password IS NOT NULL AND wallet_address IS NOT NULL THEN 'hybrid'
            WHEN wallet_address IS NOT NULL THEN 'wallet'
            ELSE 'email'
        END,
        email_verified = CASE WHEN email IS NOT NULL THEN true ELSE false END,
        wallet_verified = CASE WHEN wallet_address IS NOT NULL THEN true ELSE false END
    """))


def downgrade():
    """Remove unified authentication fields from users table."""
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Drop indexes
        batch_op.drop_index('idx_wallet_network')
        batch_op.drop_index('idx_auth_type')
        batch_op.drop_index('idx_role')
        
        # Drop unique constraints
        batch_op.drop_constraint('uq_user_email', type_='unique')
        batch_op.drop_constraint('uq_user_wallet', type_='unique')
        
        # Remove new columns
        batch_op.drop_column('wallet_address')
        batch_op.drop_column('network')
        batch_op.drop_column('auth_type')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('email_verified')
        batch_op.drop_column('wallet_verified')
        batch_op.drop_column('last_login')
        
        # Rename hashed_password back to password_hash and make non-nullable
        batch_op.alter_column('hashed_password',
                            new_column_name='password_hash',
                            existing_type=sa.String(255),
                            nullable=False)
        
        # Make email non-nullable again
        batch_op.alter_column('email',
                            existing_type=sa.String(255),
                            nullable=False)
        
        # Change id back from UUID to Integer
        batch_op.alter_column('id',
                            existing_type=postgresql.UUID(as_uuid=True),
                            type_=sa.Integer(),
                            existing_nullable=False)
    
    # Drop AuthType enum
    auth_type_enum = postgresql.ENUM('email', 'wallet', 'hybrid', name='authtype')
    auth_type_enum.drop(op.get_bind())