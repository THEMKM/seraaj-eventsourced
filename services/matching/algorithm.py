from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

@dataclass
class MatchScore:
    """Detailed scoring for a match"""
    total: float
    components: Dict[str, float]
    explanation: List[str]

class MatchingAlgorithm:
    """Core matching algorithm"""
    
    # Scoring weights
    WEIGHTS = {
        "distance": 0.4,      # 40% - Physical proximity
        "skills": 0.35,       # 35% - Skill match
        "availability": 0.25, # 25% - Time availability
    }
    
    def calculate_match_score(
        self,
        volunteer: Dict[str, Any],
        opportunity: Dict[str, Any]
    ) -> MatchScore:
        """Calculate match score between volunteer and opportunity"""
        
        components = {}
        explanations = []
        
        # Distance score (inverse of distance)
        distance_km = self._calculate_distance(
            volunteer.get("location", {}),
            opportunity.get("location", {})
        )
        
        if distance_km <= 5:
            components["distance"] = 1.0
            explanations.append("Very close (< 5km)")
        elif distance_km <= 15:
            components["distance"] = 0.8
            explanations.append("Nearby (< 15km)")
        elif distance_km <= 30:
            components["distance"] = 0.5
            explanations.append("Moderate distance (< 30km)")
        else:
            components["distance"] = 0.2
            explanations.append(f"Far ({distance_km:.1f}km)")
        
        # Skills match
        volunteer_skills = set(volunteer.get("skills", []))
        required_skills = set(opportunity.get("requiredSkills", []))
        
        if required_skills:
            skill_match = len(volunteer_skills & required_skills) / len(required_skills)
            components["skills"] = skill_match
            
            if skill_match >= 1.0:
                explanations.append("All skills matched")
            elif skill_match >= 0.5:
                explanations.append(f"{int(skill_match * 100)}% skills matched")
            else:
                explanations.append(f"Only {int(skill_match * 100)}% skills matched")
        else:
            components["skills"] = 1.0  # No specific skills required
            explanations.append("No specific skills required")
        
        # Availability match
        volunteer_avail = set(volunteer.get("availability", []))
        opportunity_times = set(opportunity.get("timeSlots", []))
        
        if opportunity_times and volunteer_avail:
            avail_match = len(volunteer_avail & opportunity_times) / len(opportunity_times)
            components["availability"] = avail_match
            
            if avail_match >= 0.8:
                explanations.append("Excellent time match")
            elif avail_match >= 0.5:
                explanations.append("Good time match")
            else:
                explanations.append("Limited time overlap")
        else:
            components["availability"] = 0.5  # Neutral if not specified
        
        # Calculate weighted total
        total_score = sum(
            components.get(factor, 0) * weight
            for factor, weight in self.WEIGHTS.items()
        )
        
        return MatchScore(
            total=min(total_score, 1.0),  # Keep as 0-1 scale
            components=components,
            explanation=explanations
        )
    
    def _calculate_distance(
        self,
        loc1: Dict[str, float],
        loc2: Dict[str, float]
    ) -> float:
        """Calculate distance between two locations in kilometers"""
        
        if not (loc1 and loc2):
            return 999  # Unknown distance
        
        lat1, lon1 = loc1.get("latitude", 0), loc1.get("longitude", 0)
        lat2, lon2 = loc2.get("latitude", 0), loc2.get("longitude", 0)
        
        if not all([lat1, lon1, lat2, lon2]):
            return 999
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def rank_opportunities(
        self,
        volunteer: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Tuple[Dict[str, Any], MatchScore]]:
        """Rank opportunities for a volunteer"""
        
        scored = []
        for opportunity in opportunities:
            score = self.calculate_match_score(volunteer, opportunity)
            
            # Only include if minimum threshold met
            if score.total >= 0.3:  # 30% minimum match
                scored.append((opportunity, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1].total, reverse=True)
        
        return scored[:limit]