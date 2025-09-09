import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from sparkr.app.core.security import get_password_hash
from sparkr.app.models.models import User


@pytest.fixture
async def test_user(session: AsyncSession):
    """Create a test user for authentication tests"""
    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)
    
    yield test_user
    
    # Cleanup
    await session.delete(test_user)
    await session.commit()


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """Test user registration endpoint"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_existing_user(async_client: AsyncClient, test_user):
    """Test registration with existing email"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "username": "newusername",
            "password": "newpassword"
        }
    )
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, test_user):
    """Test successful login"""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,  # OAuth2 form uses username field for email
            "password": "testpassword"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_user):
    """Test login with wrong password"""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient, test_user):
    """Test get current user endpoint"""
    # First login to get token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Use token to get current user
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username
    assert data["id"] == test_user.id