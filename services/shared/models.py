# Generated Pydantic models from JSON schemas

from __future__ import annotations

from typing import Optional, List, Dict, Any, Annotated

from pydantic import BaseModel, Field, AnyUrl, EmailStr, ConfigDict

from datetime import datetime

from enum import Enum


#   filename:  application.schema.json
from uuid import UUID
class ApplicationStatus(Enum):
    """
    Current status of the application
    """
    draft = 'draft'
    submitted = 'submitted'
    reviewing = 'reviewing'
    accepted = 'accepted'
    rejected = 'rejected'
    completed = 'completed'
    cancelled = 'cancelled'
class Application(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """
    A volunteer application to an opportunity
    """
    id: UUID
    """
    Unique application identifier
    """
    volunteerId: UUID
    """
    ID of the applying volunteer
    """
    opportunityId: UUID
    """
    ID of the opportunity being applied to
    """
    organizationId: Optional[UUID] = None
    """
    ID of the organization offering the opportunity
    """
    status: ApplicationStatus
    """
    Current status of the application
    """
    coverLetter: Annotated[Optional[str], Field(max_length=1000)] = None
    """
    Optional cover letter from volunteer
    """
    submittedAt: Optional[datetime] = None
    """
    When application was submitted
    """
    reviewedAt: Optional[datetime] = None
    """
    When application was reviewed
    """
    createdAt: datetime
    """
    When application was created
    """
    updatedAt: Optional[datetime] = None
    """
    When application was last updated
    """


# External application model for BFF/API contract compliance
class ExternalApplicationStatus(Enum):
    """
    Application status as exposed in API (matches BFF contract)
    """
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    withdrawn = 'withdrawn'


class ExternalApplication(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """
    Contract-compliant application shape for API responses
    """
    id: UUID
    volunteerId: UUID
    opportunityId: UUID
    organizationId: Optional[UUID] = None
    status: ExternalApplicationStatus
    coverLetter: Annotated[Optional[str], Field(max_length=1000)] = None
    submittedAt: Optional[datetime] = None
    reviewedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


#   filename:  match-suggestion.schema.json
from uuid import UUID
class MatchSuggestionStatus(Enum):
    """
    Current status of the match suggestion
    """
    active = 'active'
    applied = 'applied'
    expired = 'expired'
    dismissed = 'dismissed'
class MatchSuggestion(BaseModel):
    model_config = ConfigDict(extra='ignore')
    """
    A suggested match between volunteer and opportunity
    """
    id: UUID
    """
    Unique match suggestion identifier
    """
    volunteerId: UUID
    """
    ID of the matched volunteer
    """
    opportunityId: UUID
    """
    ID of the matched opportunity
    """
    organizationId: UUID
    """
    ID of the organization offering the opportunity
    """
    score: Annotated[float, Field(ge=0.0, le=100.0)]
    """
    Match confidence score (0-100)
    """
    reasons: Optional[List[str]] = None
    """
    List of reasons why this is a good match
    """
    opportunityTitle: Optional[str] = None
    """
    Title of the matched opportunity
    """
    organizationName: Optional[str] = None
    """
    Name of the organization
    """
    status: MatchSuggestionStatus
    """
    Current status of the match suggestion
    """
    generatedAt: datetime
    """
    When the match was generated
    """
    expiresAt: Optional[datetime] = None
    """
    When the match suggestion expires
    """


#   filename:  volunteer-profile-view.schema.json
from uuid import UUID
class VolunteerStatus(Enum):
    """
    Account status
    """
    pending = 'pending'
    active = 'active'
    inactive = 'inactive'
    suspended = 'suspended'
class Skill(Enum):
    teaching = 'teaching'
    medical = 'medical'
    technical = 'technical'
    administrative = 'administrative'
    creative = 'creative'
    physical = 'physical'
    social = 'social'
class Badge(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: UUID
    name: str
    description: Optional[str] = None
    imageUrl: Optional[AnyUrl] = None
    earnedAt: datetime
class VolunteerProfileView(BaseModel):
    model_config = ConfigDict(extra='ignore')
    """
    A volunteer's profile view for dashboard display
    """
    id: UUID
    """
    Unique volunteer identifier
    """
    email: EmailStr
    """
    Volunteer's email address
    """
    firstName: Annotated[str, Field(max_length=100, min_length=1)]
    """
    Volunteer's first name
    """
    lastName: Annotated[str, Field(max_length=100, min_length=1)]
    """
    Volunteer's last name
    """
    level: Annotated[Optional[int], Field(ge=1, le=100)] = 1
    """
    Gamification level
    """
    status: Optional[VolunteerStatus] = None
    """
    Account status
    """
    skills: Optional[List[Skill]] = None
    """
    Volunteer's verified skills
    """
    badges: Optional[List[Badge]] = None
    """
    Earned badges
    """
    totalHours: Annotated[Optional[float], Field(ge=0.0)] = None
    """
    Total volunteer hours completed
    """
    completedApplications: Annotated[Optional[int], Field(ge=0)] = None
    """
    Number of completed volunteer applications
    """
    createdAt: datetime
    """
    When the volunteer profile was created
    """
    lastActive: Optional[datetime] = None
    """
    Last activity timestamp
    """

