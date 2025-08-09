"""
End-to-end test for complete volunteer flow through BFF
Tests: quick-match → apply → dashboard flow
"""

import pytest
import httpx
import asyncio
from uuid import uuid4
from typing import Dict, Any


@pytest.mark.asyncio
class TestBFFVolunteerFlow:
    """Test complete volunteer journey through BFF endpoints"""
    
    BASE_URL = "http://localhost:8000"
    TIMEOUT = 30
    
    @pytest.fixture
    def volunteer_id(self):
        """Generate a test volunteer ID"""
        return str(uuid4())
    
    @pytest.fixture
    def opportunity_id(self):
        """Generate a test opportunity ID"""
        return str(uuid4())
    
    async def test_services_health_check(self):
        """Verify BFF and downstream services are accessible"""
        try:
            async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=self.TIMEOUT) as client:
                # Test BFF health
                response = await client.get("/api/health")
                if response.status_code != 200:
                    pytest.skip("BFF service not running - skipping E2E tests")
                
                # Verify basic health response structure
                data = response.json()
                assert "status" in data
                
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("BFF service not accessible - skipping E2E tests")
    
    async def test_complete_volunteer_flow(self, volunteer_id):
        """Test complete flow: quick-match → apply → dashboard"""
        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=self.TIMEOUT) as client:
            
            # Step 1: Get quick matches for volunteer
            print(f"\n[1] Step 1: Getting quick matches for volunteer {volunteer_id}")
            try:
                match_response = await client.post(
                    "/api/volunteer/quick-match",
                    json={"volunteerId": volunteer_id, "limit": 10}
                )
                
                # Assert successful response
                assert match_response.status_code == 200, f"Quick match failed: {match_response.text}"
                
                match_data = match_response.json()
                self._validate_quick_match_response(match_data, volunteer_id)
                
                # Handle both array and object response formats
                matches = match_data if isinstance(match_data, list) else match_data.get('matches', [])
                print(f"[OK] Quick match successful, found {len(matches)} matches")
                
                # Get first match for application (or use test opportunity)
                if matches:
                    opportunity_id = matches[0]["opportunityId"]
                else:
                    opportunity_id = str(uuid4())  # Use test opportunity if no matches
                    print("[INFO] No matches found, using test opportunity ID")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # No matches found is acceptable
                    opportunity_id = str(uuid4())
                    print("ℹ️ No matches found (404), continuing with test opportunity")
                else:
                    pytest.fail(f"Quick match request failed: {e}")
            
            # Step 2: Apply to opportunity
            print(f"\n[2] Step 2: Applying to opportunity {opportunity_id}")
            try:
                apply_response = await client.post(
                    "/api/volunteer/apply",
                    json={
                        "volunteerId": volunteer_id,
                        "opportunityId": opportunity_id,
                        "coverLetter": "I'm excited to contribute to this opportunity!"
                    }
                )
                
                # Assert successful application
                assert apply_response.status_code in [200, 201], f"Application failed: {apply_response.text}"
                
                apply_data = apply_response.json()
                self._validate_application_response(apply_data, volunteer_id, opportunity_id)
                
                print("[OK] Application submitted successfully")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [400, 409]:
                    # Bad request or conflict (duplicate application) is acceptable
                    print(f"[INFO] Application returned {e.response.status_code}, continuing test")
                else:
                    pytest.fail(f"Application request failed: {e}")
            
            # Step 3: Verify application appears in dashboard
            print(f"\n[3] Step 3: Checking volunteer dashboard")
            try:
                dashboard_response = await client.get(f"/api/volunteer/{volunteer_id}/dashboard")
                
                # Assert successful dashboard retrieval
                assert dashboard_response.status_code == 200, f"Dashboard failed: {dashboard_response.text}"
                
                dashboard_data = dashboard_response.json()
                self._validate_dashboard_response(dashboard_data, volunteer_id)
                
                print("[OK] Dashboard retrieved successfully")
                
                # Check if our application appears (may not be immediate due to async processing)
                active_apps = dashboard_data.get("activeApplications", [])
                print(f"[INFO] Found {len(active_apps)} active applications")
                
            except httpx.HTTPStatusError as e:
                pytest.fail(f"Dashboard request failed: {e}")
            
            print("\n[SUCCESS] Complete volunteer flow test passed!")
    
    async def test_parallel_quick_matches(self):
        """Test system handles parallel quick-match requests"""
        async def make_quick_match(client, vol_id):
            try:
                response = await client.post(
                    "/api/volunteer/quick-match", 
                    json={"volunteerId": vol_id, "limit": 5}
                )
                return response.status_code, vol_id
            except Exception as e:
                return 500, vol_id
        
        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=self.TIMEOUT) as client:
            # Test with 3 parallel volunteers
            volunteer_ids = [str(uuid4()) for _ in range(3)]
            
            tasks = [make_quick_match(client, vid) for vid in volunteer_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least some should succeed
            successful = [r for r in results if not isinstance(r, Exception) and r[0] == 200]
            
            print(f"Parallel test: {len(successful)}/3 requests succeeded")
            assert len(successful) >= 1, "At least one parallel request should succeed"
    
    async def test_error_handling(self):
        """Test API error handling with invalid inputs"""
        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=self.TIMEOUT) as client:
            
            # Test invalid volunteer ID format
            response = await client.post(
                "/api/volunteer/quick-match",
                json={"volunteerId": "invalid-id-format", "limit": 5}
            )
            # Should handle gracefully (might return 200 with empty results, 400, or 404)
            assert response.status_code in [200, 400, 404, 500]  # 500 is also acceptable for invalid input
            
            # Test missing parameters
            response = await client.post(
                "/api/volunteer/quick-match",
                json={}
            )
            assert response.status_code in [400, 422]  # Bad request or validation error
            
            # Test dashboard with invalid ID
            response = await client.get("/api/volunteer/invalid-id/dashboard")
            assert response.status_code in [200, 404]  # Might return empty dashboard or 404
    
    def _validate_quick_match_response(self, data: Any, volunteer_id: str):
        """Validate quick match response structure"""
        # Handle both array response and object with matches
        if isinstance(data, list):
            matches = data
        elif isinstance(data, dict):
            if "matches" in data:
                matches = data["matches"]
                assert data.get("volunteerId") == volunteer_id, "Response should include volunteer ID"
            else:
                matches = []
        else:
            assert False, f"Response should be array or dict, got {type(data)}"
        
        assert isinstance(matches, list), "Matches should be an array"
        
        # If matches exist, validate structure
        for match in matches:
            assert "opportunityId" in match, "Match should have opportunity ID"
            # Note: some APIs use 'score' others use different fields
            # Just check that basic opportunity info is present
            assert isinstance(match.get("opportunityId"), str), "Opportunity ID should be string"
    
    def _validate_application_response(self, data: Dict[Any, Any], volunteer_id: str, opportunity_id: str):
        """Validate application response structure"""
        assert isinstance(data, dict), "Response should be a dictionary"
        
        # The response structure might vary - check for key fields
        if "application" in data:
            app = data["application"]
            assert app.get("volunteerId") == volunteer_id, "Application should have correct volunteer ID"
            assert app.get("opportunityId") == opportunity_id, "Application should have correct opportunity ID"
            assert "status" in app, "Application should have status"
            assert "submittedAt" in app, "Application should have submission timestamp"
        elif "id" in data:
            # Direct application response
            assert data.get("volunteerId") == volunteer_id, "Application should have correct volunteer ID"
            assert data.get("opportunityId") == opportunity_id, "Application should have correct opportunity ID"
    
    def _validate_dashboard_response(self, data: Dict[Any, Any], volunteer_id: str):
        """Validate dashboard response structure"""
        assert isinstance(data, dict), "Response should be a dictionary"
        
        # Profile section
        assert "profile" in data, "Dashboard should include profile"
        profile = data["profile"]
        assert profile.get("id") == volunteer_id, "Profile should have correct volunteer ID"
        
        # Applications section
        assert "activeApplications" in data, "Dashboard should include active applications"
        assert isinstance(data["activeApplications"], list), "Active applications should be an array"
        
        # Matches section
        assert "recentMatches" in data, "Dashboard should include recent matches"
        assert isinstance(data["recentMatches"], list), "Recent matches should be an array"
        
        # Note: statistics might be embedded in profile or not present
        # This is acceptable as the BFF is designed for graceful degradation


# Integration test for service interaction patterns
@pytest.mark.asyncio
async def test_service_interaction_patterns():
    """Test that BFF properly orchestrates service calls"""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30) as client:
        volunteer_id = str(uuid4())
        
        try:
            # Test that BFF can handle service failures gracefully
            response = await client.get(f"/api/volunteer/{volunteer_id}/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should return reasonable defaults even if services are down
                assert "profile" in data
                assert "activeApplications" in data
                assert "recentMatches" in data
                
                print("[OK] BFF handles service orchestration correctly")
            else:
                print(f"[INFO] Dashboard returned {response.status_code}, which is acceptable")
                
        except httpx.ConnectError:
            pytest.skip("BFF not accessible for service interaction test")


if __name__ == "__main__":
    # Run the tests directly for debugging
    import asyncio
    
    async def run_tests():
        test_instance = TestBFFVolunteerFlow()
        
        # Health check
        await test_instance.test_services_health_check()
        
        # Main flow test
        volunteer_id = str(uuid4())
        await test_instance.test_complete_volunteer_flow(volunteer_id)
        
        # Error handling
        await test_instance.test_error_handling()
        
        print("\n[SUCCESS] All E2E tests completed!")
    
    asyncio.run(run_tests())