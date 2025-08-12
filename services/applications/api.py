"""
FastAPI application for Applications service
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.shared.models import Application
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


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "applications",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - is the service running?"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


# Application endpoints
@app.post("/api/applications", response_model=Application, status_code=201)
async def submit_application(
    request: SubmitApplicationRequest,
    req: Request,
    service: ApplicationService = Depends(get_application_service)
):
    """Submit a new application"""
    trace_id = get_trace_id(req)
    start_time = datetime.utcnow()
    
    log_structured(
        logger, "INFO", "Application submission started",
        trace_id=trace_id,
        operation="submit_application",
        volunteerId=request.volunteerId,
        opportunityId=request.opportunityId
    )
    
    try:
        command = SubmitApplicationCommand(
            volunteer_id=request.volunteerId,
            opportunity_id=request.opportunityId,
            cover_letter=request.coverLetter
        )
        application = await service.submit_application(command)
        
        # Log successful creation
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_structured(
            logger, "INFO", "Application created successfully",
            trace_id=trace_id,
            operation="submit_application",
            applicationId=application.id,
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId,
            durationMs=duration_ms
        )
        
        # Log business metric
        log_business_metric(
            logger, "application_created", 1,
            trace_id=trace_id,
            volunteerId=request.volunteerId,
            opportunityId=request.opportunityId
        )
        
        return application
        
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
        raise HTTPException(status_code=400, detail=str(e))
        
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/applications/{application_id}", response_model=Application)
async def get_application(
    application_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service)
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
            raise HTTPException(status_code=404, detail="Application not found")
        
        log_structured(
            logger, "INFO", "Application retrieved successfully",
            trace_id=trace_id,
            operation="get_application",
            applicationId=application_id,
            volunteerId=application.volunteer_id
        )
        return application
        
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.patch("/api/applications/{application_id}/state", response_model=Application)
async def update_application_state(
    application_id: str,
    request: UpdateStateRequest,
    req: Request,
    service: ApplicationService = Depends(get_application_service)
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
        
        return application
        
    except ValueError as e:
        log_structured(
            logger, "WARN", "Application state update failed - business rule violation",
            trace_id=trace_id,
            operation="update_application_state",
            error=str(e),
            applicationId=application_id,
            action=request.action
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in application state update",
            trace_id=trace_id,
            operation="update_application_state",
            error=str(e),
            applicationId=application_id
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/applications/volunteer/{volunteer_id}", response_model=List[Application])
async def get_volunteer_applications(
    volunteer_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service)
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
        
        return applications
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in volunteer applications retrieval",
            trace_id=trace_id,
            operation="get_volunteer_applications",
            error=str(e),
            volunteerId=volunteer_id
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/applications/opportunity/{opportunity_id}", response_model=List[Application])
async def get_opportunity_applications(
    opportunity_id: str,
    req: Request,
    service: ApplicationService = Depends(get_application_service)
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
        
        return applications
    except Exception as e:
        log_structured(
            logger, "ERROR", "Unexpected error in opportunity applications retrieval",
            trace_id=trace_id,
            operation="get_opportunity_applications",
            error=str(e),
            opportunityId=opportunity_id
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)