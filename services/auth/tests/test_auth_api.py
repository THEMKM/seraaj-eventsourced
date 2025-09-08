"""
Tests for the Auth API endpoints
"""
import pytest
from fastapi.testclient import TestClient
import tempfile
import shutil
import json
import uuid

from services.auth.api import app, get_auth_service
from services.auth.service import AuthService


@pytest.fixture
def test_client():
    """Create test client with temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    
    def override_auth_service():
        return AuthService(data_dir=temp_dir)
    
    app.dependency_overrides[get_auth_service] = override_auth_service
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()
    shutil.rmtree(temp_dir)


def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth"
    assert data["version"] == "1.1.0"


def test_register_user(test_client):
    """Test user registration endpoint"""
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"test-{unique_id}@example.com",
        "password": "testpass123",
        "name": "Test User",
        "role": "VOLUNTEER"
    }
    
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["email"] == f"test-{unique_id}@example.com"
    assert data["user"]["name"] == "Test User"
    assert data["user"]["role"] == "VOLUNTEER"
    assert data["user"]["isVerified"] is True
    assert data["tokens"]["tokenType"] == "Bearer"
    assert "accessToken" in data["tokens"]
    assert "refreshToken" in data["tokens"]


def test_register_duplicate_email(test_client):
    """Test registering with duplicate email"""
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"duplicate-{unique_id}@example.com",
        "password": "testpass123",
        "name": "First User",
        "role": "VOLUNTEER"
    }
    
    # First registration
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Second registration with same email
    user_data["name"] = "Second User"
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 409
    
    data = response.json()
    assert data["detail"]["error"] == "EMAIL_EXISTS"


def test_register_invalid_role(test_client):
    """Test registering with invalid role"""
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"invalid-{unique_id}@example.com",
        "password": "testpass123",
        "name": "Invalid User",
        "role": "SUPERADMIN"  # Not allowed via API
    }
    
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    
    data = response.json()
    assert data["detail"]["error"] == "INVALID_REQUEST"


def test_register_validation_errors(test_client):
    """Test registration with validation errors"""
    # Missing required fields
    response = test_client.post("/auth/register", json={})
    assert response.status_code == 422
    
    # Short password - this should definitely fail validation
    user_data = {
        "email": "short@example.com",
        "password": "short",  # Less than 8 chars
        "name": "Test User",
        "role": "VOLUNTEER"
    }
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 422


def test_login_user(test_client):
    """Test user login endpoint"""
    # Register user first
    user_data = {
        "email": "login@example.com",
        "password": "loginpass123",
        "name": "Login User",
        "role": "VOLUNTEER"
    }
    test_client.post("/auth/register", json=user_data)
    
    # Login
    login_data = {
        "email": "login@example.com",
        "password": "loginpass123"
    }
    
    response = test_client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["lastLoginAt"] is not None
    assert data["tokens"]["tokenType"] == "Bearer"


def test_login_invalid_credentials(test_client):
    """Test login with invalid credentials"""
    # Register user first
    user_data = {
        "email": "valid@example.com",
        "password": "correctpass123",
        "name": "Valid User",
        "role": "VOLUNTEER"
    }
    test_client.post("/auth/register", json=user_data)
    
    # Login with wrong password
    login_data = {
        "email": "valid@example.com",
        "password": "wrongpass"
    }
    
    response = test_client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    
    data = response.json()
    assert data["detail"]["error"] == "INVALID_CREDENTIALS"


def test_refresh_tokens(test_client):
    """Test token refresh endpoint"""
    # Register user first
    user_data = {
        "email": "refresh@example.com",
        "password": "refreshpass123",
        "name": "Refresh User",
        "role": "VOLUNTEER"
    }
    
    register_response = test_client.post("/auth/register", json=user_data)
    register_data = register_response.json()
    refresh_token = register_data["tokens"]["refreshToken"]
    
    # Refresh tokens
    refresh_data = {
        "refreshToken": refresh_token
    }
    
    response = test_client.post("/auth/refresh", json=refresh_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["tokenType"] == "Bearer"
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["accessToken"] != register_data["tokens"]["accessToken"]


def test_refresh_invalid_token(test_client):
    """Test refresh with invalid token"""
    refresh_data = {
        "refreshToken": "invalid_token"
    }
    
    response = test_client.post("/auth/refresh", json=refresh_data)
    assert response.status_code == 401
    
    data = response.json()
    assert data["detail"]["error"] == "INVALID_TOKEN"


def test_get_current_user(test_client):
    """Test get current user endpoint"""
    # Register user first
    user_data = {
        "email": "current@example.com",
        "password": "currentpass123",
        "name": "Current User",
        "role": "ORG_ADMIN"
    }
    
    register_response = test_client.post("/auth/register", json=user_data)
    register_data = register_response.json()
    access_token = register_data["tokens"]["accessToken"]
    
    # Get current user
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = test_client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "current@example.com"
    assert data["name"] == "Current User"
    assert data["role"] == "ORG_ADMIN"


def test_get_current_user_missing_auth(test_client):
    """Test get current user without authorization header"""
    response = test_client.get("/auth/me")
    assert response.status_code == 401
    
    data = response.json()
    assert data["detail"]["error"] == "MISSING_TOKEN"


def test_get_current_user_invalid_auth_format(test_client):
    """Test get current user with invalid auth header format"""
    headers = {
        "Authorization": "InvalidFormat token123"
    }
    
    response = test_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    
    data = response.json()
    assert data["detail"]["error"] == "INVALID_TOKEN"


def test_get_current_user_invalid_token(test_client):
    """Test get current user with invalid token"""
    headers = {
        "Authorization": "Bearer invalid_token"
    }
    
    response = test_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    
    data = response.json()
    assert data["detail"]["error"] == "INVALID_TOKEN"


def test_complete_auth_flow(test_client):
    """Test complete authentication flow"""
    # 1. Register
    user_data = {
        "email": "flow@example.com",
        "password": "flowpass123",
        "name": "Flow User",
        "role": "VOLUNTEER"
    }
    
    register_response = test_client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201
    
    register_data = register_response.json()
    access_token = register_data["tokens"]["accessToken"]
    refresh_token = register_data["tokens"]["refreshToken"]
    
    # 2. Get current user
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = test_client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    
    # 3. Login
    login_data = {
        "email": "flow@example.com",
        "password": "flowpass123"
    }
    login_response = test_client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    # 4. Refresh tokens
    refresh_data = {"refreshToken": refresh_token}
    refresh_response = test_client.post("/auth/refresh", json=refresh_data)
    assert refresh_response.status_code == 200
    
    # 5. Use new access token
    new_access_token = refresh_response.json()["accessToken"]
    new_headers = {"Authorization": f"Bearer {new_access_token}"}
    final_me_response = test_client.get("/auth/me", headers=new_headers)
    assert final_me_response.status_code == 200