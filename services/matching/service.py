import os
import logging
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime, UTC

from services.shared.models import MatchSuggestion
from .algorithm import MatchingAlgorithm
from .repository import MatchRepository
from .adapters import AuthServiceAdapter, OpportunitiesServiceAdapter

try:
    from infrastructure.event_bus import RedisEventBus
    from infrastructure.event_types import EventTypes
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MatchingService:
    """Matching domain service with event publishing"""
    
    def __init__(self):
        self.algorithm = MatchingAlgorithm()
        self.repository = MatchRepository()
        
        # Service adapters for external data
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")
        opportunities_service_url = os.getenv("OPPORTUNITIES_SERVICE_URL", "http://localhost:8002")
        self.auth_adapter = AuthServiceAdapter(auth_service_url)
        self.opportunities_adapter = OpportunitiesServiceAdapter(opportunities_service_url)
        
        # Event publishing setup
        self.use_redis = os.getenv("USE_REDIS_EVENTS", "true").lower() == "true"
        self.redis_bus = None
        
        if self.use_redis and REDIS_AVAILABLE:
            try:
                self.redis_bus = RedisEventBus()
            except Exception as e:
                logger.warning(f"Failed to initialize Redis event bus: {e}")
                self.redis_bus = None
    
    async def quick_match(
        self,
        volunteer_id: str,
        limit: int = 3,
        authorization: str = None
    ) -> List[MatchSuggestion]:
        """Generate quick match suggestions (top matches)"""
        
        # Get volunteer profile from Auth service
        volunteer = await self.auth_adapter.get_volunteer_profile(volunteer_id, authorization)
        if not volunteer:
            logger.warning(f"Volunteer profile not found: {volunteer_id}")
            return []
        
        # Convert profile to internal format
        volunteer = self._convert_volunteer_profile(volunteer)
        
        # Get available opportunities from Opportunities service
        opportunities = await self.opportunities_adapter.get_available_opportunities()
        
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
                # Scale to 0-100 as per shared model
                score=round(score.total * 100, 2),
                # Extras are ignored by the model, but we still pass reasons below
                # to preserve human-friendly explanations when serialized
                # scoreComponents=score.components,
                # explanation=score.explanation,
                reasons=score.explanation,
                opportunityTitle=opportunity.get("title"),
                generatedAt=datetime.now(UTC),
                status="active"
            )
            
            # Save to repository
            await self.repository.save(suggestion)
            suggestions.append(suggestion)
        
        # Publish match generation event
        await self._publish_match_suggestions_generated(volunteer_id, suggestions)
        
        return suggestions
    
    async def generate_matches(
        self,
        volunteer_id: str,
        filters: Dict[str, Any] = None,
        limit: int = 10,
        authorization: str = None
    ) -> List[MatchSuggestion]:
        """Generate comprehensive match suggestions"""
        
        # Get volunteer profile from Auth service
        volunteer = await self.auth_adapter.get_volunteer_profile(volunteer_id, authorization)
        if not volunteer:
            logger.warning(f"Volunteer profile not found: {volunteer_id}")
            return []
        
        # Convert profile to internal format
        volunteer = self._convert_volunteer_profile(volunteer)
        
        # Get available opportunities from Opportunities service
        opportunities = await self.opportunities_adapter.get_available_opportunities(filters)
        
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
                score=round(score.total * 100, 2),
                reasons=score.explanation,
                opportunityTitle=opportunity.get("title"),
                generatedAt=datetime.now(UTC),
                status="active"
            )
            await self.repository.save(suggestion)
            suggestions.append(suggestion)
        
        # Publish match generation event
        await self._publish_match_suggestions_generated(volunteer_id, suggestions)
        
        return suggestions
    
    async def get_suggestions(self, volunteer_id: str) -> List[MatchSuggestion]:
        """Get existing suggestions for a volunteer"""
        return await self.repository.find_by_volunteer(volunteer_id)
    
    def _convert_volunteer_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Convert volunteer profile from Auth service to internal matching format"""
        # Extract location coordinates (default to Cairo if not specified)
        location = {"latitude": 30.0444, "longitude": 31.2357}
        if profile.get("location"):
            # For MVP, use simple location mapping
            location_str = profile["location"].lower()
            if "alexandria" in location_str:
                location = {"latitude": 31.2001, "longitude": 29.9187}
            elif "giza" in location_str:
                location = {"latitude": 30.0131, "longitude": 31.2089}
        
        # Convert availability structure
        availability = []
        if profile.get("availability"):
            avail = profile["availability"]
            if avail.get("weekdays"):
                availability.extend(["weekday-morning", "weekday-afternoon"])
            if avail.get("weekends"):
                availability.extend(["weekend-morning", "weekend-afternoon"])
            if avail.get("evenings"):
                availability.append("weekday-evening")
        
        # Default availability if none specified
        if not availability:
            availability = ["weekend-morning"]
        
        return {
            "id": profile.get("id") or profile.get("userId"),
            "skills": profile.get("skills", []),
            "location": location,
            "availability": availability
        }
    
    
    # Event publishing helper methods
    async def _publish_match_suggestions_generated(self, volunteer_id: str, suggestions: List[MatchSuggestion]):
        """Publish event when match suggestions are generated"""
        if not self.redis_bus:
            return
        
        try:
            await self.redis_bus.publish(
                EventTypes.MATCH_SUGGESTIONS_GENERATED,
                {
                    "volunteerId": volunteer_id,
                    "matchCount": len(suggestions),
                    "matches": [
                        {
                            "id": s.id,
                            "opportunityId": s.opportunityId,
                            "organizationId": s.organizationId,
                            "score": s.score,
                            "explanation": s.explanation
                        }
                        for s in suggestions
                    ],
                    "generatedAt": datetime.now(UTC).isoformat()
                },
                source_service="matching"
            )
            logger.info(f"Published match suggestions generated event for volunteer {volunteer_id}")
        except Exception as e:
            logger.error(f"Failed to publish match suggestions event: {e}")
    
    async def publish_match_suggestion_applied(self, suggestion_id: str, volunteer_id: str, opportunity_id: str):
        """Publish event when volunteer applies to a matched opportunity"""
        if not self.redis_bus:
            return
            
        try:
            await self.redis_bus.publish(
                EventTypes.MATCH_SUGGESTION_APPLIED,
                {
                    "suggestionId": suggestion_id,
                    "volunteerId": volunteer_id,
                    "opportunityId": opportunity_id,
                    "appliedAt": datetime.now(UTC).isoformat()
                },
                source_service="matching"
            )
            logger.info(f"Published match suggestion applied event: {suggestion_id}")
        except Exception as e:
            logger.error(f"Failed to publish match applied event: {e}")
    
    async def close(self):
        """Close event bus connections"""
        if self.redis_bus:
            await self.redis_bus.close()
