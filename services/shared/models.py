# Generated models from JSON schemas
# This is a placeholder - legacy code generation path

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Application(BaseModel):
    id: str
    volunteerId: str
    opportunityId: str
    status: str
    createdAt: datetime
    coverLetter: Optional[str] = None

class MatchSuggestion(BaseModel):
    id: str
    volunteerId: str
    opportunityId: str
    organizationId: str
    score: float
    generatedAt: datetime
    status: str

class VolunteerProfileView(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    level: str
    createdAt: datetime