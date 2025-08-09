# Generated models from JSON schemas
# This is a placeholder - legacy code generation path

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Application(BaseModel):
    id: str
    volunteerId: str
    opportunityId: str
    organizationId: Optional[str] = None
    status: str
    coverLetter: Optional[str] = None
    submittedAt: Optional[datetime] = None
    reviewedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None

class MatchSuggestion(BaseModel):
    id: str
    volunteerId: str
    opportunityId: str
    organizationId: str
    score: float
    scoreComponents: Optional[dict] = None
    explanation: Optional[List[str]] = None
    generatedAt: datetime
    status: str

class VolunteerProfileView(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    level: str
    createdAt: datetime