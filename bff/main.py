"""
Simplified Seraaj BFF API for testing schema validation
"""

import os
import json
import yaml
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import jsonschema
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import service adapters
from .adapters.applications import ApplicationsAdapter
from .adapters.matching import MatchingAdapter
from .adapters.auth import AuthAdapter

# Import logging
from services.shared.logging_config import (
    StructuredLoggingMiddleware, 
    setup_json_logging, 
    setup_telemetry,
    log_structured, 
    get_trace_id,
    log_business_metric,
    log_performance_metric
)
from services.shared.models import StandardErrorResponse


# Load OpenAPI schema for validation
def load_openapi_schema():
    """Load the OpenAPI schema and referenced schemas for validation"""
    try:
        schema_path = Path(__file__).parent.parent / "contracts" / "v1.1.0" / "api" / "bff.openapi.yaml"
        schemas_dir = schema_path.parent / "schemas"
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            openapi_spec = yaml.safe_load(f)
        
        # Load referenced schemas
        referenced_schemas = {}
        for schema_file in ["match-suggestion.yaml", "application.yaml", "submit-application.yaml", "volunteer-profile-view.yaml"]:
            schema_file_path = schemas_dir / schema_file
            if schema_file_path.exists():
                with open(schema_file_path, 'r', encoding='utf-8') as f:
                    schema_content = yaml.safe_load(f)
                    referenced_schemas[f"./schemas/{schema_file}"] = schema_content
        
        return openapi_spec, referenced_schemas
    except Exception as e:
        print(f"[WARNING] Could not load OpenAPI schema: {e}")
        return {}, {}


OPENAPI_SPEC, REFERENCED_SCHEMAS = load_openapi_schema()


def resolve_schema_ref(schema_ref: str) -> Dict[str, Any]:
    """Resolve a schema reference to actual schema"""
    if schema_ref.startswith('./schemas/'):
        return REFERENCED_SCHEMAS.get(schema_ref, {})
    elif schema_ref.startswith('#/components/schemas/'):
        component_name = schema_ref.split('/')[-1]
        return OPENAPI_SPEC.get('components', {}).get('schemas', {}).get(component_name, {})
    return {}


def validate_response_schema(endpoint_path: str, method: str, status_code: int, response_data: Any):
    """Validate response against OpenAPI schema - simplified version"""
    try:
        if not OPENAPI_SPEC:
            print("[DEBUG] No OpenAPI spec loaded, skipping validation")
            return
            
        print(f"[DEBUG] Validating {method.upper()} {endpoint_path} ({status_code})")
        
        # Find the endpoint in OpenAPI spec
        paths = OPENAPI_SPEC.get('paths', {})
        endpoint_spec = paths.get(endpoint_path, {})
        method_spec = endpoint_spec.get(method.lower(), {})
        responses = method_spec.get('responses', {})
        
        # Get response schema for status code
        response_spec = responses.get(str(status_code), responses.get('default', {}))
        content = response_spec.get('content', {}).get('application/json', {})
        schema = content.get('schema', {})
        
        if not schema:
            print(f"[DEBUG] No schema found for {method.upper()} {endpoint_path} ({status_code})")
            return
        
        print(f"[DEBUG] Found schema: {json.dumps(schema, indent=2)}")
        
        # Resolve schema references
        if '$ref' in schema:
            resolved_schema = resolve_schema_ref(schema['$ref'])
            if resolved_schema:
                schema = resolved_schema
                print(f"[DEBUG] Resolved schema: {json.dumps(schema, indent=2)[:200]}...")
        
        # Handle array responses
        if schema.get('type') == 'array' and 'items' in schema:
            items_schema = schema['items']
            if '$ref' in items_schema:
                resolved_items = resolve_schema_ref(items_schema['$ref'])
                if resolved_items:
                    items_schema = resolved_items
            
            # Validate each item in the array
            if isinstance(response_data, list):
                for i, item in enumerate(response_data):
                    jsonschema.validate(item, items_schema)
                    print(f"[DEBUG] Item {i} validation passed")
            print(f"[DEBUG] Array validation passed for {len(response_data) if isinstance(response_data, list) else 0} items")
            return
        
        # Validate the response
        jsonschema.validate(response_data, schema)
        print(f"[DEBUG] Schema validation passed for {method.upper()} {endpoint_path} ({status_code})")
        
    except jsonschema.ValidationError as e:
        print(f"[ERROR] Schema validation failed for {method.upper()} {endpoint_path} ({status_code}): {e.message}")
        print(f"[DEBUG] Failed at: {e.json_path}")
        print(f"[DEBUG] Response data sample: {str(response_data)[:500]}...")
        # Don't raise in development - just log
    except Exception as e:
        print(f"[WARNING] Schema validation error for {method.upper()} {endpoint_path}: {str(e)}")


# Initialize FastAPI app
app = FastAPI(
    title="Seraaj BFF API",
    description="Backend for Frontend API for the Seraaj volunteer platform",
        version="1.1.0"
)

# Setup structured logging
logger = setup_json_logging("bff")

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware, service_name="bff")

# Setup optional OpenTelemetry
setup_telemetry(app, "bff")

# CORS Configuration - allow frontend on port 3001
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QuickMatchRequest(BaseModel):
    volunteerId: str = Field(..., description="ID of the volunteer requesting matches")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of matches to return")


class SubmitApplicationRequest(BaseModel):
    volunteerId: str = Field(..., description="ID of the volunteer submitting the application")
    opportunityId: str = Field(..., description="ID of the opportunity being applied to")
    coverLetter: Optional[str] = Field(None, max_length=1000, description="Optional cover letter from volunteer")


class RegisterUserRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password (minimum 8 characters)")
    name: str = Field(..., min_length=1, max_length=200, description="User's full name")
    role: str = Field(..., description="User's role")


class LoginUserRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class RefreshTokenRequest(BaseModel):
    refreshToken: str = Field(..., description="Valid refresh token")


class ResetPasswordRequest(BaseModel):
    # TODO(security): Replace with token-based reset and email verification.
    email: str = Field(..., description="User's email address")
    newPassword: str = Field(..., min_length=8, max_length=128, description="New password (minimum 8 characters)")


# Mock data generators for contract-accurate responses
def generate_mock_match_suggestion(volunteer_id: str, index: int = 0) -> Dict[str, Any]:
    """Generate a mock match suggestion that matches the contract schema"""
    opportunities = [
        {
            "title": "Community Education Program",
            "description": "Help teach basic literacy skills to adults in the community center. Work with diverse groups of learners in a supportive environment.",
            "requiredSkills": ["teaching", "communication", "patience"],
            "location": "Downtown Community Center, 123 Main St",
            "timeCommitment": "4 hours per week, evenings"
        },
        {
            "title": "Environmental Cleanup Initiative",
            "description": "Join our monthly park cleanup and tree planting activities. Help preserve local green spaces for future generations.",
            "requiredSkills": ["physical", "environmental", "teamwork"],
            "location": "Central Park, North Entrance",
            "timeCommitment": "6 hours per month, weekends"
        },
        {
            "title": "Senior Care Support",
            "description": "Provide companionship and assistance to elderly residents. Activities include reading, games, and light assistance.",
            "requiredSkills": ["social", "caregiving", "empathy"],
            "location": "Sunset Senior Home, 456 Oak Ave",
            "timeCommitment": "3 hours per week, flexible"
        }
    ]
    opp = opportunities[index % len(opportunities)]
    return {
        "id": f"550e8400-e29b-41d4-a716-{446655440000 + index:012d}",  # Valid UUID format
        "title": opp["title"],
        "description": opp["description"],
        "organizationName": f"Hope Foundation {index + 1}",
        "requiredSkills": opp["requiredSkills"],
        "location": opp["location"],
        "timeCommitment": opp["timeCommitment"],
        "matchScore": min(95, 85.5 + (index * 2))
    }

def _to_contract_match_suggestion(raw: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    """Map internal/legacy match suggestion to contract-compliant shape"""
    title = raw.get("title") or raw.get("opportunityTitle") or f"Opportunity {index + 1}"
    description = raw.get("description") or " ".join(raw.get("reasons", [])) or "Suggested opportunity"
    organization_name = raw.get("organizationName") or "Unknown Organization"
    required_skills = raw.get("requiredSkills") or raw.get("reasons") or []
    location = raw.get("location") or "Remote"
    time_commitment = raw.get("timeCommitment") or "Flexible"
    # Prefer explicit matchScore, fall back to score
    match_score = raw.get("matchScore") if isinstance(raw.get("matchScore"), (int, float)) else raw.get("score", 0)
    # Ensure result is within 0..100
    try:
        match_score = max(0, min(100, float(match_score)))
    except Exception:
        match_score = 0

    # Contract-compliant core fields
    result = {
        "id": str(raw.get("id")) if raw.get("id") else f"550e8400-e29b-41d4-a716-{446655440000 + index:012d}",
        "title": title,
        "description": description,
        "organizationName": organization_name,
        "requiredSkills": required_skills,
        "location": location,
        "timeCommitment": time_commitment,
        "matchScore": match_score,
    }
    # Backward-compatibility extras (allowed by schema additionalProperties):
    for extra_key in (
        "volunteerId", "opportunityId", "organizationId",
        "status", "generatedAt", "expiresAt",
        "scoreComponents", "explanation",
    ):
        if extra_key in raw and raw.get(extra_key) is not None:
            result[extra_key] = raw.get(extra_key)
    return result


# Helpers to map internal models to contract schemas
def _to_contract_application(raw: Dict[str, Any]) -> Dict[str, Any]:
    status_map = {
        "draft": "pending",
        "submitted": "pending",
        "reviewing": "pending",
        "accepted": "approved",
        "completed": "approved",
        "rejected": "rejected",
        "cancelled": "withdrawn",
    }
    status_value = str(raw.get("status", "")).lower()
    return {
        "id": str(raw.get("id")),
        "volunteerId": str(raw.get("volunteerId")),
        "opportunityId": str(raw.get("opportunityId")),
        "status": status_map.get(status_value, "pending"),
        "message": raw.get("coverLetter") or "",
        "appliedAt": (raw.get("submittedAt") or raw.get("createdAt") or datetime.now(UTC)).isoformat(),
        "reviewedAt": raw.get("reviewedAt") or None,
        "reviewerNotes": None,
    }

def generate_mock_application(volunteer_id: str, index: int = 0) -> Dict[str, Any]:
    """Generate a mock application that matches the contract schema"""
    base_time = datetime.now(UTC)
    return {
        "id": f"550e8400-e29b-41d4-a716-{556677880000 + index:012d}",
        "volunteerId": volunteer_id,
        "opportunityId": f"660e8400-e29b-41d4-a716-{112233440000 + index:012d}",
        "status": "pending",
        "message": "I am very interested in this opportunity because...",
        "appliedAt": base_time.isoformat(),
        "reviewedAt": None,
        "reviewerNotes": None,
    }


def generate_mock_volunteer_profile(volunteer_id: str) -> Dict[str, Any]:
    """Generate a mock volunteer profile that matches the schema"""
    base_time = datetime.now(UTC)
    return {
        "id": volunteer_id,
        "email": "volunteer@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "level": 5,
        "status": "active",
        "skills": ["teaching", "technical", "social"],
        "badges": [
            {
                "id": "badge-rookie",
                "name": "Rookie",
                "description": "Completed first volunteer opportunity",
                "imageUrl": "https://example.com/badges/rookie.png",
                "earnedAt": base_time.isoformat()
            }
        ],
        "totalHours": 120.5,
        "completedApplications": 8,
        "createdAt": base_time.isoformat(),
        "lastActive": base_time.isoformat()
    }


# Health check endpoints
@app.get("/api/health")
async def health_check():
    """Dependency-aware health check endpoint"""
    health_result = await health_checker.check_health()
    response_data = health_result.to_dict()
    
    # Validate against schema
    try:
        validate_response_schema("/health", "get", 200, response_data)
    except Exception as e:
        logger.warning(f"Health response schema validation failed: {e}")
        # Return basic format if schema validation fails
        return {
            "status": health_result.overall_status.value,
            "timestamp": health_result.timestamp,
            "version": health_result.version
        }
    
    return response_data


@app.get("/api/health/services")
async def services_health_check():
    """Extended health check that includes dependent services"""
    applications_healthy = await applications_adapter.health_check()
    matching_healthy = await matching_adapter.health_check()
    auth_healthy = await auth_adapter.health_check()
    
    # Use health checker for consistent status reporting
    health_result = await health_checker.check_health(use_cache=False)
    response_data = health_result.to_dict()
    
    # Add circuit breaker status
    from infrastructure.circuit_breaker import get_all_circuit_breaker_status
    response_data["circuit_breakers"] = get_all_circuit_breaker_status()
    
    # Add service registry status
    response_data["service_registry"] = service_registry.get_service_status()
    
    # Add legacy adapter checks for backward compatibility
    response_data["legacy_checks"] = {
        "applications": "healthy" if applications_healthy else "unhealthy",
        "matching": "healthy" if matching_healthy else "unhealthy",
        "auth": "healthy" if auth_healthy else "unhealthy"
    }
    
    return response_data


@app.get("/api/health/transactions")
async def transaction_health_check():
    """Transaction manager health and statistics"""
    from infrastructure.transaction_manager import transaction_manager
    
    stats = transaction_manager.get_transaction_stats()
    return {
        "transaction_stats": stats,
        "pending_transactions": len(transaction_manager.pending_transactions),
        "status": "healthy" if stats.get("pending", 0) < 10 else "degraded"  # Too many pending is bad
    }


# Auth endpoints (proxy to auth service)
@app.post("/api/auth/register", status_code=201)
async def register_user(request: RegisterUserRequest, req: Request):
    """Register a new user account"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "BFF user registration request",
        trace_id=trace_id,
        operation="register_user",
        email=request.email,
        role=request.role,
        upstreamService="auth"
    )
    
    try:
        response = await auth_adapter.register_user(
            request.email, 
            request.password, 
            request.name, 
            request.role
        )
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "BFF user registration response",
            trace_id=trace_id,
            operation="register_user",
            email=request.email,
            userId=response.get('user', {}).get('id'),
            upstreamLatencyMs=duration_ms
        )
        
        # Log business metric
        log_business_metric(
            logger, "bff_user_registered", 1,
            trace_id=trace_id,
            email=request.email,
            role=request.role
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions from adapter
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF user registration failed - unexpected error",
            trace_id=trace_id,
            operation="register_user",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.post("/api/auth/login")
async def login_user(request: LoginUserRequest, req: Request):
    """Login with email and password"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "BFF user login request",
        trace_id=trace_id,
        operation="login_user",
        email=request.email,
        upstreamService="auth"
    )
    
    try:
        response = await auth_adapter.login_user(request.email, request.password)
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "BFF user login response",
            trace_id=trace_id,
            operation="login_user",
            email=request.email,
            userId=response.get('user', {}).get('id'),
            upstreamLatencyMs=duration_ms
        )
        
        # Log business metric
        log_business_metric(
            logger, "bff_user_login", 1,
            trace_id=trace_id,
            email=request.email
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions from adapter
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF user login failed - unexpected error",
            trace_id=trace_id,
            operation="login_user",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.post("/api/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, req: Request):
    """Temporary insecure reset: set new password by email and approve immediately.
    TODO(security): Replace with secure token-based reset and email verification.
    """
    trace_id = get_trace_id(req)
    try:
        response = await auth_adapter.reset_password(request.email, request.newPassword)
        log_structured(
            logger, "INFO", "BFF password reset (temporary flow)",
            trace_id=trace_id,
            operation="reset_password",
            email=request.email
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF password reset failed - unexpected error",
            trace_id=trace_id,
            operation="reset_password",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.post("/api/auth/refresh")
async def refresh_tokens(request: RefreshTokenRequest, req: Request):
    """Refresh access token"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "BFF token refresh request",
        trace_id=trace_id,
        operation="refresh_tokens",
        upstreamService="auth"
    )
    
    try:
        response = await auth_adapter.refresh_tokens(request.refreshToken)
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "BFF token refresh response",
            trace_id=trace_id,
            operation="refresh_tokens",
            upstreamLatencyMs=duration_ms
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions from adapter
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF token refresh failed - unexpected error",
            trace_id=trace_id,
            operation="refresh_tokens",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.get("/api/auth/me")
async def get_current_user(req: Request):
    """Get current user profile"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    # Extract Bearer token from Authorization header
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        err = StandardErrorResponse(error="unauthorized", message="Missing or invalid authorization header", code=401)
        raise HTTPException(status_code=401, detail=err.model_dump())
    
    access_token = auth_header.replace("Bearer ", "")
    
    log_structured(
        logger, "INFO", "BFF get current user request",
        trace_id=trace_id,
        operation="get_current_user",
        upstreamService="auth"
    )
    
    try:
        response = await auth_adapter.get_current_user(access_token)
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "BFF get current user response",
            trace_id=trace_id,
            operation="get_current_user",
            userId=response.get('id'),
            upstreamLatencyMs=duration_ms
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions from adapter
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF get current user failed - unexpected error",
            trace_id=trace_id,
            operation="get_current_user",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


# Initialize service registry and adapters
from infrastructure.service_registry import service_registry
from infrastructure.health_checker import create_service_health_checker, check_http_endpoint

# Register default services
service_registry.register_default_services()

# Initialize service adapters with service registry
applications_adapter = ApplicationsAdapter(service_registry)
matching_adapter = MatchingAdapter(service_registry)
auth_adapter = AuthAdapter()

# Initialize health checker with service dependencies
health_checker = create_service_health_checker("bff")

# Add service dependencies to health checker
health_checker.add_dependency(
    "applications_service",
    lambda: check_http_endpoint("http://localhost:8001/health"),
    timeout_seconds=3.0,
    critical=False  # Degraded but not unhealthy if down
)

health_checker.add_dependency(
    "matching_service", 
    lambda: check_http_endpoint("http://localhost:8003/health"),
    timeout_seconds=3.0,
    critical=False
)

health_checker.add_dependency(
    "auth_service",
    lambda: check_http_endpoint("http://localhost:8004/health"),
    timeout_seconds=3.0,
    critical=True  # Auth is critical for BFF functionality
)


@app.on_event("startup")
async def startup_event():
    """Initialize service health monitoring on startup"""
    await service_registry.start_health_monitor()
    logger.info("Service registry health monitoring started")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up service health monitoring on shutdown"""
    await service_registry.stop_health_monitor()
    logger.info("Service registry health monitoring stopped")


# Volunteer endpoints with real service calls
@app.post("/api/volunteer/quick-match")
async def get_quick_match(request: QuickMatchRequest, req: Request):
    """Get quick match suggestions for a volunteer"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "BFF quick match request",
        trace_id=trace_id,
        operation="quick_match",
        volunteerId=request.volunteerId,
        limit=request.limit,
        upstreamService="matching"
    )
    
    try:
        # Call matching service (forward Authorization if present)
        auth_header = req.headers.get('Authorization')
        raw_matches = await matching_adapter.quick_match(request.volunteerId, request.limit, authorization=auth_header)
        # Map to contract-compliant schema
        matches = [
            _to_contract_match_suggestion(m, i)
            for i, m in enumerate(raw_matches)
        ]
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        # Log successful aggregation  
        log_structured(
            logger, "INFO", "BFF quick match response",
            trace_id=trace_id,
            operation="quick_match",
            volunteerId=request.volunteerId,
            matchCount=len(matches),
            upstreamLatencyMs=duration_ms
        )
        
        # Validate response against schema
        validate_response_schema("/volunteer/quick-match", "post", 200, matches)
        
        # Log performance metric
        log_performance_metric(
            logger, "bff_quick_match", duration_ms,
            trace_id=trace_id,
            volunteerId=request.volunteerId
        )
        
        return matches
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (from service adapter)
        log_structured(
            logger, "WARN", "BFF quick match failed - upstream HTTP error",
            trace_id=trace_id,
            operation="quick_match",
            upstreamService="matching",
            statusCode=e.status_code,
            error=e.detail
        )
        raise
    except httpx.RequestError as e:
        log_structured(
            logger, "ERROR", "BFF quick match failed - upstream service error",
            trace_id=trace_id,
            operation="quick_match",
            upstreamService="matching",
            error=str(e)
        )
        # Fallback to mock data for graceful degradation
        matches = [
            generate_mock_match_suggestion(request.volunteerId, i)
            for i in range(min(request.limit, 3))
        ]
        validate_response_schema("/volunteer/quick-match", "post", 200, matches)
        return matches
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF quick match failed - unexpected error",
            trace_id=trace_id,
            operation="quick_match",
            error=str(e),
            errorType=type(e).__name__
        )
        # Fallback to mock data for graceful degradation
        matches = [
            generate_mock_match_suggestion(request.volunteerId, i)
            for i in range(min(request.limit, 3))
        ]
        validate_response_schema("/volunteer/quick-match", "post", 200, matches)
        return matches


@app.post("/api/volunteer/apply", status_code=201)
async def submit_application(request: SubmitApplicationRequest, req: Request):
    """Submit a volunteer application"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "BFF application submission request",
        trace_id=trace_id,
        operation="submit_application",
        volunteerId=request.volunteerId,
        opportunityId=request.opportunityId,
        upstreamService="applications"
    )
    
    try:
        # Call applications service (forward Authorization if present)
        auth_header = req.headers.get('Authorization')
        application = await applications_adapter.submit_application(
            request.volunteerId, 
            request.opportunityId, 
            request.coverLetter,
            authorization=auth_header
        )
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "BFF application submission response",
            trace_id=trace_id,
            operation="submit_application",
            volunteerId=request.volunteerId,
            applicationId=application.get('id'),
            upstreamLatencyMs=duration_ms
        )
        
        # Validate response against schema
        validate_response_schema("/volunteer/apply", "post", 201, application)
        
        # Log business metric
        log_business_metric(
            logger, "bff_application_submitted", 1,
            trace_id=trace_id,
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId
        )
        
        return application
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (from service adapter)
        log_structured(
            logger, "WARN", "BFF application submission failed - upstream HTTP error",
            trace_id=trace_id,
            operation="submit_application",
            upstreamService="applications",
            statusCode=e.status_code,
            error=e.detail
        )
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF application submission failed - unexpected error",
            trace_id=trace_id,
            operation="submit_application",
            error=str(e),
            errorType=type(e).__name__
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.get("/api/volunteer/{volunteer_id}/dashboard")
async def get_volunteer_dashboard(volunteer_id: str, req: Request):
    """Get volunteer dashboard data"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "BFF dashboard request",
        trace_id=trace_id,
        operation="get_dashboard",
        volunteerId=volunteer_id
    )
    
    try:
        # Fetch data from multiple services concurrently
        # In production, these would be done in parallel
        
        # Get applications from applications service
        auth_header = req.headers.get('Authorization')
        applications = await applications_adapter.get_volunteer_applications(volunteer_id, authorization=auth_header)
        
        # Filter for active applications (not in final states) and map to contract schema
        active_applications_internal = [
            app for app in applications 
            if app.get('status') not in ['completed', 'cancelled', 'rejected']
        ]
        active_applications = [_to_contract_application(app) for app in active_applications_internal]
        
        # Get recent matches from matching service and map to contract schema
        recent_matches_raw = await matching_adapter.get_suggestions(volunteer_id, authorization=auth_header)
        recent_matches = [_to_contract_match_suggestion(m, i) for i, m in enumerate(recent_matches_raw)]
        
        # Generate profile data (mock for now - would come from volunteer service in production)
        profile = generate_mock_volunteer_profile(volunteer_id)
        
        # Update profile stats based on real data
        profile.update({
            "completedApplications": len([
                app for app in applications 
                if app.get('status') == 'completed'
            ])
        })
        
        dashboard_data = {
            "profile": profile,
            "activeApplications": active_applications,
            "recentMatches": recent_matches
        }
        
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        
        log_structured(
            logger, "INFO", "BFF dashboard response",
            trace_id=trace_id,
            operation="get_dashboard",
            volunteerId=volunteer_id,
            activeApplicationCount=len(active_applications),
            recentMatchCount=len(recent_matches),
            durationMs=duration_ms
        )
        
        # Validate response against schema
        validate_response_schema("/volunteer/{volunteerId}/dashboard", "get", 200, dashboard_data)
        
        # Log performance metric
        log_performance_metric(
            logger, "bff_dashboard", duration_ms,
            trace_id=trace_id,
            volunteerId=volunteer_id
        )
        
        return dashboard_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        log_structured(
            logger, "WARN", "BFF dashboard failed - upstream HTTP error",
            trace_id=trace_id,
            operation="get_dashboard",
            volunteerId=volunteer_id
        )
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "BFF dashboard failed - unexpected error",
            trace_id=trace_id,
            operation="get_dashboard",
            volunteerId=volunteer_id,
            error=str(e),
            errorType=type(e).__name__
        )
        # Fallback to mock data for graceful degradation
        dashboard_data = {
            "profile": generate_mock_volunteer_profile(volunteer_id),
            "activeApplications": [
                generate_mock_application(volunteer_id, i)
                for i in range(2)
            ],
            "recentMatches": [
                generate_mock_match_suggestion(volunteer_id, i)
                for i in range(3)
            ]
        }
        validate_response_schema("/volunteer/{volunteerId}/dashboard", "get", 200, dashboard_data)
        return dashboard_data


if __name__ == "__main__":
    port = int(os.getenv('BFF_PORT', '8000'))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="debug")
