"""
FastAPI application for Opportunities service
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from .models import Opportunity, CreateOpportunityRequest, UpdateOpportunityRequest, OpportunityStatus
from .repository import OpportunityRepository

# FastAPI app
app = FastAPI(
    title="Opportunities Service",
    description="Seraaj Opportunities Service - manages volunteer opportunities and matching",
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

# Repository instance
repository = OpportunityRepository()

# Dependency to get repository
def get_repository() -> OpportunityRepository:
    return repository

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "opportunities",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# API endpoints
@app.post("/api/opportunities", response_model=Opportunity, status_code=201)
async def create_opportunity(
    request: CreateOpportunityRequest,
    repo: OpportunityRepository = Depends(get_repository)
):
    """Create a new volunteer opportunity"""
    try:
        # Create opportunity from request
        opportunity = Opportunity(
            id="",  # Will be set by repository
            organization_id=request.organization_id,
            title=request.title,
            description=request.description,
            category=request.category,
            location=request.location,
            is_remote=request.is_remote,
            skills_required=request.skills_required,
            time_commitment=request.time_commitment,
            start_date=request.start_date,
            end_date=request.end_date,
            max_volunteers=request.max_volunteers,
            application_deadline=request.application_deadline,
            contact_email=request.contact_email,
            requirements=request.requirements,
            benefits=request.benefits,
            status=OpportunityStatus.ACTIVE
        )
        
        created_opportunity = await repo.create(opportunity)
        return created_opportunity
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create opportunity: {str(e)}")

@app.get("/api/opportunities/{opportunity_id}", response_model=Opportunity)
async def get_opportunity(
    opportunity_id: str,
    repo: OpportunityRepository = Depends(get_repository)
):
    """Get a specific opportunity by ID"""
    opportunity = await repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return opportunity

@app.get("/api/opportunities", response_model=List[Opportunity])
async def list_opportunities(
    limit: int = Query(20, ge=1, le=100, description="Number of opportunities to return"),
    offset: int = Query(0, ge=0, description="Number of opportunities to skip"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    status: Optional[OpportunityStatus] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    repo: OpportunityRepository = Depends(get_repository)
):
    """List opportunities with filtering and pagination"""
    try:
        opportunities = await repo.list_opportunities(
            limit=limit,
            offset=offset,
            organization_id=organization_id,
            status=status,
            category=category
        )
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch opportunities: {str(e)}")

@app.put("/api/opportunities/{opportunity_id}", response_model=Opportunity)
async def update_opportunity(
    opportunity_id: str,
    request: UpdateOpportunityRequest,
    repo: OpportunityRepository = Depends(get_repository)
):
    """Update an existing opportunity"""
    # Check if opportunity exists
    existing = await repo.get(opportunity_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Prepare updates (only include fields that were provided)
    updates = {}
    for field, value in request.model_dump(exclude_unset=True).items():
        updates[field] = value
    
    try:
        updated_opportunity = await repo.update(opportunity_id, updates)
        if not updated_opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return updated_opportunity
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update opportunity: {str(e)}")


@app.delete("/api/opportunities/{opportunity_id}", status_code=204)
async def delete_opportunity(
    opportunity_id: str,
    repo: OpportunityRepository = Depends(get_repository)
):
    """Delete an opportunity"""
    deleted = await repo.delete(opportunity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Opportunity not found")


@app.get("/api/opportunities/organization/{org_id}", response_model=List[Opportunity])
async def get_organization_opportunities(
    org_id: str,
    limit: int = Query(50, ge=1, le=100),
    repo: OpportunityRepository = Depends(get_repository)
):
    """Get opportunities for a specific organization"""
    return await repo.get_by_organization(org_id)


@app.get("/api/opportunities/stats/organization/{org_id}")
async def get_organization_stats(
    org_id: str,
    repo: OpportunityRepository = Depends(get_repository)
):
    """Get statistics for an organization's opportunities"""
    try:
        opportunities = await repo.get_by_organization(org_id)
        
        total = len(opportunities)
        active = len([o for o in opportunities if o.status == OpportunityStatus.ACTIVE])
        filled = len([o for o in opportunities if o.status == OpportunityStatus.FILLED])
        completed = len([o for o in opportunities if o.status == OpportunityStatus.COMPLETED])
        
        return {
            "organization_id": org_id,
            "total_opportunities": total,
            "active_opportunities": active,
            "filled_opportunities": filled,
            "completed_opportunities": completed,
            "total_volunteer_slots": sum(o.max_volunteers for o in opportunities),
            "filled_volunteer_slots": sum(o.current_volunteers for o in opportunities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Main entry point
if __name__ == "__main__":
    from services.shared.port_config import get_service_startup_config
    
    host, port = get_service_startup_config("opportunities")
    print(f"Starting Opportunities service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)