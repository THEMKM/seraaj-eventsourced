"""
FastAPI application for Volunteers service - STUB
"""
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Stub FastAPI app
app = FastAPI(
    title="Volunteers Service (STUB)",
    description="Seraaj Volunteers Service - manages volunteer profiles and verification",
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
class VolunteerProfile(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str] = None
    skills: List[str] = []
    availability: List[str] = []
    verified: bool = False
    created_at: datetime
    updated_at: datetime

class CreateVolunteerRequest(BaseModel):
    email: str = Field(..., description="Email address")
    name: str = Field(..., description="Full name")
    phone: Optional[str] = None
    skills: List[str] = []
    availability: List[str] = []

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "volunteers-stub",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0-stub"
    }

# Stub endpoints
@app.post("/api/volunteers", response_model=VolunteerProfile, status_code=201)
async def create_volunteer(request: CreateVolunteerRequest):
    """Create volunteer profile - STUB"""
    return VolunteerProfile(
        id=f"vol-stub-{hash(request.email) % 10000}",
        email=request.email,
        name=request.name,
        phone=request.phone,
        skills=request.skills,
        availability=request.availability,
        verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/volunteers/{volunteer_id}", response_model=VolunteerProfile)
async def get_volunteer(volunteer_id: str):
    """Get volunteer profile - STUB"""
    if not volunteer_id.startswith("vol-"):
        raise HTTPException(status_code=404, detail="Volunteer not found")
    
    return VolunteerProfile(
        id=volunteer_id,
        email=f"volunteer{volunteer_id[-4:]}@example.com",
        name=f"Volunteer {volunteer_id[-4:]}",
        phone="+1-555-0123",
        skills=["teaching", "technical", "social"],
        availability=["weekends", "evenings"],
        verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/volunteers", response_model=List[VolunteerProfile])
async def list_volunteers(limit: int = 10, offset: int = 0):
    """List volunteers - STUB"""
    volunteers = []
    for i in range(offset, min(offset + limit, offset + 5)):  # Return max 5 stubs
        volunteers.append(VolunteerProfile(
            id=f"vol-stub-{1000 + i}",
            email=f"volunteer{i}@example.com",
            name=f"Volunteer {i}",
            skills=["teaching"] if i % 2 == 0 else ["technical"],
            availability=["weekends"],
            verified=i % 3 == 0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
    return volunteers

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8005)