"""Password handling utilities.

This module provides functions for hashing and verifying passwords.
"""

from typing import Optional

from passlib.context import CryptContext


# Create a password context for hashing and verification
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to verify against
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    return _pwd_context.verify(plain_password, hashed_password)


def password_meets_requirements(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
) -> tuple[bool, Optional[str]]:
    """Check if a password meets the specified requirements.
    
    Args:
        password: The password to check
        min_length: The minimum length required
        require_uppercase: Whether to require at least one uppercase letter
        require_lowercase: Whether to require at least one lowercase letter
        require_digit: Whether to require at least one digit
        require_special: Whether to require at least one special character
        
    Returns:
        A tuple containing (meets_requirements, error_message)
        If the password meets all requirements, error_message will be None
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    if require_uppercase and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if require_lowercase and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if require_digit and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if require_special and not any(not c.isalnum() for c in password):
        return False, "Password must contain at least one special character"
    
    return True, None