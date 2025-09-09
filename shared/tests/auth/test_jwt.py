"""Tests for JWT authentication utilities."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from jose import JWTError

from shared.auth.jwt import (
    TokenPayload,
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_auth_dependency,
    get_current_user,
    get_token_payload,
    oauth2_scheme,
    require_admin,
    require_user,
    validate_token,
)


@pytest.fixture
def secret_key():
    """Fixture for a test secret key."""
    return "test_secret_key"


def test_create_access_token(secret_key):
    """Test creating an access token."""
    # Test with default parameters
    token = create_access_token("test_user", secret_key)
    assert token is not None
    assert isinstance(token, str)
    
    # Test with custom expiration
    expires_delta = timedelta(minutes=30)
    token = create_access_token("test_user", secret_key, expires_delta=expires_delta)
    assert token is not None
    
    # Test with additional claims
    additional_claims = {"role": "admin", "permissions": ["read", "write"]}
    token = create_access_token(
        "test_user", secret_key, additional_claims=additional_claims
    )
    assert token is not None


def test_decode_token(secret_key):
    """Test decoding a token."""
    # Create a token
    token = create_access_token("test_user", secret_key)
    
    # Decode the token
    payload = decode_token(token, secret_key)
    
    # Check payload contents
    assert payload["sub"] == "test_user"
    assert "exp" in payload
    assert "iat" in payload
    assert payload["scope"] == "access"
    
    # Test with additional claims
    additional_claims = {"role": "admin", "permissions": ["read", "write"]}
    token = create_access_token(
        "test_user", secret_key, additional_claims=additional_claims
    )
    payload = decode_token(token, secret_key)
    assert payload["additional_claims"]["role"] == "admin"
    assert "read" in payload["additional_claims"]["permissions"]


def test_create_refresh_token(secret_key):
    """Test creating a refresh token."""
    token = create_refresh_token("test_user", secret_key)
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token contents
    payload = decode_token(token, secret_key)
    assert payload["sub"] == "test_user"
    assert payload["scope"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload


def test_token_with_standardized_claims(secret_key):
    """Test creating a token with standardized claims."""
    audience = "test-audience"
    issuer = "test-issuer"
    scopes = ["user", "admin"]
    
    token = create_access_token(
        "test_user",
        secret_key,
        audience=audience,
        issuer=issuer,
        scopes=scopes
    )

    payload = decode_token(
        token, secret_key, audience=audience, issuer=issuer
    )
    assert payload["sub"] == "test_user"
    assert payload["aud"] == audience
    assert payload["iss"] == issuer
    assert set(payload["scopes"]) == set(scopes)


def test_validate_token_valid(secret_key):
    """Test validating a valid token."""
    token = create_access_token("test_user", secret_key, scopes=["user"])
    result = validate_token(token, secret_key)
    assert isinstance(result, TokenPayload)
    assert result.sub == "test_user"


def test_validate_token_expired(secret_key):
    """Test validating an expired token."""
    # Create an expired token
    with patch("shared.auth.jwt.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(minutes=30)
        token = create_access_token(
            "test_user",
            secret_key,
            expires_delta=timedelta(minutes=15)
        )
    
    result = validate_token(token, secret_key)
    assert isinstance(result, TokenValidationError)
    assert result.code == "invalid_token"
    assert "Invalid token" in result.detail


def test_validate_token_with_scopes(secret_key):
    """Test validating a token with required scopes."""
    # Create token with user scope
    token = create_access_token("test_user", secret_key, scopes=["user"])
    
    # Token has 'user' scope, so this should pass
    result = validate_token(token, secret_key, required_scopes=["user"])
    assert isinstance(result, TokenPayload)

    # Token doesn't have 'admin' scope, so this should fail
    result = validate_token(token, secret_key, required_scopes=["admin"])
    assert isinstance(result, TokenValidationError)
    assert result.code == "insufficient_scope"


@pytest.fixture
def test_app():
    """Fixture for a FastAPI test app with protected routes."""
    app = FastAPI()

    @app.get("/public")
    def public_route():
        return {"message": "Public route"}

    @app.get("/protected", dependencies=[Depends(require_user)])
    def protected_route():
        return {"message": "Protected route"}

    @app.get("/admin", dependencies=[Depends(require_admin)])
    def admin_route():
        return {"message": "Admin route"}

    @app.get("/user-info")
    async def user_info(user: TokenPayload = Depends(get_auth_dependency())):
        return {"user_id": user.sub, "scopes": user.scopes}

    return app


@pytest.fixture
def client(test_app):
    """Fixture for a TestClient."""
    return TestClient(test_app)


def test_fastapi_public_route(client):
    """Test accessing a public route."""
    response = client.get("/public")
    assert response.status_code == 200
    assert response.json() == {"message": "Public route"}


@pytest.mark.parametrize(
    "endpoint,token_factory,expected_status",
    [
        ("/protected", None, 401),  # No token
        ("/protected", "create_access_token_with_user_scope", 200),  # Valid token with user scope
        ("/protected", "create_expired_token", 401),  # Expired token
        ("/admin", "create_access_token_with_user_scope", 403),  # User token for admin route
        ("/admin", "create_access_token_with_admin_scope", 200),  # Admin token for admin route
    ],
)
def test_protected_routes(client, secret_key, endpoint, token_factory, expected_status):
    """Test accessing protected routes with different tokens."""
    headers = {}
    
    if token_factory:
        if token_factory == "create_access_token_with_user_scope":
            token = create_access_token("test_user", secret_key, scopes=["user"])
        elif token_factory == "create_access_token_with_admin_scope":
            token = create_access_token("test_user", secret_key, scopes=["admin", "user"])
        elif token_factory == "create_expired_token":
            with patch("shared.auth.jwt.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(minutes=30)
                token = create_access_token(
                    "test_user", secret_key, expires_delta=timedelta(minutes=15)
                )
        headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(endpoint, headers=headers)
    assert response.status_code == expected_status


def test_user_info_endpoint(client, secret_key):
    """Test an endpoint that uses the token payload."""
    token = create_access_token("test_user", secret_key, scopes=["user"])
    response = client.get(
        "/user-info", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    assert "user" in data["scopes"]


def test_get_token_payload(secret_key):
    """Test getting token payload as a Pydantic model."""
    # Create a token
    token = create_access_token("test_user", secret_key)
    
    # Get the payload
    payload = get_token_payload(token, secret_key)
    
    # Check payload contents
    assert payload.sub == "test_user"
    assert payload.scope == "access"
    assert isinstance(payload.exp, datetime)
    assert isinstance(payload.iat, datetime)
    assert payload.additional_claims is None
    
    # Test with additional claims
    additional_claims = {"role": "admin", "permissions": ["read", "write"]}
    token = create_access_token(
        "test_user", secret_key, additional_claims=additional_claims
    )
    payload = get_token_payload(token, secret_key)
    
    assert payload.additional_claims == additional_claims


def test_invalid_token(secret_key):
    """Test decoding an invalid token."""
    # Test with an invalid token
    with pytest.raises(JWTError):
        decode_token("invalid_token", secret_key)
    
    # Test with a valid token but wrong secret key
    token = create_access_token("test_user", secret_key)
    with pytest.raises(JWTError):
        decode_token(token, "wrong_secret_key")