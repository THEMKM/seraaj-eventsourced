"""
Applications service adapter for BFF
"""
import httpx
from typing import List, Dict, Any, Optional
from fastapi import HTTPException


class ApplicationsAdapter:
    """HTTP client adapter for Applications service"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30.0
    
    async def submit_application(
        self, 
        volunteer_id: str, 
        opportunity_id: str, 
        cover_letter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit application to Applications service
        Maps BFF request to Applications service format
        """
        try:
            payload = {
                "volunteerId": volunteer_id,
                "opportunityId": opportunity_id,
            }
            if cover_letter:
                payload["coverLetter"] = cover_letter
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/applications",
                    json=payload
                )
                
                if response.status_code == 201:
                    return response.json()
                elif response.status_code == 400:
                    raise HTTPException(status_code=400, detail=f"Invalid application data: {response.text}")
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Volunteer or opportunity not found")
                elif response.status_code == 409:
                    raise HTTPException(status_code=409, detail="Application already exists or opportunity is full")
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Applications service error: {response.text}")
                    
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Applications service unavailable: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error calling applications service: {str(e)}")
    
    async def get_volunteer_applications(self, volunteer_id: str) -> List[Dict[str, Any]]:
        """
        Get applications for a volunteer from Applications service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/applications/volunteer/{volunteer_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Return empty list if volunteer not found
                    return []
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Applications service error: {response.text}")
                    
        except httpx.RequestError as e:
            # If service is unavailable, return empty list for graceful degradation
            print(f"[WARNING] Applications service unavailable: {str(e)}")
            return []
        except HTTPException:
            raise
        except Exception as e:
            print(f"[WARNING] Error calling applications service: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Applications service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False