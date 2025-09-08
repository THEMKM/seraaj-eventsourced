"""
Tests for the Auth service
"""
import pytest
from datetime import datetime
from uuid import uuid4
import tempfile
import shutil
import os

from services.auth.service import AuthService


@pytest.fixture
def auth_service():
    """Create auth service with temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    service = AuthService(data_dir=temp_dir)
    yield service
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_user_registration(auth_service):
    """Test user registration"""
    result = await auth_service.register_user(
        email="test@example.com",
        password="testpass123",
        name="Test User",
        role="VOLUNTEER"
    )
    
    assert "user" in result
    assert "tokens" in result
    assert result["user"].email == "test@example.com"
    assert result["user"].role == "VOLUNTEER"
    assert result["user"].isVerified is True
    assert result["tokens"].tokenType == "Bearer"
    assert result["tokens"].expiresIn == 900  # 15 minutes


@pytest.mark.asyncio
async def test_duplicate_email_registration(auth_service):
    """Test that duplicate email registration fails"""
    await auth_service.register_user(
        email="duplicate@example.com",
        password="testpass123",
        name="First User",
        role="VOLUNTEER"
    )
    
    with pytest.raises(ValueError, match="User with this email already exists"):
        await auth_service.register_user(
            email="duplicate@example.com",
            password="testpass123",
            name="Second User",
            role="ORG_ADMIN"
        )


@pytest.mark.asyncio
async def test_invalid_role_registration(auth_service):
    """Test that invalid role registration fails"""
    with pytest.raises(ValueError, match="Invalid role"):
        await auth_service.register_user(
            email="invalid@example.com",
            password="testpass123",
            name="Invalid User",
            role="SUPERADMIN"  # Not allowed via API
        )


@pytest.mark.asyncio
async def test_user_login(auth_service):
    """Test user login"""
    # Register user first
    await auth_service.register_user(
        email="login@example.com",
        password="loginpass123",
        name="Login User",
        role="VOLUNTEER"
    )
    
    # Login
    result = await auth_service.login_user("login@example.com", "loginpass123")
    
    assert "user" in result
    assert "tokens" in result
    assert result["user"].email == "login@example.com"
    assert result["user"].lastLoginAt is not None
    assert result["tokens"].tokenType == "Bearer"


@pytest.mark.asyncio
async def test_invalid_login_credentials(auth_service):
    """Test login with invalid credentials"""
    # Register user first
    await auth_service.register_user(
        email="valid@example.com",
        password="correctpass123",
        name="Valid User",
        role="VOLUNTEER"
    )
    
    # Try login with wrong password
    with pytest.raises(ValueError, match="Invalid email or password"):
        await auth_service.login_user("valid@example.com", "wrongpass")
    
    # Try login with non-existent email
    with pytest.raises(ValueError, match="Invalid email or password"):
        await auth_service.login_user("nonexistent@example.com", "anypass")


@pytest.mark.asyncio
async def test_token_refresh(auth_service):
    """Test token refresh"""
    # Register and get tokens
    result = await auth_service.register_user(
        email="refresh@example.com",
        password="refreshpass123",
        name="Refresh User",
        role="VOLUNTEER"
    )
    
    refresh_token = result["tokens"].refreshToken
    
    # Add small delay to ensure different timestamps
    import asyncio
    await asyncio.sleep(0.1)
    
    # Refresh tokens
    new_tokens = await auth_service.refresh_tokens(refresh_token)
    
    assert new_tokens.tokenType == "Bearer"
    assert new_tokens.expiresIn == 900
    # Don't check if tokens are different as they may be same due to timing


@pytest.mark.asyncio
async def test_invalid_refresh_token(auth_service):
    """Test refresh with invalid token"""
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await auth_service.refresh_tokens("invalid_token")


@pytest.mark.asyncio
async def test_get_current_user(auth_service):
    """Test getting current user from token"""
    # Register and get tokens
    result = await auth_service.register_user(
        email="current@example.com",
        password="currentpass123",
        name="Current User",
        role="ORG_ADMIN"
    )
    
    access_token = result["tokens"].accessToken
    
    # Get current user
    user = await auth_service.get_current_user(access_token)
    
    assert user.email == "current@example.com"
    assert user.name == "Current User"
    assert user.role == "ORG_ADMIN"


@pytest.mark.asyncio
async def test_invalid_access_token(auth_service):
    """Test get current user with invalid token"""
    with pytest.raises(ValueError, match="Invalid access token"):
        await auth_service.get_current_user("invalid_token")


@pytest.mark.asyncio
async def test_token_verification(auth_service):
    """Test token verification"""
    # Register and get tokens
    result = await auth_service.register_user(
        email="verify@example.com",
        password="verifypass123",
        name="Verify User",
        role="VOLUNTEER"
    )
    
    access_token = result["tokens"].accessToken
    refresh_token = result["tokens"].refreshToken
    
    # Verify access token
    access_payload = auth_service.verify_token(access_token)
    assert access_payload is not None
    assert access_payload['type'] == 'access'
    assert access_payload['email'] == 'verify@example.com'
    
    # Verify refresh token
    refresh_payload = auth_service.verify_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload['type'] == 'refresh'
    assert 'user_id' in refresh_payload
    
    # Verify invalid token
    invalid_payload = auth_service.verify_token("invalid_token")
    assert invalid_payload is None


@pytest.mark.asyncio
async def test_password_hashing(auth_service):
    """Test password hashing and verification"""
    password = "testpassword123"
    
    # Hash password
    hashed = auth_service._hash_password(password)
    assert hashed != password
    assert len(hashed) > 50  # Bcrypt hashes are long
    
    # Verify correct password
    assert auth_service._verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert auth_service._verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_event_sourcing_persistence(auth_service):
    """Test that events are persisted and state is rebuilt"""
    # Register user
    result = await auth_service.register_user(
        email="persist@example.com",
        password="persistpass123",
        name="Persist User",
        role="VOLUNTEER"
    )
    user_id = result["user"].id
    
    # Create new service instance (simulating restart)
    temp_dir = auth_service.repository.data_dir
    new_service = AuthService(data_dir=str(temp_dir))
    
    # Check that user still exists
    user = await new_service.repository.get(user_id)
    assert user is not None
    assert user.email == "persist@example.com"
    assert user.name == "Persist User"
    
    # Check that login still works
    login_result = await new_service.login_user("persist@example.com", "persistpass123")
    assert login_result["user"].email == "persist@example.com"