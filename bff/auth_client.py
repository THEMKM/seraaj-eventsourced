"""Auth service client for BFF
Generated from contracts/v1.1.0/api/auth.openapi.yaml
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

class AuthClient:
    """Client for communicating with the Auth service"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)
    
    async def register_user(self, email: str, password: str, name: str, role: str) -> Dict[str, Any]:
        """Register a new user"""
        response = await self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": role
        })
        response.raise_for_status()
        return response.json()
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email and password"""
        response = await self.client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        return response.json()
    
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        response = await self.client.post("/auth/refresh", json={
            "refreshToken": refresh_token
        })
        response.raise_for_status()
        return response.json()
    
    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user profile"""
        response = await self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global auth client instance
auth_client = AuthClient()