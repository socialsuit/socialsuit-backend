"""User model for authentication and authorization with unified auth support."""

import uuid
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Index, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum

from app.core.database import Base


class AuthType(PyEnum):
    EMAIL = "email"
    WALLET = "wallet"
    HYBRID = "hybrid"  # User has both email and wallet linked


class User(Base):
    """User model with unified authentication support."""
    
    __tablename__ = "users"
    
    # ✅ Primary key: UUID, PostgreSQL-native
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )
    
    # ✅ Email - now nullable for wallet-only users
    email = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )
    
    # ✅ Renamed from password_hash and made nullable for wallet-only users
    hashed_password = Column(
        String(255),
        nullable=True
    )
    
    # ✅ Wallet Address — for Web3 users
    wallet_address = Column(
        String(42),  # 42 chars for Ethereum-style addresses
        unique=True,
        nullable=True,
        index=True
    )
    
    network = Column(
        String(50),
        nullable=True,
        default="ethereum"
    )
    
    # ✅ Authentication type tracking
    auth_type = Column(
        Enum(AuthType),
        nullable=False,
        default=AuthType.EMAIL
    )
    
    # Keep existing role system
    role = Column(String(50), default="user", nullable=False, index=True)  # user, admin, analyst
    
    # Optional fields for extended functionality
    username = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Enhanced verification fields
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # ✅ Email verification status
    email_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # ✅ Wallet verification status
    wallet_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    last_login = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_wallet_network', 'wallet_address', 'network'),
        Index('idx_auth_type', 'auth_type'),
        Index('idx_role', 'role'),
        UniqueConstraint('email', name='uq_user_email'),
        UniqueConstraint('wallet_address', name='uq_user_wallet'),
        {'extend_existing': True}
    )
    
    def has_email_auth(self) -> bool:
        """Check if user has email authentication set up."""
        return self.email is not None and self.hashed_password is not None
    
    def has_wallet_auth(self) -> bool:
        """Check if user has wallet authentication set up."""
        return self.wallet_address is not None
    
    def get_auth_methods(self) -> List[str]:
        """Get list of available authentication methods for this user."""
        methods = []
        if self.has_email_auth():
            methods.append("email")
        if self.has_wallet_auth():
            methods.append("wallet")
        return methods
    
    def update_auth_type(self):
        """Update auth_type based on available authentication methods."""
        if self.has_email_auth() and self.has_wallet_auth():
            self.auth_type = AuthType.HYBRID
        elif self.has_wallet_auth():
            self.auth_type = AuthType.WALLET
        else:
            self.auth_type = AuthType.EMAIL
    
    # Relationships
    # research_items = relationship("Research", back_populates="owner")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, wallet={self.wallet_address}, role={self.role})>"