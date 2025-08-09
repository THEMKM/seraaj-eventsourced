from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime, UTC

from services.shared.models import MatchSuggestion
from .algorithm import MatchingAlgorithm
from .repository import MatchRepository

class MatchingService:
    """Matching domain service"""
    
    def __init__(self):
        self.algorithm = MatchingAlgorithm()
        self.repository = MatchRepository()
    
    async def quick_match(
        self,
        volunteer_id: str,
        limit: int = 3
    ) -> List[MatchSuggestion]:
        """Generate quick match suggestions (top matches)"""
        
        # Get volunteer profile
        volunteer = await self._get_volunteer(volunteer_id)
        
        # Get available opportunities
        opportunities = await self._get_available_opportunities()
        
        # Run matching algorithm
        matches = self.algorithm.rank_opportunities(
            volunteer,
            opportunities,
            limit=limit
        )
        
        # Convert to MatchSuggestion objects
        suggestions = []
        for opportunity, score in matches:
            suggestion = MatchSuggestion(
                id=str(uuid4()),
                volunteerId=volunteer_id,
                opportunityId=opportunity["id"],
                organizationId=opportunity["organizationId"],
                score=score.total,
                scoreComponents=score.components,
                explanation=score.explanation,
                generatedAt=datetime.now(UTC),
                status="pending"
            )
            
            # Save to repository
            await self.repository.save(suggestion)
            suggestions.append(suggestion)
        
        return suggestions
    
    async def generate_matches(
        self,
        volunteer_id: str,
        filters: Dict[str, Any] = None,
        limit: int = 10
    ) -> List[MatchSuggestion]:
        """Generate comprehensive match suggestions"""
        
        volunteer = await self._get_volunteer(volunteer_id)
        opportunities = await self._get_available_opportunities(filters)
        
        matches = self.algorithm.rank_opportunities(
            volunteer,
            opportunities,
            limit=limit
        )
        
        suggestions = []
        for opportunity, score in matches:
            suggestion = MatchSuggestion(
                id=str(uuid4()),
                volunteerId=volunteer_id,
                opportunityId=opportunity["id"],
                organizationId=opportunity["organizationId"],
                score=score.total,
                scoreComponents=score.components,
                explanation=score.explanation,
                generatedAt=datetime.now(UTC),
                status="pending"
            )
            await self.repository.save(suggestion)
            suggestions.append(suggestion)
        
        return suggestions
    
    async def get_suggestions(self, volunteer_id: str) -> List[MatchSuggestion]:
        """Get existing suggestions for a volunteer"""
        return await self.repository.find_by_volunteer(volunteer_id)
    
    async def _get_volunteer(self, volunteer_id: str) -> Dict[str, Any]:
        """Get volunteer data (mock for MVP)"""
        # Mock volunteer profiles for testing
        volunteers = {
            "vol1": {
                "id": "vol1",
                "skills": ["teaching", "administrative", "communication"],
                "location": {"latitude": 30.0444, "longitude": 31.2357},  # Cairo
                "availability": ["weekend-morning", "weekend-afternoon", "weekday-evening"]
            },
            "vol2": {
                "id": "vol2",
                "skills": ["medical", "counseling"],
                "location": {"latitude": 30.0626, "longitude": 31.2497},  # Near Cairo
                "availability": ["weekday-morning", "weekday-afternoon"]
            },
            "vol3": {
                "id": "vol3",
                "skills": ["technical", "programming", "design"],
                "location": {"latitude": 31.2001, "longitude": 29.9187},  # Alexandria
                "availability": ["weekend-morning", "weekend-evening"]
            }
        }
        
        # Default volunteer if not found
        return volunteers.get(volunteer_id, {
            "id": volunteer_id,
            "skills": ["general"],
            "location": {"latitude": 30.0444, "longitude": 31.2357},
            "availability": ["weekend-morning"]
        })
    
    async def _get_available_opportunities(
        self,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get available opportunities (mock for MVP)"""
        opportunities = [
            {
                "id": "opp1",
                "organizationId": "org1",
                "title": "Teaching Assistant - Mathematics",
                "description": "Help students with math homework",
                "requiredSkills": ["teaching", "communication"],
                "timeSlots": ["weekend-morning", "weekend-afternoon"],
                "location": {"latitude": 30.0626, "longitude": 31.2497},  # 2km from Cairo center
                "category": "education"
            },
            {
                "id": "opp2",
                "organizationId": "org2",
                "title": "Medical Volunteer",
                "description": "Assist in health clinic",
                "requiredSkills": ["medical"],
                "timeSlots": ["weekday-morning", "weekday-afternoon"],
                "location": {"latitude": 30.0500, "longitude": 31.2333},  # 1km from Cairo center
                "category": "health"
            },
            {
                "id": "opp3",
                "organizationId": "org1",
                "title": "Administrative Support",
                "description": "Help with office tasks and organization",
                "requiredSkills": ["administrative", "communication"],
                "timeSlots": ["weekend-morning", "weekday-evening"],
                "location": {"latitude": 30.0450, "longitude": 31.2350},  # Very close to Cairo
                "category": "administrative"
            },
            {
                "id": "opp4",
                "organizationId": "org3",
                "title": "Website Development",
                "description": "Build website for NGO",
                "requiredSkills": ["technical", "programming", "design"],
                "timeSlots": ["weekend-morning", "weekend-evening"],
                "location": {"latitude": 31.2100, "longitude": 29.9300},  # Alexandria
                "category": "technology"
            },
            {
                "id": "opp5",
                "organizationId": "org2",
                "title": "Counseling Support",
                "description": "Provide emotional support to patients",
                "requiredSkills": ["counseling", "communication"],
                "timeSlots": ["weekday-afternoon", "weekend-afternoon"],
                "location": {"latitude": 30.0400, "longitude": 31.2400},  # Close to Cairo
                "category": "health"
            },
            {
                "id": "opp6",
                "organizationId": "org4",
                "title": "General Volunteer",
                "description": "Help with various tasks as needed",
                "requiredSkills": [],  # No specific skills required
                "timeSlots": ["weekend-morning", "weekend-afternoon"],
                "location": {"latitude": 30.0444, "longitude": 31.2357},  # Exact Cairo center
                "category": "general"
            }
        ]
        
        # Apply filters if provided
        if filters:
            if "category" in filters:
                opportunities = [opp for opp in opportunities if opp["category"] == filters["category"]]
            if "skills" in filters:
                skill_filter = set(filters["skills"])
                opportunities = [
                    opp for opp in opportunities 
                    if not opp["requiredSkills"] or skill_filter & set(opp["requiredSkills"])
                ]
        
        return opportunities