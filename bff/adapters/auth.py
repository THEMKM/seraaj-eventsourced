"""Auth service adapter for BFF"""
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException


class AuthAdapter:
    def __init__(self, auth_service_url: str = "http://127.0.0.1:8004"):
        import os
        self.auth_service_url = auth_service_url.rstrip('/')
        default_timeout = float(os.getenv('AUTH_HTTP_TIMEOUT', os.getenv('BFF_HTTP_TIMEOUT', '30.0')))
        self.timeout = httpx.Timeout(default_timeout)

    async def health_check(self) -> bool:
        """Check if auth service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.auth_service_url}/health")
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
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/register",
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/login",
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/refresh",
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.auth_service_url}/auth/me",
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/reset-password",
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
