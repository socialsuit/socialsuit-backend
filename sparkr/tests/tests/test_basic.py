import pytest
from fastapi.testclient import TestClient

from sparkr.app.main import app


@pytest.fixture
def client():
    """Create a test client for the app"""
    return TestClient(app)


def test_read_main(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Sparkr API"}


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_failing_placeholder():
    """A failing test placeholder as requested"""
    # This test will fail as requested
    assert False