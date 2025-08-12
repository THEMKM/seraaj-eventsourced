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

# Compatibility helpers for tests and typed construction while preserving runtime shapes
class ScoreComponents(dict):
    """Dict-like score components with friendly constructor.

    Accepts distanceScore/skillsScore/availabilityScore and maps them to
    the canonical keys used across the codebase: distance, skills, availability.
    """
    def __init__(
        self,
        *,
        distanceScore: float,
        skillsScore: float,
        availabilityScore: float,
    ) -> None:
        super().__init__({
            "distance": float(distanceScore),
            "skills": float(skillsScore),
            "availability": float(availabilityScore),
        })


class MatchExplanation(list):
    """List-like explanation with summary and details flattened to a list of strings.

    This preserves the existing API where explanation is a List[str].
    """
    def __init__(self, *, summary: str, details: List[str]) -> None:
        # Ensure all items are strings
        items = [str(summary)] + [str(d) for d in details]
        super().__init__(items)

class VolunteerProfileView(BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str
    level: str
    createdAt: datetime