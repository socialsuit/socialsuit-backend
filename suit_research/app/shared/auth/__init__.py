"""Shared authentication module for Suit Research."""

from .unified_auth_service import UnifiedAuthService
from .dependencies import (
    get_current_user,
    get_current_user_optional,
    require_email_auth,
    require_wallet_auth,
    require_verified_email,
    require_verified_wallet,
    require_admin,
    require_analyst_or_admin
)

# Create a singleton instance of the auth service
auth_service = UnifiedAuthService()

__all__ = [
    "UnifiedAuthService",
    "auth_service",
    "get_current_user",
    "get_current_user_optional",
    "require_email_auth",
    "require_wallet_auth",
    "require_verified_email",
    "require_verified_wallet",
    "require_admin",
    "require_analyst_or_admin"
]