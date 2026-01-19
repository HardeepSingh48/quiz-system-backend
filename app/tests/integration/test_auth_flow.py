"""Integration tests for authentication flow"""

import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_register_login_refresh_logout_flow(client: AsyncClient):
    """Test complete authentication flow"""
    
    # 1. Register user
    register_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test123456",
        "role": "user"
    }
    
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/register", json=register_data)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == register_data["email"]
    assert user_data["username"] == register_data["username"]
    
    # 2. Login
    login_data = {
        "email": "test@example.com",
        "password": "Test123456"
    }
    
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # 3. Access protected endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get(f"{settings.API_V1_PREFIX}/auth/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == register_data["email"]
    
    # 4. Refresh token
    refresh_data = {"refresh_token": refresh_token}
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/refresh", json=refresh_data)
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["access_token"] != access_token  # New token
    assert new_tokens["refresh_token"] != refresh_token  # Rotated token
    
    # 5. Old refresh token should not work (rotation)
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/refresh", json=refresh_data)
    assert response.status_code in [400, 401]  # Should fail
    
    # 6. New access token should work
    new_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    response = await client.get(f"{settings.API_V1_PREFIX}/auth/me", headers=new_headers)
    assert response.status_code == 200
    
    # 7. Logout
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/logout", headers=new_headers)
    assert response.status_code == 204
    
    # 8. After logout, tokens should not work
    response = await client.get(f"{settings.API_V1_PREFIX}/auth/me", headers=new_headers)
    assert response.status_code in [401, 404]  # Unauthorized


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123"
    }
    
    response = await client.post(f"{settings.API_V1_PREFIX}/auth/login", json=login_data)
    assert response.status_code == 401
