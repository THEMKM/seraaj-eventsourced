"""
Opportunities service domain models
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class OpportunityStatus(str, Enum):
    """Opportunity status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    FILLED = "filled" 
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Opportunity(BaseModel):
    """Core opportunity model"""
    id: str = Field(..., description="Unique opportunity identifier")
    organization_id: str = Field(..., description="ID of the organization posting this opportunity")
    title: str = Field(..., min_length=1, max_length=200, description="Opportunity title")
    description: str = Field(..., min_length=1, description="Detailed description")
    category: Optional[str] = Field(None, description="Opportunity category")
    location: str = Field(..., description="Physical location or 'Remote'")
    is_remote: bool = Field(default=False, description="Whether this is a remote opportunity")
    skills_required: List[str] = Field(default_factory=list, description="Required skills")
    time_commitment: Optional[str] = Field(None, description="Time commitment description")
    start_date: datetime = Field(..., description="When the opportunity starts")
    end_date: Optional[datetime] = Field(None, description="When the opportunity ends")
    max_volunteers: int = Field(default=1, ge=1, description="Maximum number of volunteers needed")
    current_volunteers: int = Field(default=0, ge=0, description="Current number of volunteers")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    contact_email: str = Field(..., description="Contact email for applications")
    requirements: Optional[str] = Field(None, description="Additional requirements")
    benefits: Optional[str] = Field(None, description="Benefits for volunteers")
    status: OpportunityStatus = Field(default=OpportunityStatus.ACTIVE, description="Opportunity status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateOpportunityRequest(BaseModel):
    """Request model for creating opportunities"""
    organization_id: str = Field(..., description="Organization ID")
    title: str = Field(..., min_length=1, max_length=200, description="Opportunity title")
    description: str = Field(..., min_length=1, description="Detailed description")
    category: Optional[str] = Field(None, description="Opportunity category")
    location: str = Field(..., description="Physical location or 'Remote'")
    is_remote: bool = Field(default=False, description="Whether this is a remote opportunity")
    skills_required: List[str] = Field(default_factory=list, description="Required skills")
    time_commitment: Optional[str] = Field(None, description="Time commitment description")
    start_date: datetime = Field(..., description="When the opportunity starts")
    end_date: Optional[datetime] = Field(None, description="When the opportunity ends")
    max_volunteers: int = Field(default=1, ge=1, description="Maximum number of volunteers needed")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    contact_email: str = Field(..., description="Contact email for applications")
    requirements: Optional[str] = Field(None, description="Additional requirements")
    benefits: Optional[str] = Field(None, description="Benefits for volunteers")


class UpdateOpportunityRequest(BaseModel):
    """Request model for updating opportunities"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    skills_required: Optional[List[str]] = None
    time_commitment: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_volunteers: Optional[int] = Field(None, ge=1)
    application_deadline: Optional[datetime] = None
    contact_email: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    status: Optional[OpportunityStatus] = None