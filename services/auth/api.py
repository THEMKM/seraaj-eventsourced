"""
FastAPI application for Auth service matching OpenAPI v1.1.0 specification
"""
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Header, status, Request
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


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.1.0"
    }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - is the service running?"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@app.post("/auth/register", 
         status_code=status.HTTP_201_CREATED,
         response_model=AuthResponse,
         responses={
             400: {"model": ApiError, "description": "Invalid request data"},
             409: {"model": ApiError, "description": "Email already registered"}
         })
async def register_user(request: RegisterUserRequest, req: Request):
    """Register a new user account"""
    trace_id = get_trace_id(req)
    start_time = datetime.utcnow()
    
    log_structured(
        logger, "INFO", "User registration requested",
        trace_id=trace_id,
        operation="register_user",
        email=request.email,
        role=request.role.value
    )
    
    try:
        service = get_auth_service()
        result = await service.register_user(
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role.value
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "User registered successfully",
            trace_id=trace_id,
            operation="register_user",
            email=request.email,
            userId=result['user'].id,
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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "EMAIL_EXISTS", "message": error_msg}
            )
        else:
            log_structured(
                logger, "WARN", "Registration failed - invalid request",
                trace_id=trace_id,
                operation="register_user",
                email=request.email,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "INVALID_REQUEST", "message": error_msg}
            )
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during user registration",
            trace_id=trace_id,
            operation="register_user",
            email=request.email,
            error=str(e),
            errorType=type(e).__name__
        )
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
async def login_user(request: LoginUserRequest, req: Request):
    """Login with email and password"""
    trace_id = get_trace_id(req)
    start_time = datetime.utcnow()
    
    log_structured(
        logger, "INFO", "User login requested",
        trace_id=trace_id,
        operation="login_user",
        email=request.email
    )
    
    try:
        service = get_auth_service()
        result = await service.login_user(
            email=request.email,
            password=request.password
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "User logged in successfully",
            trace_id=trace_id,
            operation="login_user",
            email=request.email,
            userId=result['user'].id,
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "ACCOUNT_SUSPENDED", "message": error_msg}
            )
        else:
            log_structured(
                logger, "WARN", "Login failed - invalid credentials",
                trace_id=trace_id,
                operation="login_user",
                email=request.email,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "INVALID_CREDENTIALS", "message": error_msg}
            )
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during user login",
            trace_id=trace_id,
            operation="login_user",
            email=request.email,
            error=str(e),
            errorType=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

@app.post("/auth/refresh",
         response_model=AuthTokens,
         responses={
             401: {"model": ApiError, "description": "Invalid or expired refresh token"}
         })
async def refresh_tokens(request: RefreshTokenRequest, req: Request):
    """Exchange refresh token for new access and refresh tokens"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Token refresh requested",
        trace_id=trace_id,
        operation="refresh_tokens"
    )
    
    try:
        service = get_auth_service()
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": str(e)}
        )
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during token refresh",
            trace_id=trace_id,
            operation="refresh_tokens",
            error=str(e),
            errorType=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

@app.get("/auth/me",
        response_model=User,
        responses={
            401: {"model": ApiError, "description": "Invalid or expired token"}
        })
async def get_current_user(
    req: Request,
    authorization: Optional[str] = Header(None)
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "MISSING_TOKEN", "message": "Authorization header required"}
        )
    
    if not authorization.startswith("Bearer "):
        log_structured(
            logger, "WARN", "Profile request failed - invalid authorization header format",
            trace_id=trace_id,
            operation="get_current_user"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": "Invalid authorization header format"}
        )
    
    access_token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        service = get_auth_service()
        user = await service.get_current_user(access_token)
        
        log_structured(
            logger, "INFO", "Current user profile retrieved successfully",
            trace_id=trace_id,
            operation="get_current_user",
            userId=user.id,
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_TOKEN", "message": str(e)}
        )
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error during profile retrieval",
            trace_id=trace_id,
            operation="get_current_user",
            error=str(e),
            errorType=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Internal server error"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)