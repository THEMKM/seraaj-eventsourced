import pytest
from services.matching.algorithm import MatchingAlgorithm, MatchScore

def test_distance_calculation():
    """Test distance calculation"""
    algorithm = MatchingAlgorithm()
    
    # Cairo to Alexandria (approximate)
    cairo = {"latitude": 30.0444, "longitude": 31.2357}
    alex = {"latitude": 31.2001, "longitude": 29.9187}
    
    distance = algorithm._calculate_distance(cairo, alex)
    assert 170 <= distance <= 200  # Approximate distance (more accurate)

def test_distance_same_location():
    """Test distance calculation for same location"""
    algorithm = MatchingAlgorithm()
    
    cairo = {"latitude": 30.0444, "longitude": 31.2357}
    
    distance = algorithm._calculate_distance(cairo, cairo)
    assert distance < 1  # Should be very close to 0

def test_distance_missing_data():
    """Test distance calculation with missing location data"""
    algorithm = MatchingAlgorithm()
    
    distance = algorithm._calculate_distance({}, {"latitude": 30.0444, "longitude": 31.2357})
    assert distance == 999  # Should return high distance for unknown

def test_enhanced_matching():
    """Test the enhanced 7-factor matching system"""
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
    assert any("Strong skills match" in explanation for explanation in score.explanation)

def test_skill_matching_perfect():
    """Test perfect skill matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching", "administrative"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.total >= 0.8  # Should be high match
    assert score.components["skill_match"] >= 0.9  # Perfect skill match with bonus
    assert any("Strong skills match" in explanation for explanation in score.explanation)

def test_skill_matching_partial():
    """Test partial skill matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching", "administrative"],  # 2 required, volunteer has 1
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["skill_match"] == 0.5  # 50% skill match
    assert score.total > 0.5  # Should still be decent match due to other factors

def test_skill_matching_none():
    """Test no skill matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["medical"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Health"],
        "interests": ["Clinical Work"]
    }
    
    opportunity = {
        "requiredSkills": ["technical", "programming"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Technology"],
        "activityTypes": ["Software Development"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["skill_match"] <= 0.1  # Very low skill match (with minimal bonus)

def test_availability_matching():
    """Test availability matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",  # 3-5 hours per week
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",  # Should match 3-5 hours
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["availability_match"] == 1.0  # Perfect availability match

def test_location_matching_same_city():
    """Test location matching for same city"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",  # Same city
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["location_match"] == 1.0  # Perfect location match

def test_location_matching_remote():
    """Test location matching when remote is allowed"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "New York, USA",  # Different city
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": True,  # Remote allowed
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["location_match"] == 1.0  # Perfect match due to remote
    assert "Remote work available" in score.explanation

def test_experience_matching():
    """Test experience level matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",  # Perfect match
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["experience_match"] == 1.0  # Perfect experience match

def test_cause_matching():
    """Test cause alignment matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],  # Only one cause for better match
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],  # Same single cause
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["cause_match"] == 1.0  # Perfect cause match (same single cause)
    assert any("Shared cause" in explanation for explanation in score.explanation)

def test_low_match_filtered():
    """Test that low matches are filtered out"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["medical"],
        "location": "Amman, Jordan",
        "availability": "1-2",
        "experienceLevel": "beginner",
        "causes": ["Health"],
        "interests": ["Clinical Work"]
    }
    
    # Opportunity with completely different requirements
    opportunity = {
        "requiredSkills": ["technical"],
        "location": "New York, USA",  # Different country
        "timeCommitment": "extensive",  # Much more time
        "experienceRequired": "expert",  # Much more experience
        "causes": ["Technology"],  # Different cause
        "activityTypes": ["Software Development"],  # Different activity
        "remoteAllowed": False,  # Not remote
        "timeCommitmentHours": 20  # Way more hours
    }
    
    matches = algorithm.rank_opportunities(volunteer, [opportunity])
    assert len(matches) == 0  # Should be filtered out for low score

def test_ranking_order():
    """Test that opportunities are ranked correctly"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching", "administrative"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    # High match opportunity
    good_opp = {
        "id": "good",
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",  # Same location
        "timeCommitment": "moderate",  # Perfect match
        "experienceRequired": "intermediate",  # Perfect match
        "causes": ["Education"],  # Same cause
        "activityTypes": ["Direct Service"],  # Same interest
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    # Lower match opportunity
    okay_opp = {
        "id": "okay", 
        "requiredSkills": ["teaching"],
        "location": "Cairo, Egypt",  # Different country
        "timeCommitment": "significant",  # More time required
        "experienceRequired": "advanced",  # Higher experience
        "causes": ["Youth Development"],  # Different cause
        "activityTypes": ["Training"],  # Different activity
        "remoteAllowed": False,
        "timeCommitmentHours": 8
    }
    
    matches = algorithm.rank_opportunities(volunteer, [okay_opp, good_opp])
    
    # Should be ordered by score (highest first)
    assert len(matches) == 2
    assert matches[0][0]["id"] == "good"  # Better match should be first
    assert matches[0][1].total > matches[1][1].total  # Higher score first

def test_score_components_structure():
    """Test that score components are properly structured"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    # Verify all expected 7 components are present
    expected_components = [
        "skill_match", "location_match", "availability_match", 
        "experience_match", "cause_match", "time_commitment_match", "interest_match"
    ]
    for component in expected_components:
        assert component in score.components
    
    # Verify score is within valid range
    assert 0.0 <= score.total <= 1.0
    
    # Verify explanations are provided
    assert isinstance(score.explanation, list)
    assert len(score.explanation) > 0

def test_no_required_skills():
    """Test opportunity with no required skills"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["anything"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": [],  # No skills required
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["skill_match"] == 0.5  # Neutral score for no requirements

def test_interest_matching():
    """Test interest/activity type matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service", "Training"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],  # Matches one interest
        "remoteAllowed": False,
        "timeCommitmentHours": 4
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["interest_match"] == 1.0  # Perfect interest match

def test_time_commitment_matching():
    """Test time commitment hours matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": "Amman, Jordan",
        "availability": "3-5",  # Maps to 4 hours
        "experienceLevel": "intermediate",
        "causes": ["Education"],
        "interests": ["Direct Service"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": "Amman, Jordan",
        "timeCommitment": "moderate",
        "experienceRequired": "intermediate",
        "causes": ["Education"],
        "activityTypes": ["Direct Service"],
        "remoteAllowed": False,
        "timeCommitmentHours": 4  # Perfect match with volunteer's 4 hours
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["time_commitment_match"] == 1.0  # Perfect time match