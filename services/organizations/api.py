"""
FastAPI application for Organizations service - STUB
"""
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Stub FastAPI app
app = FastAPI(
    title="Organizations Service (STUB)",
    description="Seraaj Organizations Service - manages nonprofit organizations and verification",
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
class Organization(BaseModel):
    id: str
    name: str
    description: str
    website: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    verified: bool = False
    tax_exempt: bool = False
    created_at: datetime
    updated_at: datetime

class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., description="Organization name")
    description: str = Field(..., description="Description")
    website: Optional[str] = None
    contact_email: str = Field(..., description="Contact email")
    contact_phone: Optional[str] = None
    address: Optional[str] = None

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "organizations-stub",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0-stub"
    }

# Stub endpoints
@app.post("/api/organizations", response_model=Organization, status_code=201)
async def create_organization(request: CreateOrganizationRequest):
    """Create organization - STUB"""
    return Organization(
        id=f"org-stub-{hash(request.name) % 10000}",
        name=request.name,
        description=request.description,
        website=request.website,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone,
        address=request.address,
        verified=False,
        tax_exempt=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/organizations/{organization_id}", response_model=Organization)
async def get_organization(organization_id: str):
    """Get organization - STUB"""
    if not organization_id.startswith("org-"):
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return Organization(
        id=organization_id,
        name=f"Hope Foundation {organization_id[-3:]}",
        description=f"A nonprofit organization focused on community service {organization_id[-3:]}",
        website=f"https://hopefoundation{organization_id[-3:]}.org",
        contact_email=f"contact@hopefoundation{organization_id[-3:]}.org",
        contact_phone="+1-555-0100",
        address=f"123 Community St, City, State {organization_id[-3:]}",
        verified=True,
        tax_exempt=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/organizations", response_model=List[Organization])
async def list_organizations(limit: int = 10, offset: int = 0, verified: Optional[bool] = None):
    """List organizations - STUB"""
    organizations = []
    for i in range(offset, min(offset + limit, offset + 5)):  # Return max 5 stubs
        is_verified = verified if verified is not None else (i % 2 == 0)
        organizations.append(Organization(
            id=f"org-stub-{3000 + i}",
            name=f"Hope Foundation {i}",
            description=f"Community service organization {i}",
            website=f"https://hopefoundation{i}.org",
            contact_email=f"contact{i}@hopefoundation.org",
            contact_phone="+1-555-0100",
            address=f"123 Community St {i}",
            verified=is_verified,
            tax_exempt=is_verified,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
    return organizations

@app.patch("/api/organizations/{organization_id}/verify")
async def verify_organization(organization_id: str):
    """Verify organization - STUB"""
    if not organization_id.startswith("org-"):
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {"message": f"Organization {organization_id} verification initiated", "status": "pending"}

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8007)