"""
Authentication service implementing JWT-based authentication
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

import bcrypt
import jwt
from jwt import InvalidTokenError

from services.shared.auth_models import User, UserRole, AuthTokens
from .repository import UserRepository


class AuthService:
    """Authentication service with JWT token management"""
    
    def __init__(self, data_dir: str = "data"):
        self.repository = UserRepository(data_dir)
        # JWT configuration matching manifest
        self.jwt_secret = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.access_token_expire = timedelta(minutes=15)
        self.refresh_token_expire = timedelta(days=7)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _generate_tokens(self, user: User) -> AuthTokens:
        """Generate access and refresh tokens for user"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value if hasattr(user.role, 'value') else user.role,
            'exp': now + self.access_token_expire,
            'iat': now,
            'type': 'access',
            'jti': str(uuid4())
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'exp': now + self.refresh_token_expire,
            'iat': now,
            'type': 'refresh',
            'jti': str(uuid4())
        }
        
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return AuthTokens(
            accessToken=access_token,
            refreshToken=refresh_token,
            tokenType='Bearer',
            expiresIn=int(self.access_token_expire.total_seconds())
        )
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except InvalidTokenError:
            return None
    
    async def register_user(self, email: str, password: str, name: str, role: str) -> Dict:
        """Register a new user"""
        # Validate role - only allow VOLUNTEER and ORG_ADMIN via API
        valid_roles = ['VOLUNTEER', 'ORG_ADMIN']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        
        # Check if user already exists
        existing_user = await self.repository.find_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = self._hash_password(password)
        
        # Create user data
        now = datetime.utcnow()
        user_data = {
            'id': str(uuid4()),
            'email': email,
            'name': name,
            'role': role,
            'hashedPassword': hashed_password,
            'isVerified': True,  # Auto-verify for now
            'createdAt': now,
            'updatedAt': now,
            'lastLoginAt': None,
            'profileImageUrl': None
        }
        
        # Save user
        user = await self.repository.create(user_data)
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        return {
            'user': user,
            'tokens': tokens
        }
    
    async def login_user(self, email: str, password: str) -> Dict:
        """Login user with email and password"""
        # Find user
        user = await self.repository.find_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Get internal user data for password verification
        user_data = self.repository.get_internal_data(user.id)
        if not user_data:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not self._verify_password(password, user_data['hashedPassword']):
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user_data.get('isActive', True):
            raise ValueError("Account is deactivated")
        
        # Check if user is verified
        if not user.isVerified:
            raise ValueError("Account not verified")
        
        # Record login
        await self.repository.record_login(user.id)
        
        # Get updated user
        user = await self.repository.get(user.id)
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        return {
            'user': user,
            'tokens': tokens
        }
    
    async def refresh_tokens(self, refresh_token: str) -> AuthTokens:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = self.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            raise ValueError("Invalid refresh token")
        
        # Get user
        user = await self.repository.get(payload['user_id'])
        if not user:
            raise ValueError("User not found")
        
        # Check if user is active
        user_data = self.repository.get_internal_data(user.id)
        if not user_data or not user_data.get('isActive', True):
            raise ValueError("User not found or inactive")
        
        # Generate new tokens
        return self._generate_tokens(user)
    
    async def get_current_user(self, access_token: str) -> User:
        """Get current user from access token"""
        # Verify access token
        payload = self.verify_token(access_token)
        if not payload or payload.get('type') != 'access':
            raise ValueError("Invalid access token")
        
        # Get user
        user = await self.repository.get(payload['user_id'])
        if not user:
            raise ValueError("User not found")
        
        # Check if user is active
        user_data = self.repository.get_internal_data(user.id)
        if not user_data or not user_data.get('isActive', True):
            raise ValueError("User not found or inactive")
        
        return user