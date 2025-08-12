"""
FastAPI application for Opportunities service - STUB
"""
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Stub FastAPI app
app = FastAPI(
    title="Opportunities Service (STUB)",
    description="Seraaj Opportunities Service - manages volunteer opportunities and matching",
    version="0.1.0-stub"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stub models
class Opportunity(BaseModel):
    id: str
    organization_id: str
    title: str
    description: str
    skills_required: List[str] = []
    location: str
    start_date: datetime
    end_date: Optional[datetime] = None
    max_volunteers: int = 1
    status: str = "active"  # active, filled, cancelled
    created_at: datetime
    updated_at: datetime

class CreateOpportunityRequest(BaseModel):
    organization_id: str = Field(..., description="Organization ID")
    title: str = Field(..., description="Opportunity title")
    description: str = Field(..., description="Description")
    skills_required: List[str] = []
    location: str = Field(..., description="Location")
    start_date: datetime
    end_date: Optional[datetime] = None
    max_volunteers: int = 1

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "opportunities-stub",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0-stub"
    }

# Stub endpoints
@app.post("/api/opportunities", response_model=Opportunity, status_code=201)
async def create_opportunity(request: CreateOpportunityRequest):
    """Create opportunity - STUB"""
    return Opportunity(
        id=f"opp-stub-{hash(request.title) % 10000}",
        organization_id=request.organization_id,
        title=request.title,
        description=request.description,
        skills_required=request.skills_required,
        location=request.location,
        start_date=request.start_date,
        end_date=request.end_date,
        max_volunteers=request.max_volunteers,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/opportunities/{opportunity_id}", response_model=Opportunity)
async def get_opportunity(opportunity_id: str):
    """Get opportunity - STUB"""
    if not opportunity_id.startswith("opp-"):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return Opportunity(
        id=opportunity_id,
        organization_id=f"org-{opportunity_id[-3:]}",
        title=f"Community Service {opportunity_id[-3:]}",
        description=f"Help with community service project {opportunity_id[-3:]}",
        skills_required=["teaching", "technical"],
        location="Community Center",
        start_date=datetime.utcnow() + timedelta(days=7),
        end_date=datetime.utcnow() + timedelta(days=14),
        max_volunteers=5,
        status="active",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/opportunities", response_model=List[Opportunity])
async def list_opportunities(limit: int = 10, offset: int = 0, organization_id: Optional[str] = None):
    """List opportunities - STUB"""
    opportunities = []
    for i in range(offset, min(offset + limit, offset + 5)):  # Return max 5 stubs
        opportunities.append(Opportunity(
            id=f"opp-stub-{2000 + i}",
            organization_id=organization_id or f"org-{i % 3}",
            title=f"Community Education Program {i}",
            description=f"Help with educational program {i}",
            skills_required=["teaching"] if i % 2 == 0 else ["technical", "social"],
            location=f"Community Center {i % 3}",
            start_date=datetime.utcnow() + timedelta(days=i+1),
            end_date=datetime.utcnow() + timedelta(days=i+8),
            max_volunteers=3 + (i % 3),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
    return opportunities

@app.get("/api/opportunities/organization/{org_id}", response_model=List[Opportunity])
async def get_organization_opportunities(org_id: str, limit: int = 10):
    """Get opportunities for organization - STUB"""
    return await list_opportunities(limit=limit, organization_id=org_id)

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8006)