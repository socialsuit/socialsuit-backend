import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID  # For PostgreSQL UUID support
from datetime import datetime
from services.database.database import Base

class User(Base):
    __tablename__ = "users"
    
    # 1. Better ID: UUID (Universally Unique) instead of String
    id = Column(
        UUID(as_uuid=True),  # Use PostgreSQL-native UUID (optional)
        primary_key=True,
        default=uuid.uuid4,  # Auto-generates UUID
        unique=True,
        index=True
    )
    
    # 2. Email with length limit + stricter constraints
    email = Column(
        String(255),  # Prevents excessively long strings
        unique=True,
        nullable=True,
        index=True  # Faster queries for email-based lookups
    )
    
    # 3. Hashed password (always non-null for authenticated users)
    hashed_password = Column(
        String(255),  # Matches common hash lengths (e.g., bcrypt)
        nullable=True  # Allow null for OAuth/wallet-only users
    )
    
    # 4. Wallet address with validation hints
    wallet_address = Column(
        String(42),  # Ethereum addresses are 42 chars (0x + 40 hex)
        unique=True,
        nullable=True,
        index=True
    )
    
    # 5. Network with constrained choices (optional)
    network = Column(
        String(50),  # e.g., "Ethereum", "Solana", "Polygon"
        nullable=True
    )
    
    # 6. Verification status
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False  # Explicitly non-null
    )
    
    # 7. Timestamps with timezone awareness (if needed)
    created_at = Column(
        DateTime(timezone=True),  # For timezone support
        default=datetime.utcnow,
        nullable=False
    )
    
    last_login = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,  # Auto-updates on login
        nullable=False
    )

    # 8. Composite index for wallet + network (if often queried together)
    __table_args__ = (
        Index('idx_wallet_network', 'wallet_address', 'network'),
    )