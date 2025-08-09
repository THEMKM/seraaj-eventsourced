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

def test_skill_matching_perfect():
    """Test perfect skill matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching", "administrative"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "timeSlots": ["weekend-morning"]
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.total >= 0.8  # Should be high match
    assert score.components["skills"] == 1.0  # Perfect skill match
    assert "All skills matched" in score.explanation

def test_skill_matching_partial():
    """Test partial skill matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching", "administrative"],  # 2 required, volunteer has 1
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "timeSlots": ["weekend-morning"]
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["skills"] == 0.5  # 50% skill match
    assert "50% skills matched" in score.explanation

def test_skill_matching_none():
    """Test no skill matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["medical"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning"]
    }
    
    opportunity = {
        "requiredSkills": ["technical", "programming"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "timeSlots": ["weekend-morning"]
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["skills"] == 0.0  # No skill match

def test_availability_matching():
    """Test availability matching"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning", "weekend-afternoon"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "timeSlots": ["weekend-morning"]  # 1 out of 1 time slots match
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["availability"] == 1.0  # Perfect availability match

def test_low_match_filtered():
    """Test that low matches are filtered out"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["medical"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekday-morning"]
    }
    
    # Opportunity with completely different requirements
    opportunity = {
        "requiredSkills": ["technical"],
        "location": {"latitude": 40.7128, "longitude": -74.0060},  # NYC - very far
        "timeSlots": ["weekend-evening"]
    }
    
    matches = algorithm.rank_opportunities(volunteer, [opportunity])
    assert len(matches) == 0  # Should be filtered out for low score

def test_ranking_order():
    """Test that opportunities are ranked correctly"""
    algorithm = MatchingAlgorithm()
    
    volunteer = {
        "skills": ["teaching", "administrative"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning"]
    }
    
    # High match opportunity
    good_opp = {
        "id": "good",
        "requiredSkills": ["teaching"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},  # Same location
        "timeSlots": ["weekend-morning"]
    }
    
    # Lower match opportunity
    okay_opp = {
        "id": "okay", 
        "requiredSkills": ["teaching"],
        "location": {"latitude": 30.1444, "longitude": 31.2357},  # Bit farther
        "timeSlots": ["weekend-afternoon"]  # Different time
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
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning"]
    }
    
    opportunity = {
        "requiredSkills": ["teaching"],
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "timeSlots": ["weekend-morning"]
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    # Verify all expected components are present
    assert "distance" in score.components
    assert "skills" in score.components
    assert "availability" in score.components
    
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
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "availability": ["weekend-morning"]
    }
    
    opportunity = {
        "requiredSkills": [],  # No skills required
        "location": {"latitude": 30.0444, "longitude": 31.2357},
        "timeSlots": ["weekend-morning"]
    }
    
    score = algorithm.calculate_match_score(volunteer, opportunity)
    
    assert score.components["skills"] == 1.0  # Should get full score
    assert "No specific skills required" in score.explanation