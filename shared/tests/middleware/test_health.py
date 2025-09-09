"""Tests for the health check endpoints."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from shared.middleware.health import HealthCheckConfig, setup_health_endpoints, HealthStatus


@pytest.fixture
def basic_app():
    """Create a test FastAPI application with basic health check endpoints."""
    app = FastAPI()
    health_config = HealthCheckConfig(
        app_version="1.0.0-test",
        liveness_path="/healthz",
        readiness_path="/readyz",
    )
    setup_health_endpoints(app, health_config)
    return app


@pytest.fixture
def app_with_checks():
    """Create a test FastAPI application with custom health checks."""
    app = FastAPI()
    
    # Define test health checks
    async def always_healthy():
        return True, "Always healthy"
    
    async def always_unhealthy():
        return False, "Always unhealthy"
    
    health_config = HealthCheckConfig(
        app_version="1.0.0-test",
        liveness_path="/healthz",
        readiness_path="/readyz",
        liveness_checks=[always_healthy],
        readiness_checks=[always_healthy, always_unhealthy],
    )
    setup_health_endpoints(app, health_config)
    return app


def test_liveness_endpoint(basic_app):
    """Test the liveness endpoint returns 200 OK."""
    client = TestClient(basic_app)
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0-test"
    assert "timestamp" in data
    assert "checks" in data
    assert len(data["checks"]) == 0  # No checks configured


def test_readiness_endpoint(basic_app):
    """Test the readiness endpoint returns 200 OK."""
    client = TestClient(basic_app)
    response = client.get("/readyz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0-test"
    assert "timestamp" in data
    assert "checks" in data
    assert len(data["checks"]) == 0  # No checks configured


def test_liveness_with_checks(app_with_checks):
    """Test the liveness endpoint with custom checks."""
    client = TestClient(app_with_checks)
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert len(data["checks"]) == 1
    assert data["checks"][0]["status"] == "healthy"
    assert data["checks"][0]["message"] == "Always healthy"


def test_readiness_with_failing_check(app_with_checks):
    """Test the readiness endpoint with a failing check."""
    client = TestClient(app_with_checks)
    response = client.get("/readyz")
    
    # Should return 503 Service Unavailable when any check fails
    assert response.status_code == 503
    data = response.json()
    
    assert data["status"] == "unhealthy"
    assert len(data["checks"]) == 2
    
    # First check should be healthy
    assert data["checks"][0]["status"] == "healthy"
    assert data["checks"][0]["message"] == "Always healthy"
    
    # Second check should be unhealthy
    assert data["checks"][1]["status"] == "unhealthy"
    assert data["checks"][1]["message"] == "Always unhealthy"


def test_custom_paths():
    """Test using custom paths for health check endpoints."""
    app = FastAPI()
    health_config = HealthCheckConfig(
        app_version="1.0.0-test",
        liveness_path="/live",
        readiness_path="/ready",
    )
    setup_health_endpoints(app, health_config)
    client = TestClient(app)
    
    # Test custom liveness path
    response = client.get("/live")
    assert response.status_code == 200
    
    # Test custom readiness path
    response = client.get("/ready")
    assert response.status_code == 200
    
    # Original paths should not exist
    response = client.get("/healthz")
    assert response.status_code == 404
    
    response = client.get("/readyz")
    assert response.status_code == 404