"""Tests for the correlation ID middleware."""

import uuid
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pytest

from shared.middleware.correlation import CorrelationIDMiddleware, get_correlation_id


@pytest.fixture
def app():
    """Create a test FastAPI application with correlation ID middleware."""
    app = FastAPI()
    app.add_middleware(CorrelationIDMiddleware)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        correlation_id = get_correlation_id(request)
        return {"correlation_id": correlation_id}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


def test_correlation_id_generated(client):
    """Test that a correlation ID is generated if not provided."""
    response = client.get("/test")
    assert response.status_code == 200
    
    # Check response header
    assert "X-Correlation-ID" in response.headers
    header_correlation_id = response.headers["X-Correlation-ID"]
    
    # Check response body
    assert "correlation_id" in response.json()
    body_correlation_id = response.json()["correlation_id"]
    
    # Verify correlation IDs match
    assert header_correlation_id == body_correlation_id
    
    # Verify it's a valid UUID
    try:
        uuid.UUID(header_correlation_id)
        assert True
    except ValueError:
        assert False, "Correlation ID is not a valid UUID"


def test_correlation_id_passed_through(client):
    """Test that a provided correlation ID is passed through."""
    test_correlation_id = str(uuid.uuid4())
    response = client.get("/test", headers={"X-Correlation-ID": test_correlation_id})
    assert response.status_code == 200
    
    # Check response header
    assert "X-Correlation-ID" in response.headers
    header_correlation_id = response.headers["X-Correlation-ID"]
    
    # Check response body
    assert "correlation_id" in response.json()
    body_correlation_id = response.json()["correlation_id"]
    
    # Verify correlation IDs match the one we provided
    assert header_correlation_id == test_correlation_id
    assert body_correlation_id == test_correlation_id


def test_custom_header_name():
    """Test using a custom header name for correlation ID."""
    app = FastAPI()
    app.add_middleware(CorrelationIDMiddleware, header_name="X-Request-ID")
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        correlation_id = get_correlation_id(request)
        return {"correlation_id": correlation_id}
    
    client = TestClient(app)
    
    # Test with custom header
    test_correlation_id = str(uuid.uuid4())
    response = client.get("/test", headers={"X-Request-ID": test_correlation_id})
    assert response.status_code == 200
    
    # Check response header uses custom name
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == test_correlation_id
    
    # Check response body
    assert response.json()["correlation_id"] == test_correlation_id


def test_disable_response_header():
    """Test disabling the correlation ID in response headers."""
    app = FastAPI()
    app.add_middleware(CorrelationIDMiddleware, include_in_response=False)
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        correlation_id = get_correlation_id(request)
        return {"correlation_id": correlation_id}
    
    client = TestClient(app)
    
    # Test with header disabled in response
    response = client.get("/test")
    assert response.status_code == 200
    
    # Check correlation ID is not in response header
    assert "X-Correlation-ID" not in response.headers
    
    # But it should still be available in the request state
    assert "correlation_id" in response.json()
    assert response.json()["correlation_id"] is not None