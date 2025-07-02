import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime, timezone
from services.database.database import Base


class User(Base):
    tablename = "users"   # ✅ Always double underscore

    # ✅ Primary key: UUID, PostgreSQL-native
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )

    # ✅ Email
    email = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    # ✅ Hashed Password — nullable=True for wallet-only logins
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
        nullable=True
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )

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

    table_args = (
        Index('idx_wallet_network', 'wallet_address', 'network'),
    )

    def repr(self):
        return f"<User(id={self.id}, email={self.email}, wallet={self.wallet_address})>"