"""Authentication utilities for shared projects.

This module provides common authentication functionality including JWT handling,
password hashing and verification, and user authentication flows.
"""

# Import key components to make them available when importing the auth module
from shared.auth.jwt import create_access_token, decode_token, get_token_payload
from shared.auth.password import hash_password, verify_password