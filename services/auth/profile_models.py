from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, AnyUrl


class Availability(BaseModel):
    weekdays: Optional[bool] = Field(default=None)
    weekends: Optional[bool] = Field(default=None)
    evenings: Optional[bool] = Field(default=None)


class VolunteerProfile(BaseModel):
    """Volunteer profile stored and managed by Auth service (MVP)."""

    id: UUID = Field(..., description="Profile identifier (UUID)")
    userId: UUID = Field(..., description="Associated user identifier (UUID)")
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., description="User email")
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    availability: Optional[Availability] = None
    profileImageUrl: Optional[AnyUrl] = None
    # Gamification and stats (defaults for new users)
    points: int = Field(default=0, ge=0, description="Volunteer points for gamification")
    level: int = Field(default=1, ge=1, description="Volunteer level for gamification")
    badges: List[Any] = Field(default_factory=list, description="Earned badges metadata list")
    totalHours: int = Field(default=0, ge=0, description="Cumulative volunteer hours (placeholder)")
    completedApplications: int = Field(default=0, ge=0, description="Completed applications count (placeholder)")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = None


class UpdateVolunteerProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    availability: Optional[Availability] = None
    profileImageUrl: Optional[AnyUrl] = None
