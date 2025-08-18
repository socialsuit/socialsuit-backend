"""Unified Authentication Service for Social Suit and Suit Research (Shared Module)."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from eth_account.messages import encode_defunct
from eth_account import Account
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Import from services for Social Suit, but make it configurable for Suit Research
try:
    from services.models.user_model import User, AuthType
    from services.core.config import settings
except ImportError:
    # Fallback for Suit Research project
    try:
        from suit_research.app.models.user import User, AuthType
        from suit_research.app.core.config import settings
    except ImportError:
        raise ImportError("Could not import User model and settings from either project")


class UnifiedAuthService:
    """Unified authentication service supporting email/password and wallet authentication."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.secret_key = secret_key or getattr(settings, 'SECRET_KEY', 'fallback-secret-key')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
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
    
    def verify_wallet_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        """Verify wallet signature for authentication."""
        try:
            # Create the message that was signed
            message_hash = encode_defunct(text=message)
            
            # Recover the address from the signature
            recovered_address = Account.recover_message(message_hash, signature=signature)
            
            # Compare addresses (case-insensitive)
            return recovered_address.lower() == wallet_address.lower()
        except Exception:
            return False
    
    def generate_wallet_challenge(self, wallet_address: str) -> str:
        """Generate a challenge message for wallet authentication."""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        nonce = secrets.token_hex(16)
        return f"Sign this message to authenticate with Social Suit:\nWallet: {wallet_address}\nTimestamp: {timestamp}\nNonce: {nonce}"
    
    def authenticate_user_email(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def authenticate_user_wallet(self, db: Session, wallet_address: str, message: str, signature: str) -> Optional[User]:
        """Authenticate user with wallet signature."""
        if not self.verify_wallet_signature(wallet_address, message, signature):
            return None
        
        user = db.query(User).filter(User.wallet_address == wallet_address.lower()).first()
        return user
    
    def create_token_pair(self, user: User) -> Dict[str, str]:
        """Create access and refresh token pair for user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "wallet_address": user.wallet_address,
            "auth_type": user.auth_type.value if user.auth_type else "email"
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def get_user_from_token(self, db: Session, token: str) -> Optional[User]:
        """Get user from JWT token."""
        payload = self.verify_token(token, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return db.query(User).filter(User.id == user_id).first()


# Global instance
auth_service = UnifiedAuthService()