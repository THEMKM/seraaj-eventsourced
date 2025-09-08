# Enhance Matching Algorithm with V2-Style Scoring

## 📋 **Task Description**
Upgrade the current 3-factor matching algorithm to use a more sophisticated 7-factor system with better scoring components, similar to what was working well in the V2 system.

## 🔍 **Current State**
The matching algorithm in `services/matching/algorithm.py` currently uses:
- Distance (40%)
- Skills (35%) 
- Availability (25%)

## 🎯 **Goal**
Expand to a 7-factor system with more nuanced scoring:
- Skill match (25%)
- Location match (20%)
- Availability match (15%)
- Experience match (15%)
- Cause match (10%)
- Time commitment match (10%)
- Interest match (5%)

## ⚡ **Exact Steps to Follow**

### Step 1: Update the WEIGHTS in the algorithm
Modify `services/matching/algorithm.py`:

```python
class MatchingAlgorithm:
    """Core matching algorithm"""
    
    # Updated V2-inspired 7-factor system
    WEIGHTS = {
        "skill_match": 0.25,           # 25% - Skill alignment
        "location_match": 0.20,        # 20% - Location compatibility  
        "availability_match": 0.15,    # 15% - Time availability
        "experience_match": 0.15,      # 15% - Experience level
        "cause_match": 0.10,           # 10% - Cause alignment
        "time_commitment_match": 0.10, # 10% - Hours per week match
        "interest_match": 0.05,        # 5% - Activity type interests
    }
```

### Step 2: Update the calculate_match_score method
Replace the existing method with this expanded version:

```python
def calculate_match_score(
    self,
    volunteer: Dict[str, Any],
    opportunity: Dict[str, Any]
) -> MatchScore:
    """Calculate match score between volunteer and opportunity"""
    
    components = {}
    explanations = []
    
    # 1. Skill matching
    components["skill_match"] = self._calculate_skill_match(
        volunteer.get("skills", []), 
        opportunity.get("requiredSkills", [])
    )
    
    # 2. Location matching
    components["location_match"] = self._calculate_location_match(
        volunteer.get("location", ""),
        opportunity.get("location", ""),
        opportunity.get("remoteAllowed", False)
    )
    
    # 3. Availability matching (time commitment)
    components["availability_match"] = self._calculate_availability_match(
        volunteer.get("availability", ""),
        opportunity.get("timeCommitment", "")
    )
    
    # 4. Experience matching
    components["experience_match"] = self._calculate_experience_match(
        volunteer.get("experienceLevel", "beginner"),
        opportunity.get("experienceRequired", "")
    )
    
    # 5. Cause alignment
    components["cause_match"] = self._calculate_cause_match(
        volunteer.get("causes", []),
        opportunity.get("causes", [])
    )
    
    # 6. Time commitment match (hours per week)
    components["time_commitment_match"] = self._calculate_time_commitment_match(
        volunteer.get("availability", ""),  # Maps to hours/week
        opportunity.get("timeCommitmentHours", 0)
    )
    
    # 7. Interest match (activity types)
    components["interest_match"] = self._calculate_interest_match(
        volunteer.get("interests", []),
        opportunity.get("activityTypes", [])
    )
    
    # Generate explanations
    explanations = self._generate_explanations(volunteer, opportunity, components)
    
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
```

### Step 3: Add the new scoring methods
Add these methods to the MatchingAlgorithm class:

```python
def _calculate_skill_match(self, volunteer_skills: List[str], required_skills: List[str]) -> float:
    """Calculate skill matching score"""
    if not required_skills:
        return 0.5  # Neutral if no skills required
    
    if not volunteer_skills:
        return 0.0
    
    vol_skills = set(skill.lower().strip() for skill in volunteer_skills)
    req_skills = set(skill.lower().strip() for skill in required_skills)
    
    matching_skills = vol_skills.intersection(req_skills)
    match_ratio = len(matching_skills) / len(req_skills)
    
    # Bonus for additional relevant skills
    additional_relevant = vol_skills - req_skills
    bonus = min(len(additional_relevant) * 0.1, 0.3)
    
    return min(match_ratio + bonus, 1.0)

def _calculate_location_match(self, vol_location: str, opp_location: str, remote_allowed: bool) -> float:
    """Calculate location matching score"""
    if remote_allowed:
        return 1.0  # Perfect match if remote work is allowed
    
    if not vol_location or not opp_location:
        return 0.5  # Neutral if location not specified
    
    vol_parts = vol_location.lower().split(',')
    opp_parts = opp_location.lower().split(',')
    
    # Same city match
    if len(vol_parts) >= 1 and len(opp_parts) >= 1:
        if vol_parts[0].strip() == opp_parts[0].strip():
            return 1.0
    
    # Same country match
    if len(vol_parts) >= 2 and len(opp_parts) >= 2:
        if vol_parts[1].strip() == opp_parts[1].strip():
            return 0.7
    
    return 0.2  # Different regions

def _calculate_availability_match(self, volunteer_availability: str, opportunity_commitment: str) -> float:
    """Calculate availability matching score"""
    availability_scores = {
        ("1-2", "minimal"): 1.0,
        ("1-2", "moderate"): 0.3,
        ("1-2", "significant"): 0.1,
        ("3-5", "minimal"): 0.8,
        ("3-5", "moderate"): 1.0,
        ("3-5", "significant"): 0.6,
        ("6-10", "moderate"): 0.9,
        ("6-10", "significant"): 1.0,
        ("6-10", "extensive"): 0.8,
        ("10+", "significant"): 0.9,
        ("10+", "extensive"): 1.0,
    }
    
    key = (volunteer_availability, opportunity_commitment.lower() if opportunity_commitment else "moderate")
    return availability_scores.get(key, 0.5)

def _calculate_experience_match(self, volunteer_exp: str, required_exp: str) -> float:
    """Calculate experience level matching"""
    if not required_exp:
        return 0.8  # Good match if no specific experience required
    
    experience_levels = {
        "beginner": 1,
        "intermediate": 2,
        "advanced": 3,
        "expert": 4,
    }
    
    vol_level = experience_levels.get(volunteer_exp.lower(), 1)
    req_level = experience_levels.get(required_exp.lower(), 1)
    
    # Perfect match if levels are equal
    if vol_level == req_level:
        return 1.0
    
    # Good match if volunteer has higher experience
    if vol_level > req_level:
        return max(0.8 - (vol_level - req_level) * 0.1, 0.5)
    
    # Lower match if volunteer has less experience
    return max(0.6 - (req_level - vol_level) * 0.2, 0.1)

def _calculate_cause_match(self, volunteer_causes: List[str], opportunity_causes: List[str]) -> float:
    """Calculate cause alignment score"""
    if not opportunity_causes or not volunteer_causes:
        return 0.5  # Neutral if causes not specified
    
    vol_causes = set(cause.lower().strip() for cause in volunteer_causes)
    opp_causes = set(cause.lower().strip() for cause in opportunity_causes)
    
    intersection = vol_causes.intersection(opp_causes)
    union = vol_causes.union(opp_causes)
    
    if not union:
        return 0.5
    
    # Jaccard similarity
    return len(intersection) / len(union)

def _calculate_time_commitment_match(self, volunteer_availability: str, opportunity_hours: int) -> float:
    """Calculate time commitment matching"""
    if not volunteer_availability or not opportunity_hours:
        return 0.6  # Neutral if time not specified
    
    # Map availability to hours per week
    availability_hours = {
        "1-2": 1.5,
        "3-5": 4,
        "6-10": 8,
        "10+": 15
    }
    
    volunteer_hours = availability_hours.get(volunteer_availability, 4)
    
    # Calculate ratio (smaller/larger to get value <= 1)
    ratio = min(volunteer_hours, opportunity_hours) / max(volunteer_hours, opportunity_hours)
    return ratio

def _calculate_interest_match(self, volunteer_interests: List[str], activity_types: List[str]) -> float:
    """Calculate interest/activity type matching"""
    if not activity_types or not volunteer_interests:
        return 0.5  # Neutral if not specified
    
    vol_interests = set(interest.lower().strip() for interest in volunteer_interests)
    opp_activities = set(activity.lower().strip() for activity in activity_types)
    
    intersection = vol_interests.intersection(opp_activities)
    
    if not opp_activities:
        return 0.5
    
    return len(intersection) / len(opp_activities)

def _generate_explanations(self, volunteer: Dict[str, Any], opportunity: Dict[str, Any], components: Dict[str, float]) -> List[str]:
    """Generate human-readable match explanations"""
    explanations = []
    
    # Skills
    if components.get("skill_match", 0) > 0.7:
        matching_skills = set(volunteer.get("skills", [])) & set(opportunity.get("requiredSkills", []))
        if matching_skills:
            explanations.append(f"Strong skills match: {', '.join(list(matching_skills)[:3])}")
    
    # Location
    if opportunity.get("remoteAllowed", False):
        explanations.append("Remote work available")
    elif components.get("location_match", 0) > 0.8:
        explanations.append("Same location")
    
    # Causes
    if components.get("cause_match", 0) > 0.6:
        matching_causes = set(volunteer.get("causes", [])) & set(opportunity.get("causes", []))
        if matching_causes:
            explanations.append(f"Shared cause: {list(matching_causes)[0]}")
    
    # Experience
    if components.get("experience_match", 0) > 0.8:
        explanations.append("Good experience match")
    
    return explanations[:4]  # Return top 4 reasons
```

### Step 4: Update the test data structure
Update test data in `services/matching/tests/test_algorithm.py` to include the new fields:

```python
def test_enhanced_matching():
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["Teaching", "Mentoring"],
        "location": "Amman, Jordan", 
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education", "Youth Development"],
        "interests": ["Direct Service", "Training"]
    }
    
    opportunity = {
        "requiredSkills": ["Teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "beginner", 
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    # Should be a high match score
    assert score.total > 0.7
    assert len(score.components) == 7
    assert "Strong skills match" in score.explanation
```

## ✅ **Definition of Done**
- [ ] Algorithm uses 7 scoring factors instead of 3
- [ ] All new scoring methods are implemented correctly
- [ ] Skill matching works with string matching and bonuses
- [ ] Location matching handles city/country comparisons
- [ ] Experience matching uses proper level comparisons
- [ ] Cause matching uses set intersection (Jaccard similarity)
- [ ] Time commitment matching maps availability to hours
- [ ] Interest matching compares activity types
- [ ] Explanations generated for high-scoring factors
- [ ] Tests pass with new scoring system
- [ ] Match scores are more nuanced and accurate

## 🧪 **How to Test**
1. Run the existing matching tests: `pytest services/matching/tests/`
2. Test matching API endpoint with sample volunteer/opportunity data
3. Verify match scores show more granular differences
4. Check that explanations include the new factors
5. Compare match quality with old 3-factor system

**This should take 2-3 hours to implement and test.**