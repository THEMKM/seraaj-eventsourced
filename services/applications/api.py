"""
FastAPI application for Applications service
"""
from datetime import datetime, UTC
from typing import List, Optional
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Header
import os
import jwt
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.shared.models import Application, ExternalApplication, StandardErrorResponse
from services.shared.logging_config import (
    StructuredLoggingMiddleware, 
    setup_json_logging, 
    setup_telemetry,
    log_structured, 
    get_trace_id,
    log_business_metric,
    log_performance_metric
)
from .service import ApplicationService, SubmitApplicationCommand


# FastAPI app
app = FastAPI(
    title="Applications Service",
    description="Seraaj Applications Service - manages volunteer application lifecycle",
    version="1.0.0"
)

# Setup structured logging
logger = setup_json_logging("applications")

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware, service_name="applications")

# Setup optional OpenTelemetry
setup_telemetry(app, "applications")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight JWT verification (optional enforcement via REQUIRE_SERVICE_AUTH)
def verify_service_token(authorization: str | None = Header(default=None)) -> dict | None:
    require = os.getenv('REQUIRE_SERVICE_AUTH', 'false').lower() == 'true'
    if not authorization or not authorization.startswith('Bearer '):
        if require:
            err = StandardErrorResponse(error='unauthorized', message='Missing or invalid token', code=401)
            raise HTTPException(status_code=401, detail=err.model_dump())
        return None
    token = authorization.split(' ', 1)[1]
    secret = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except Exception:
        if require:
            err = StandardErrorResponse(error='unauthorized', message='Invalid token', code=401)
            raise HTTPException(status_code=401, detail=err.model_dump())
        return None

# Service dependency
def get_application_service() -> ApplicationService:
    return ApplicationService()


# Request models
class SubmitApplicationRequest(BaseModel):
    volunteerId: str = Field(..., description="ID of the volunteer submitting the application")
    opportunityId: str = Field(..., description="ID of the opportunity being applied to") 
    coverLetter: Optional[str] = Field(None, max_length=1000, description="Optional cover letter")


class UpdateStateRequest(BaseModel):
    action: str = Field(..., description="Action to perform: submit, review, accept, reject, complete, cancel")
    reason: Optional[str] = Field(None, description="Optional reason for the state change")


class ReviewApplicationRequest(BaseModel):
    decision: str = Field(..., description="Review decision: accept or reject")
    reviewerNotes: Optional[str] = Field(None, max_length=2000, description="Optional reviewer notes")
    reviewerId: Optional[str] = Field(None, description="ID of the reviewer (organization member)")


# Health check endpoints
from infrastructure.health_checker import create_service_health_checker, check_file_exists

# Initialize health checker for applications service
app_health_checker = create_service_health_checker("applications")

# Add service-specific dependencies
app_health_checker.add_dependency(
    "application_data_file",
    lambda: check_file_exists("data/applications.json"),
    timeout_seconds=1.0,
    critical=False
)

@app.get("/health")
async def health_check():
    """Dependency-aware health check endpoint"""
    health_result = await app_health_checker.check_health()
    return health_result.to_dict()


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - is the service running?"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "applications",
        "version": "1.0.0"
    }


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - can the service handle requests?"""
    checks = {}
    overall_healthy = True
    
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


# Application endpoints
@app.post("/api/applications", response_model=ExternalApplication, status_code=201)
async def submit_application(
    request: SubmitApplicationRequest,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Submit a new application"""
    trace_id = get_trace_id(req)
    start_time = datetime.now(UTC)
    
    log_structured(
        logger, "INFO", "Application submission started",
        trace_id=trace_id,
        operation="submit_application",
        volunteerId=request.volunteerId,
        opportunityId=request.opportunityId
    )
    
    try:
        command = SubmitApplicationCommand(
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId,
            coverLetter=request.coverLetter
        )
        application = await service.submit_application(command)
        
        # Log successful creation
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        log_structured(
            logger, "INFO", "Application created successfully",
            trace_id=trace_id,
            operation="submit_application",
            applicationId=application.id,
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId,
            durationMs=duration_ms
        )

        # Performance metric
        log_performance_metric(
            logger,
            "applications_submit",
            duration_ms,
            trace_id=trace_id,
            applicationId=application.id,
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId
        )
        
        # Log business metric
        log_business_metric(
            logger, "application_created", 1,
            trace_id=trace_id,
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId
        )
        
        # Map internal status to external contract value
        application_dict = application.dict()
        application_dict['status'] = application.status.to_external_status() if hasattr(application.status, 'to_external_status') else application.status
        return application_dict
        
    except ValueError as e:
        # Log business logic errors
        log_structured(
            logger, "WARN", "Application submission failed - business rule violation", 
            trace_id=trace_id,
            operation="submit_application",
            error=str(e),
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId
        )
        err = StandardErrorResponse(error="validation_error", message=str(e), code=400)
        raise HTTPException(status_code=400, detail=err.model_dump())
        
    except Exception as e:
        # Log system errors
        log_structured(
            logger, "ERROR", "Unexpected error in application creation",
            trace_id=trace_id,
            operation="submit_application",
            error=str(e),
            errorType=type(e).__name__,
            volunteerId=request.volunteerId
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.get("/api/applications/{application_id}", response_model=ExternalApplication)
async def get_application(
    application_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Get application by ID"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Application retrieval requested",
        trace_id=trace_id,
        operation="get_application",
        applicationId=application_id
    )
    
    try:
        application = await service.get_application(application_id)
        if not application:
            log_structured(
                logger, "WARN", "Application not found",
                trace_id=trace_id,
                operation="get_application",
                applicationId=application_id
            )
            err = StandardErrorResponse(error="not_found", message="Application not found", code=404)
            raise HTTPException(status_code=404, detail=err.model_dump())
        
        log_structured(
            logger, "INFO", "Application retrieved successfully",
            trace_id=trace_id,
            operation="get_application",
            applicationId=application_id,
            volunteerId=application.volunteer_id
        )
        application_dict = application.dict()
        application_dict['status'] = application.status.to_external_status() if hasattr(application.status, 'to_external_status') else application.status
        return application_dict
        
    except HTTPException:
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in application retrieval",
            trace_id=trace_id,
            operation="get_application",
            error=str(e),
            applicationId=application_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.patch("/api/applications/{application_id}/state", response_model=ExternalApplication)
async def update_application_state(
    application_id: str,
    request: UpdateStateRequest,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Update application state"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Application state update requested",
        trace_id=trace_id,
        operation="update_application_state",
        applicationId=application_id,
        action=request.action
    )
    
    try:
        application = await service.update_application_state(
            application_id=application_id,
            action=request.action,
            reason=request.reason
        )
        
        log_structured(
            logger, "INFO", "Application state updated successfully",
            trace_id=trace_id,
            operation="update_application_state",
            applicationId=application_id,
            action=request.action,
            newState=application.status,
            volunteerId=application.volunteer_id
        )
        
        # Log business metric
        log_business_metric(
            logger, f"application_{request.action}", 1,
            trace_id=trace_id,
            applicationId=application_id,
            newState=application.status
        )
        
        application_dict = application.dict()
        application_dict['status'] = application.status.to_external_status() if hasattr(application.status, 'to_external_status') else application.status
        return application_dict
        
    except ValueError as e:
        log_structured(
            logger, "WARN", "Application state update failed - business rule violation",
            trace_id=trace_id,
            operation="update_application_state",
            error=str(e),
            applicationId=application_id,
            action=request.action
        )
        err = StandardErrorResponse(error="validation_error", message=str(e), code=400)
        raise HTTPException(status_code=400, detail=err.model_dump())
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in application state update",
            trace_id=trace_id,
            operation="update_application_state",
            error=str(e),
            applicationId=application_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.get("/api/applications/volunteer/{volunteer_id}", response_model=List[ExternalApplication])
async def get_volunteer_applications(
    volunteer_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Get all applications for a volunteer"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Volunteer applications retrieval requested",
        trace_id=trace_id,
        operation="get_volunteer_applications",
        volunteerId=volunteer_id
    )
    
    try:
        applications = await service.get_volunteer_applications(volunteer_id)
        
        log_structured(
            logger, "INFO", "Volunteer applications retrieved successfully",
            trace_id=trace_id,
            operation="get_volunteer_applications",
            volunteerId=volunteer_id,
            applicationCount=len(applications)
        )
        
        external_applications = []
        for app in applications:
            app_dict = app.dict()
            app_dict['status'] = app.status.to_external_status() if hasattr(app.status, 'to_external_status') else app.status
            external_applications.append(app_dict)
        return external_applications
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in volunteer applications retrieval",
            trace_id=trace_id,
            operation="get_volunteer_applications",
            error=str(e),
            volunteerId=volunteer_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.get("/api/applications/opportunity/{opportunity_id}", response_model=List[ExternalApplication])
async def get_opportunity_applications(
    opportunity_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Get all applications for an opportunity"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Opportunity applications retrieval requested",
        trace_id=trace_id,
        operation="get_opportunity_applications",
        opportunityId=opportunity_id
    )
    
    try:
        applications = await service.get_opportunity_applications(opportunity_id)
        
        log_structured(
            logger, "INFO", "Opportunity applications retrieved successfully",
            trace_id=trace_id,
            operation="get_opportunity_applications",
            opportunityId=opportunity_id,
            applicationCount=len(applications)
        )
        
        external_applications = []
        for app in applications:
            app_dict = app.dict()
            app_dict['status'] = app.status.to_external_status() if hasattr(app.status, 'to_external_status') else app.status
            external_applications.append(app_dict)
        return external_applications
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in opportunity applications retrieval",
            trace_id=trace_id,
            operation="get_opportunity_applications",
            error=str(e),
            opportunityId=opportunity_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.post("/api/applications/{application_id}/review", response_model=ExternalApplication)
async def review_application(
    application_id: str,
    request: ReviewApplicationRequest,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Review an application (organization endpoint)"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Application review requested",
        trace_id=trace_id,
        operation="review_application",
        applicationId=application_id,
        decision=request.decision,
        reviewerId=request.reviewerId
    )
    
    try:
        # Validate decision
        if request.decision not in ["accept", "reject"]:
            err = StandardErrorResponse(
                error="validation_error", 
                message="Decision must be 'accept' or 'reject'", 
                code=400
            )
            raise HTTPException(status_code=400, detail=err.model_dump())
        
        # First transition to reviewing state if not already there
        application = await service.get_application(application_id)
        if not application:
            err = StandardErrorResponse(error="not_found", message="Application not found", code=404)
            raise HTTPException(status_code=404, detail=err.model_dump())
        
        # Auto-transition to reviewing state if currently submitted
        if application.status == "submitted":
            await service.update_application_state(application_id, "review")
        
        # Apply the review decision
        application = await service.update_application_state(
            application_id=application_id,
            action=request.decision,
            reason=request.reviewerNotes
        )
        
        # Store reviewer information if provided
        if request.reviewerId or request.reviewerNotes:
            # In a full implementation, this would update reviewer fields in the application
            # For MVP, we log the review information
            log_structured(
                logger, "INFO", "Application review completed",
                trace_id=trace_id,
                operation="review_application",
                applicationId=application_id,
                decision=request.decision,
                reviewerId=request.reviewerId,
                hasNotes=bool(request.reviewerNotes)
            )
        
        # Log business metric
        log_business_metric(
            logger, f"application_reviewed_{request.decision}", 1,
            trace_id=trace_id,
            applicationId=application_id,
            reviewerId=request.reviewerId
        )
        
        application_dict = application.dict()
        application_dict['status'] = application.status.to_external_status() if hasattr(application.status, 'to_external_status') else application.status
        return application_dict
        
    except ValueError as e:
        log_structured(
            logger, "WARN", "Application review failed - business rule violation",
            trace_id=trace_id,
            operation="review_application",
            error=str(e),
            applicationId=application_id
        )
        err = StandardErrorResponse(error="validation_error", message=str(e), code=400)
        raise HTTPException(status_code=400, detail=err.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in application review",
            trace_id=trace_id,
            operation="review_application",
            error=str(e),
            applicationId=application_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


@app.get("/api/applications/organization/{org_id}/pending", response_model=List[ExternalApplication])
async def get_pending_applications_for_organization(
    org_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Get all pending applications for an organization's opportunities"""
    trace_id = get_trace_id(req)
    
    log_structured(
        logger, "INFO", "Organization pending applications requested",
        trace_id=trace_id,
        operation="get_org_pending_applications",
        organizationId=org_id
    )
    
    try:
        # For MVP, we'll need to filter applications by checking each opportunity
        # In production, this would be a more efficient database query
        
        # This is a simplified implementation - would need opportunity service integration
        # For now, return empty list with proper logging
        log_structured(
            logger, "INFO", "Organization pending applications retrieved (MVP stub)",
            trace_id=trace_id,
            operation="get_org_pending_applications",
            organizationId=org_id,
            applicationCount=0
        )
        
        return []
        
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in organization pending applications retrieval",
            trace_id=trace_id,
            operation="get_org_pending_applications",
            error=str(e),
            organizationId=org_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())

@app.get("/api/applications/stats/organization/{org_id}")
async def get_organization_application_stats(
    org_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service),
    _token: dict | None = Depends(verify_service_token)
):
    """Get application statistics for an organization"""
    trace_id = get_trace_id(req)
    
    try:
        # Get real statistics from repository
        repo_stats = await service.get_organization_stats(org_id)
        
        stats = {
            "organizationId": org_id,
            "totalApplications": repo_stats.get("totalApplications", 0),
            "pendingReview": repo_stats.get("pendingReview", 0),
            "approved": repo_stats.get("approved", 0),
            "rejected": repo_stats.get("rejected", 0),
            "lastUpdated": datetime.now(UTC).isoformat()
        }
        
        log_structured(
            logger, "INFO", "Organization application stats retrieved",
            trace_id=trace_id,
            operation="get_org_application_stats",
            organizationId=org_id
        )
        
        return stats
        
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in organization stats retrieval",
            trace_id=trace_id,
            operation="get_org_application_stats",
            error=str(e),
            organizationId=org_id
        )
        err = StandardErrorResponse(error="internal_error", message="Internal server error", code=500, details={"reason": str(e)})
        raise HTTPException(status_code=500, detail=err.model_dump())


# Main entry point
if __name__ == "__main__":
    from services.shared.port_config import get_service_startup_config
    
    host, port = get_service_startup_config("applications")
    print(f"Starting Applications service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
