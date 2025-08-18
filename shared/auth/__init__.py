"""Shared authentication module for Social Suit and Suit Research."""

from .unified_auth_service import UnifiedAuthService, auth_service
from .dependencies import get_current_user, get_current_user_optional
from .middleware import AuthMiddleware

__all__ = [
    "UnifiedAuthService",
    "auth_service",
    "get_current_user",
    "get_current_user_optional",
    "AuthMiddleware"
]