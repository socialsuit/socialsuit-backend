"""Unified authentication service for cross-platform compatibility."""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from eth_account.messages import encode_defunct
from eth_account import Account
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Try to import from shared location first, then fallback to local
try:
    from app.models.user import User, AuthType
    from app.core.config import settings
except ImportError:
    try:
        from services.models.user_model import User, AuthType
        from core.config import settings
    except ImportError:
        # Final fallback for development
        from app.models.user import User, AuthType
        from app.core.config import settings

from app.schemas.auth_schemas import TokenResponse, WalletChallengeResponse


class UnifiedAuthService:
    """Unified authentication service for both Social Suit and Suit Research."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = getattr(settings, 'ALGORITHM', 'HS256')
        self.secret_key = getattr(settings, 'SECRET_KEY', 'your-secret-key')
        self.access_token_expire_minutes = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)
        self.refresh_token_expire_days = getattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS', 7)
    
    # Password utilities
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # JWT utilities
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    
    # Wallet utilities
    def verify_wallet_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        """Verify wallet signature for authentication."""
        try:
            # Create the message hash
            message_hash = encode_defunct(text=message)
            
            # Recover the address from signature
            recovered_address = Account.recover_message(message_hash, signature=signature)
            
            # Compare addresses (case-insensitive)
            return recovered_address.lower() == wallet_address.lower()
        except Exception:
            return False
    
    def generate_wallet_challenge(self, wallet_address: str, network: str = "ethereum") -> WalletChallengeResponse:
        """Generate a challenge message for wallet authentication."""
        nonce = secrets.token_hex(16)
        timestamp = datetime.now(timezone.utc)
        
        message = f"Sign this message to authenticate with your wallet.\n\nWallet: {wallet_address}\nNetwork: {network}\nNonce: {nonce}\nTimestamp: {timestamp.isoformat()}"
        
        expires_at = timestamp + timedelta(minutes=5)  # 5-minute expiry
        
        return WalletChallengeResponse(
            message=message,
            expires_at=expires_at
        )
    
    # User authentication methods
    async def authenticate_user_email(self, email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        return user
    
    async def authenticate_user_wallet(self, wallet_address: str, network: str, db: Session) -> Optional[User]:
        """Authenticate user with wallet address."""
        user = db.query(User).filter(
            User.wallet_address == wallet_address.lower(),
            User.network == network
        ).first()
        
        if user:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            db.commit()
        
        return user
    
    # User registration methods
    async def register_user_email(self, email: str, password: str, full_name: Optional[str], db: Session) -> User:
        """Register a new user with email and password."""
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Create new user
        hashed_password = self.hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            auth_type=AuthType.EMAIL,
            email_verified=True,  # Auto-verify for now
            wallet_verified=False,
            is_verified=True
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("Email already registered")
    
    async def register_user_wallet(self, wallet_address: str, network: str, full_name: Optional[str], db: Session) -> User:
        """Register a new user with wallet."""
        wallet_address = wallet_address.lower()
        
        # Check if wallet already exists
        existing_user = db.query(User).filter(
            User.wallet_address == wallet_address,
            User.network == network
        ).first()
        if existing_user:
            raise ValueError("Wallet already registered")
        
        # Create new user
        user = User(
            wallet_address=wallet_address,
            network=network,
            full_name=full_name,
            auth_type=AuthType.WALLET,
            email_verified=False,
            wallet_verified=True,
            is_verified=True
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("Wallet already registered")
    
    # Account linking methods
    async def link_email_to_user(self, user_id: str, email: str, password: str, db: Session) -> User:
        """Link email/password authentication to existing user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.email:
            raise ValueError("Email already linked to this account")
        
        # Check if email is already used by another user
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered to another account")
        
        # Link email to user
        user.email = email
        user.hashed_password = self.hash_password(password)
        user.email_verified = True
        user.update_auth_type()
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("Email already registered")
    
    async def link_wallet_to_user(self, user_id: str, wallet_address: str, network: str, db: Session) -> User:
        """Link wallet authentication to existing user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.wallet_address:
            raise ValueError("Wallet already linked to this account")
        
        wallet_address = wallet_address.lower()
        
        # Check if wallet is already used by another user
        existing_user = db.query(User).filter(
            User.wallet_address == wallet_address,
            User.network == network
        ).first()
        if existing_user:
            raise ValueError("Wallet already registered to another account")
        
        # Link wallet to user
        user.wallet_address = wallet_address
        user.network = network
        user.wallet_verified = True
        user.update_auth_type()
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError("Wallet already registered")
    
    async def unlink_wallet_from_user(self, user_id: str, wallet_address: str, db: Session) -> User:
        """Unlink wallet from user account."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if not user.wallet_address or user.wallet_address.lower() != wallet_address.lower():
            raise ValueError("Wallet not linked to this account")
        
        if not user.has_email_auth():
            raise ValueError("Cannot unlink wallet: no alternative authentication method")
        
        # Unlink wallet
        user.wallet_address = None
        user.network = None
        user.wallet_verified = False
        user.update_auth_type()
        
        db.commit()
        db.refresh(user)
        return user
    
    # Token management
    async def create_token_pair(self, user: User) -> TokenResponse:
        """Create access and refresh token pair for user."""
        access_token = self.create_access_token(data={"sub": str(user.id)})
        refresh_token = self.create_refresh_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60
        )
    
    async def refresh_access_token(self, refresh_token: str, db: Session) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        return await self.create_token_pair(user)