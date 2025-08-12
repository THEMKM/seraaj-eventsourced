"""
Matching service adapter for BFF
"""
import httpx
from typing import List, Dict, Any
from fastapi import HTTPException


class MatchingAdapter:
    """HTTP client adapter for Matching service"""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30.0
    
    async def quick_match(self, volunteer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get quick match suggestions from Matching service
        Maps BFF request to Matching service format
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/quick-match",
                    params={
                        "volunteer_id": volunteer_id,
                        "limit": limit
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail="No suitable matches found for this volunteer")
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Matching service error: {response.text}")
                    
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Matching service unavailable: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error calling matching service: {str(e)}")
    
    async def get_suggestions(self, volunteer_id: str) -> List[Dict[str, Any]]:
        """
        Get existing suggestions for a volunteer from Matching service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/suggestions/{volunteer_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Return empty list if no suggestions found
                    return []
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Matching service error: {response.text}")
                    
        except httpx.RequestError as e:
            # If service is unavailable, return empty list for graceful degradation
            print(f"[WARNING] Matching service unavailable: {str(e)}")
            return []
        except HTTPException:
            raise
        except Exception as e:
            print(f"[WARNING] Error calling matching service: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Matching service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False