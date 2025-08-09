"""
FastAPI application for Applications service
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.shared.models import Application
from .service import ApplicationService, SubmitApplicationCommand


# FastAPI app
app = FastAPI(
    title="Applications Service",
    description="Seraaj Applications Service - manages volunteer application lifecycle",
    version="1.0.0"
)

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


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "applications",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# Application endpoints
@app.post("/api/applications", response_model=Application, status_code=201)
async def submit_application(
    request: SubmitApplicationRequest,
    service: ApplicationService = Depends(get_application_service)
):
    """Submit a new application"""
    try:
        command = SubmitApplicationCommand(
            volunteer_id=request.volunteerId,
            opportunity_id=request.opportunityId,
            cover_letter=request.coverLetter
        )
        application = await service.submit_application(command)
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/applications/{application_id}", response_model=Application)
async def get_application(
    application_id: str,
    service: ApplicationService = Depends(get_application_service)
):
    """Get application by ID"""
    try:
        application = await service.get_application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.patch("/api/applications/{application_id}/state", response_model=Application)
async def update_application_state(
    application_id: str,
    request: UpdateStateRequest,
    service: ApplicationService = Depends(get_application_service)
):
    """Update application state"""
    try:
        application = await service.update_application_state(
            application_id=application_id,
            action=request.action,
            reason=request.reason
        )
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/applications/volunteer/{volunteer_id}", response_model=List[Application])
async def get_volunteer_applications(
    volunteer_id: str,
    service: ApplicationService = Depends(get_application_service)
):
    """Get all applications for a volunteer"""
    try:
        applications = await service.get_volunteer_applications(volunteer_id)
        return applications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/applications/opportunity/{opportunity_id}", response_model=List[Application])
async def get_opportunity_applications(
    opportunity_id: str,
    service: ApplicationService = Depends(get_application_service)
):
    """Get all applications for an opportunity"""
    try:
        applications = await service.get_opportunity_applications(opportunity_id)
        return applications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)