"""
Service adapters for Matching service to call external services
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class AuthServiceAdapter:
    """Adapter to call Auth service for volunteer profiles"""
    
    def __init__(self, auth_service_url: str = "http://localhost:8004"):
        self.base_url = auth_service_url.rstrip('/')
        self.timeout = 30.0
    
    async def get_volunteer_profile(self, volunteer_id: str, authorization: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get volunteer profile from Auth service.

        Note: Auth service exposes only authenticated profile at /auth/profile.
        We rely on the forwarded Authorization header to return the correct user's profile.
        """
        try:
            headers = {}
            if authorization:
                headers["Authorization"] = authorization
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/auth/profile",
                    headers=headers
                )
                
                if response.status_code == 200:
                    profile = response.json()
                    # Optional: warn if token subject doesn't match requested volunteer_id
                    req_id = str(volunteer_id)
                    prof_user_id = str(profile.get("userId", ""))
                    if req_id and prof_user_id and req_id != prof_user_id:
                        logger.warning(
                            f"Auth profile userId ({prof_user_id}) does not match requested volunteerId ({req_id})"
                        )
                    return profile
                elif response.status_code == 404:
                    logger.warning(f"Volunteer profile not found for token subject (requested id: {volunteer_id})")
                    return None
                else:
                    logger.error(f"Auth service error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch volunteer profile {volunteer_id}: {e}")
            return None


class OpportunitiesServiceAdapter:
    """Adapter to call Opportunities service for available opportunities"""
    
    def __init__(self, opportunities_service_url: str = "http://localhost:8002"):
        self.base_url = opportunities_service_url
        self.timeout = 30.0
    
    async def get_available_opportunities(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get available opportunities from Opportunities service"""
        try:
            params = {"limit": 50}  # Get more opportunities for matching
            if filters:
                if "category" in filters:
                    params["category"] = filters["category"]
                if "organization_id" in filters:
                    params["organization_id"] = filters["organization_id"]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/opportunities",
                    params=params
                )
                
                if response.status_code == 200:
                    opportunities = response.json()
                    # Convert to internal format expected by matching algorithm
                    converted_opportunities = []
                    for opp in opportunities:
                        converted_opportunities.append({
                            "id": opp["id"],
                            "organizationId": opp["organization_id"],
                            "title": opp["title"],
                            "description": opp["description"],
                            "requiredSkills": opp.get("skills_required", []),
                            "timeSlots": self._extract_time_slots(opp),
                            "location": self._extract_location_coordinates(opp["location"]),
                            "category": self._categorize_opportunity(opp),
                        })
                    return converted_opportunities
                else:
                    logger.error(f"Opportunities service error: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            return []
    
    def _extract_time_slots(self, opportunity: Dict[str, Any]) -> List[str]:
        """Extract time slots from opportunity data"""
        # For MVP, use simple heuristics based on opportunity type
        # In production, this would be structured data
        time_slots = []
        description = opportunity.get("description", "").lower()
        title = opportunity.get("title", "").lower()
        
        if "evening" in description or "evening" in title:
            time_slots.append("weekday-evening")
        if "weekend" in description or "weekend" in title:
            time_slots.extend(["weekend-morning", "weekend-afternoon"])
        if "morning" in description or "morning" in title:
            time_slots.append("weekday-morning")
        if "afternoon" in description or "afternoon" in title:
            time_slots.append("weekday-afternoon")
        
        # Default time slots if none detected
        if not time_slots:
            time_slots = ["weekend-morning", "weekday-evening"]
        
        return time_slots
    
    def _extract_location_coordinates(self, location: str) -> Dict[str, float]:
        """Extract coordinates from location string"""
        # For MVP, use hardcoded coordinates based on common locations
        # In production, this would integrate with a geocoding service
        location_lower = location.lower()
        
        # Default to Cairo center
        coords = {"latitude": 30.0444, "longitude": 31.2357}
        
        if "alexandria" in location_lower:
            coords = {"latitude": 31.2001, "longitude": 29.9187}
        elif "giza" in location_lower:
            coords = {"latitude": 30.0131, "longitude": 31.2089}
        elif "downtown" in location_lower or "center" in location_lower:
            coords = {"latitude": 30.0444, "longitude": 31.2357}
        
        return coords
    
    def _categorize_opportunity(self, opportunity: Dict[str, Any]) -> str:
        """Categorize opportunity based on title/description"""
        title = opportunity.get("title", "").lower()
        description = opportunity.get("description", "").lower()
        skills = [skill.lower() for skill in opportunity.get("skills_required", [])]
        
        if "teach" in title or "education" in title or "teaching" in skills:
            return "education"
        elif "medical" in title or "health" in title or "medical" in skills:
            return "health"
        elif "technical" in title or "programming" in skills or "design" in skills:
            return "technology"
        elif "administrative" in title or "office" in title:
            return "administrative"
        else:
            return "general"
