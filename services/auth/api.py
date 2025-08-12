"""
FastAPI application for Auth service matching OpenAPI v1.1.0 specification
"""
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware

from services.shared.auth_models import (
    RegisterUserRequest,
    LoginUserRequest, 
    RefreshTokenRequest,
    AuthResponse,
    AuthTokens,
    ApiError,
    User,
    UserRole
)
from .service import AuthService

app = FastAPI(
    title="Seraaj Authentication API",
    description="Authentication and user management endpoints for the Seraaj platform",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_auth_service() -> AuthService:
    return AuthService()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0"
    }

@app.post("/auth/register", 
         status_code=status.HTTP_201_CREATED,
         response_model=AuthResponse,
         responses={
             400: {"model": ApiError, "description": "Invalid request data"},
             409: {"model": ApiError, "description": "Email already registered"}
         })
async def register_user(request: RegisterUserRequest):
    """Register a new user account"""
    try:
        service = get_auth_service()
        result = await service.register_user(
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role.value
        )
        
        return AuthResponse(
            user=result['user'],
            tokens=result['tokens']
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "EMAIL_EXISTS", "message": error_msg}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "INVALID_REQUEST", "message": error_msg}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

@app.post("/auth/login",
         response_model=AuthResponse,
         responses={
             401: {"model": ApiError, "description": "Invalid credentials"},
             403: {"model": ApiError, "description": "Account not verified or suspended"}
         })
async def login_user(request: LoginUserRequest):
    """Login with email and password"""
    try:
        service = get_auth_service()
        result = await service.login_user(
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            user=result['user'],
            tokens=result['tokens']
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not verified" in error_msg or "deactivated" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCOUNT_SUSPENDED", "message": error_msg}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "INVALID_CREDENTIALS", "message": error_msg}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

@app.post("/auth/refresh",
         response_model=AuthTokens,
         responses={
             401: {"model": ApiError, "description": "Invalid or expired refresh token"}
         })
async def refresh_tokens(request: RefreshTokenRequest):
    """Exchange refresh token for new access and refresh tokens"""
    try:
        service = get_auth_service()
        tokens = await service.refresh_tokens(request.refreshToken)
        return tokens
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

@app.get("/auth/me",
        response_model=User,
        responses={
            401: {"model": ApiError, "description": "Invalid or expired token"}
        })
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Retrieve the authenticated user's profile information"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "MISSING_TOKEN", "message": "Authorization header required"}
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": "Invalid authorization header format"}
        )
    
    access_token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        service = get_auth_service()
        user = await service.get_current_user(access_token)
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)