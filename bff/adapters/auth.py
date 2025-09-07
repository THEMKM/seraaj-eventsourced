"""Auth service adapter for BFF"""
import httpx
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from services.shared.models import StandardErrorResponse

from infrastructure.service_registry import ServiceRegistry, ServiceUnavailableError
from infrastructure.circuit_breaker import get_service_circuit_breaker, CircuitBreakerOpenException
from services.shared.service_auth import get_service_auth_header

logger = logging.getLogger(__name__)


class AuthAdapter:
    def __init__(self, service_registry: ServiceRegistry = None):
        import os
        self.service_registry = service_registry
        self.service_name = "auth"
        self.circuit_breaker = get_service_circuit_breaker(self.service_name) if service_registry else None
        # Fallback URL for backward compatibility
        self.fallback_url = "http://localhost:8004"
        default_timeout = float(os.getenv('AUTH_HTTP_TIMEOUT', os.getenv('BFF_HTTP_TIMEOUT', '30.0')))
        self.timeout = httpx.Timeout(default_timeout)
    
    async def _get_service_url(self) -> str:
        """Get the service URL from service discovery with fallback"""
        if self.service_registry:
            try:
                return await self.service_registry.get_service_url(self.service_name)
            except ServiceUnavailableError as e:
                logger.warning(f"Service discovery failed for {self.service_name}, using fallback: {e}")
        return self.fallback_url

    def _get_service_headers(self) -> Dict[str, str]:
        """Get headers for service-to-service requests"""
        headers = {}
        service_auth = get_service_auth_header("bff", "auth")
        if service_auth:
            headers["Authorization"] = service_auth
        return headers

    async def health_check(self) -> bool:
        """Check if auth service is healthy"""
        try:
            base_url = await self._get_service_url()
            headers = self._get_service_headers()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/health", headers=headers)
                return response.status_code == 200
        except Exception:
            return False

    async def register_user(self, email: str, password: str, name: str, role: str) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Map role to the expected enum value
            role_mapping = {
                "volunteer": "VOLUNTEER",
                "org_admin": "ORG_ADMIN", 
                "superadmin": "SUPERADMIN"
            }
            mapped_role = role_mapping.get(role.lower(), "VOLUNTEER")
            
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/auth/register",
                    json={
                        "email": email,
                        "password": password,
                        "name": name,
                        "role": mapped_role
                    }
                )
                
                if response.status_code == 201:
                    return response.json()
                elif response.status_code == 409:
                    raise HTTPException(status_code=409, detail="Email already registered")
                elif response.status_code == 400:
                    raise HTTPException(status_code=400, detail="Invalid request data")
                else:
                    print(f"[DEBUG] Auth service registration failed with status {response.status_code}: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=f"Registration failed: {response.text}")
                    
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/auth/login",
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Login failed")
                    
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/auth/refresh",
                    json={
                        "refreshToken": refresh_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Token refresh failed")
                    
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user profile"""
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{base_url}/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Failed to get user profile")
                    
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    async def reset_password(self, email: str, new_password: str) -> Dict[str, Any]:
        """Temporary: reset password without verification (MVP only)
        TODO(security): Replace with token-based reset and email verification.
        """
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/auth/reset-password",
                    json={"email": email, "newPassword": new_password}
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    raise HTTPException(status_code=400, detail="Invalid reset request")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Reset password failed")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    async def get_profile(self, authorization: Optional[str]) -> Dict[str, Any]:
        """Get the authenticated user's volunteer profile from Auth service."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{base_url}/auth/profile",
                    headers={"Authorization": authorization}
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Failed to get profile")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")

    async def update_profile(self, authorization: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the authenticated user's volunteer profile on Auth service."""
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{base_url}/auth/profile",
                    headers={"Authorization": authorization},
                    json=data
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Failed to update profile")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Auth service unavailable: {str(e)}")
