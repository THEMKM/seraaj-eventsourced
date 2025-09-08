"""
FastAPI application for Auth service matching OpenAPI v1.1.0 specification
"""
from datetime import datetime, UTC
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Header, status, Request, Depends
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
from pydantic import BaseModel, Field
from services.shared.models import StandardErrorResponse
from services.shared.logging_config import (
    StructuredLoggingMiddleware, 
    setup_json_logging, 
    setup_telemetry,
    log_structured, 
    get_trace_id,
    log_business_metric,
    log_performance_metric
)
from .service import AuthService
from .profile_models import VolunteerProfile as AuthVolunteerProfile, UpdateVolunteerProfileRequest
from .profile_repository import ProfileRepository

# Temporary reset password request without verification (MVP only)
# TODO(security): Replace with token-based reset flow with email verification.
class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    newPassword: str = Field(..., min_length=8, max_length=128, description="New password (minimum 8 characters)")

app = FastAPI(
    title="Seraaj Authentication API",
    description="Authentication and user management endpoints for the Seraaj platform",
    version="1.1.0"
)

# Setup structured logging
logger = setup_json_logging("auth")

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware, service_name="auth")

# Setup optional OpenTelemetry
setup_telemetry(app, "auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_auth_service() -> AuthService:
    return AuthService()

def get_profile_repository() -> ProfileRepository:
    return ProfileRepository()


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.1.0"
    }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - is the service running?"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "auth",
        "version": "1.1.0"
    }


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - can the service handle requests?"""
    checks = {}
    overall_healthy = True
    
    # Check database connectivity (when implemented)
    try:
        # Future: await repository.health_check()
        checks["database"] = {"status": "healthy", "latencyMs": 5}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check Redis connectivity (when event bus is active)
    try:
        # Future: await event_bus.ping()
        checks["eventBus"] = {"status": "healthy", "latencyMs": 2}
    except Exception as e:
        checks["eventBus"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks
    }


@app.get("/auth/profile", response_model=AuthVolunteerProfile,
         responses={401: {"model": ApiError, "description": "Invalid or missing token"}})
async def get_profile(
    req: Request,
    authorization: str | None = Header(None),
    service: AuthService = Depends(get_auth_service),
    repo: ProfileRepository = Depends(get_profile_repository)
):
    """Return the authenticated user's volunteer profile. Creates a default if absent."""
    if not authorization or not authorization.startswith("Bearer "):
        err = StandardErrorResponse(error="MISSING_TOKEN", message="Authorization header required", code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())

    access_token = authorization[7:]
    user = await service.get_current_user(access_token)

    # Ensure a profile exists; create default if needed
    profile = repo.get_by_user_id(user.id)
    if not profile:
        profile = repo.upsert_for_user(user.id, base_name=user.name, base_email=user.email)
    return profile


@app.put("/auth/profile", response_model=AuthVolunteerProfile,
         responses={401: {"model": ApiError, "description": "Invalid or missing token"}})
async def update_profile(
    request: UpdateVolunteerProfileRequest,
    req: Request,
    authorization: str | None = Header(None),
    service: AuthService = Depends(get_auth_service),
    repo: ProfileRepository = Depends(get_profile_repository)
):
    """Update fields on the authenticated user's volunteer profile and persist them."""
    if not authorization or not authorization.startswith("Bearer "):
        err = StandardErrorResponse(error="MISSING_TOKEN", message="Authorization header required", code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())

    access_token = authorization[7:]
    user = await service.get_current_user(access_token)
    profile = repo.upsert_for_user(user.id, base_name=user.name, base_email=user.email, update=request)
    return profile

@app.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, req: Request, service: AuthService = Depends(get_auth_service)):
    """Temporary insecure reset: set new password by email and approve immediately.
    TODO(security): Replace with secure token-based reset and email verification.
    """
    trace_id = get_trace_id(req)
    try:
        result = await service.reset_password(request.email, request.newPassword)
        log_structured(
            logger, "INFO", "Password reset (temporary flow)",
            trace_id=trace_id,
            operation="reset_password",
            email=request.email,
            userId=result.get("userId")
        )
        return {"status": "ok"}
    except ValueError as e:
        log_structured(
            logger, "WARN", "Password reset failed",
            trace_id=trace_id,
            operation="reset_password",
            email=request.email,
            error=str(e)
        )
        err = StandardErrorResponse(error="INVALID_REQUEST", message=str(e), code=status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.model_dump())
    except Exception as e:
        log_structured(
            logger, "ERROR", "Password reset unexpected error",
            trace_id=trace_id,
            operation="reset_password",
            email=request.email,
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="INTERNAL_ERROR", message="Internal server error", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.model_dump())

@app.post("/auth/register", 
         status_code=status.HTTP_201_CREATED,
         response_model=AuthResponse,
         responses={
             400: {"model": ApiError, "description": "Invalid request data"},
             409: {"model": ApiError, "description": "Email already registered"}
         })
async def register_user(request: RegisterUserRequest, req: Request, service: AuthService = Depends(get_auth_service)):
    """Register a new user account"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "User registration requested",
        trace_id=trace_id,
        operation="register_user",
        email=request.email,
        role=request.role.value
    )
    
    try:
        result = await service.register_user(
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role.value
        )
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "User registered successfully",
            trace_id=trace_id,
            operation="register_user",
            email=request.email,
            userId=str(result['user'].id),
            role=request.role.value,
            durationMs=duration_ms
        )
        
        # Log business metric
        log_business_metric(
            logger, "user_registered", 1,
            trace_id=trace_id,
            email=request.email,
            role=request.role.value
        )
        
        return AuthResponse(
            user=result['user'],
            tokens=result['tokens']
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            log_structured(
                logger, "WARN", "Registration failed - email already exists",
                trace_id=trace_id,
                operation="register_user",
                email=request.email,
                error=error_msg
            )
            err = StandardErrorResponse(error="EMAIL_EXISTS", message=error_msg, code=status.HTTP_409_CONFLICT)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err.model_dump())
        else:
            log_structured(
                logger, "WARN", "Registration failed - invalid request",
                trace_id=trace_id,
                operation="register_user",
                email=request.email,
                error=error_msg
            )
            err = StandardErrorResponse(error="INVALID_REQUEST", message=error_msg, code=status.HTTP_400_BAD_REQUEST)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.model_dump())
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during user registration",
            trace_id=trace_id,
            operation="register_user",
            email=request.email,
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="INTERNAL_ERROR", message="Internal server error", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.model_dump())

@app.post("/auth/login",
         response_model=AuthResponse,
         responses={
             401: {"model": ApiError, "description": "Invalid credentials"},
             403: {"model": ApiError, "description": "Account not verified or suspended"}
         })
async def login_user(request: LoginUserRequest, req: Request, service: AuthService = Depends(get_auth_service)):
    """Login with email and password"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "User login requested",
        trace_id=trace_id,
        operation="login_user",
        email=request.email
    )
    
    try:
        result = await service.login_user(
            email=request.email,
            password=request.password
        )
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "User logged in successfully",
            trace_id=trace_id,
            operation="login_user",
            email=request.email,
            userId=str(result['user'].id),
            role=result['user'].role,
            durationMs=duration_ms
        )
        
        # Log business metric
        log_business_metric(
            logger, "user_login", 1,
            trace_id=trace_id,
            email=request.email,
            role=result['user'].role
        )
        
        return AuthResponse(
            user=result['user'],
            tokens=result['tokens']
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not verified" in error_msg or "deactivated" in error_msg:
            log_structured(
                logger, "WARN", "Login failed - account suspended",
                trace_id=trace_id,
                operation="login_user",
                email=request.email,
                error=error_msg
            )
            err = StandardErrorResponse(error="ACCOUNT_SUSPENDED", message=error_msg, code=status.HTTP_403_FORBIDDEN)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err.model_dump())
        else:
            log_structured(
                logger, "WARN", "Login failed - invalid credentials",
                trace_id=trace_id,
                operation="login_user",
                email=request.email,
                error=error_msg
            )
        err = StandardErrorResponse(error="INVALID_CREDENTIALS", message=error_msg, code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during user login",
            trace_id=trace_id,
            operation="login_user",
            email=request.email,
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="INTERNAL_ERROR", message="Internal server error", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.model_dump())

@app.post("/auth/refresh",
         response_model=AuthTokens,
         responses={
             401: {"model": ApiError, "description": "Invalid or expired refresh token"}
         })
async def refresh_tokens(request: RefreshTokenRequest, req: Request, service: AuthService = Depends(get_auth_service)):
    """Exchange refresh token for new access and refresh tokens"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Token refresh requested",
        trace_id=trace_id,
        operation="refresh_tokens"
    )
    
    try:
        tokens = await service.refresh_tokens(request.refreshToken)
        
        log_structured(
            logger, "INFO", "Tokens refreshed successfully",
            trace_id=trace_id,
            operation="refresh_tokens"
        )
        
        # Log business metric
        log_business_metric(
            logger, "token_refresh", 1,
            trace_id=trace_id
        )
        
        return tokens
        
    except ValueError as e:
        log_structured(
            logger, "WARN", "Token refresh failed - invalid token",
            trace_id=trace_id,
            operation="refresh_tokens",
            error=str(e)
        )
        err = StandardErrorResponse(error="INVALID_TOKEN", message=str(e), code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during token refresh",
            trace_id=trace_id,
            operation="refresh_tokens",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="INTERNAL_ERROR", message="Internal server error", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.model_dump())

@app.get("/auth/me",
        response_model=User,
        responses={
            401: {"model": ApiError, "description": "Invalid or expired token"}
        })
async def get_current_user(
    req: Request,
    authorization: Optional[str] = Header(None),
    service: AuthService = Depends(get_auth_service)
):
    """Retrieve the authenticated user's profile information"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Current user profile requested",
        trace_id=trace_id,
        operation="get_current_user"
    )
    
    if not authorization:
        log_structured(
            logger, "WARN", "Profile request failed - missing authorization header",
            trace_id=trace_id,
            operation="get_current_user"
        )
        err = StandardErrorResponse(error="MISSING_TOKEN", message="Authorization header required", code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())
    
    if not authorization.startswith("Bearer "):
        log_structured(
            logger, "WARN", "Profile request failed - invalid authorization header format",
            trace_id=trace_id,
            operation="get_current_user"
        )
        err = StandardErrorResponse(error="INVALID_TOKEN", message="Invalid authorization header format", code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())
    
    access_token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        user = await service.get_current_user(access_token)
        
        log_structured(
            logger, "INFO", "Current user profile retrieved successfully",
            trace_id=trace_id,
            operation="get_current_user",
            userId=str(user.id),
            email=user.email,
            role=user.role
        )
        
        return user
        
    except ValueError as e:
        log_structured(
            logger, "WARN", "Profile request failed - invalid token",
            trace_id=trace_id,
            operation="get_current_user",
            error=str(e)
        )
        err = StandardErrorResponse(error="INVALID_TOKEN", message=str(e), code=status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.model_dump())
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during profile retrieval",
            trace_id=trace_id,
            operation="get_current_user",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="INTERNAL_ERROR", message="Internal server error", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err.model_dump())

if __name__ == "__main__":
    from services.shared.port_config import get_service_startup_config
    
    host, port = get_service_startup_config("auth")
    print(f"Starting Auth service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
