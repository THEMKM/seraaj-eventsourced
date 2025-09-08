"""
Applications service adapter for BFF with service discovery and circuit breaker
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from services.shared.models import StandardErrorResponse

from infrastructure.service_registry import ServiceRegistry, ServiceUnavailableError
from infrastructure.circuit_breaker import get_service_circuit_breaker, CircuitBreakerOpenException

logger = logging.getLogger(__name__)


class ApplicationsAdapter:
    """HTTP client adapter for Applications service with fault tolerance"""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.service_name = "applications"
        self.circuit_breaker = get_service_circuit_breaker(self.service_name)
        # Configurable HTTP timeout
        import os
        self.timeout = float(os.getenv('APPLICATIONS_HTTP_TIMEOUT', os.getenv('BFF_HTTP_TIMEOUT', '30.0')))
        
    async def _get_service_url(self) -> str:
        """Get the service URL from service discovery"""
        try:
            return await self.service_registry.get_service_url(self.service_name)
        except ServiceUnavailableError as e:
            logger.error(f"Service discovery failed for {self.service_name}: {e}")
            raise HTTPException(status_code=503, detail=f"Applications service unavailable: {e}")
    
    async def submit_application(
        self, 
        volunteer_id: str, 
        opportunity_id: str, 
        cover_letter: Optional[str] = None,
        authorization: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit application to Applications service
        Maps BFF request to Applications service format
        """
        async def _make_request():
            base_url = await self._get_service_url()
            payload = {
                "volunteerId": volunteer_id,
                "opportunityId": opportunity_id,
            }
            if cover_letter:
                payload["coverLetter"] = cover_letter
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/api/applications",
                    json=payload,
                    headers=({"Authorization": authorization} if authorization else None)
                )
                
                if response.status_code == 201:
                    return response.json()
                elif response.status_code == 400:
                    err = StandardErrorResponse(error="upstream_error", message="Invalid application data", code=400, details={"body": response.text})
                    raise HTTPException(status_code=400, detail=err.model_dump())
                elif response.status_code == 404:
                    err = StandardErrorResponse(error="not_found", message="Volunteer or opportunity not found", code=404)
                    raise HTTPException(status_code=404, detail=err.model_dump())
                elif response.status_code == 409:
                    err = StandardErrorResponse(error="conflict", message="Application already exists or opportunity is full", code=409)
                    raise HTTPException(status_code=409, detail=err.model_dump())
                else:
                    err = StandardErrorResponse(error="upstream_error", message="Applications service error", code=response.status_code, details={"body": response.text})
                    raise HTTPException(status_code=response.status_code, detail=err.model_dump())
        
        try:
            return await self.circuit_breaker.acall(_make_request)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for {self.service_name}: {e}")
            err = StandardErrorResponse(error="service_unavailable", message="Applications service temporarily unavailable", code=503)
            raise HTTPException(status_code=503, detail=err.model_dump())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Applications service call failed: {e}")
            err = StandardErrorResponse(error="service_error", message="Applications service error", code=503, details={"reason": str(e)})
            raise HTTPException(status_code=503, detail=err.model_dump())
    
    async def get_volunteer_applications(self, volunteer_id: str, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get applications for a volunteer from Applications service
        """
        async def _make_request():
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{base_url}/api/applications/volunteer/{volunteer_id}",
                    headers=({"Authorization": authorization} if authorization else None)
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Return empty list if volunteer not found
                    return []
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Applications service error: {response.text}")
        
        try:
            return await self.circuit_breaker.acall(_make_request)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for {self.service_name}, returning empty list: {e}")
            return []  # Graceful degradation
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Applications service call failed, returning empty list: {e}")
            return []  # Graceful degradation
    
    async def health_check(self) -> bool:
        """Check if Applications service is healthy"""
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def update_application_state(
        self,
        application_id: str,
        action: str,
        reason: Optional[str] = None,
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        """PATCH application state via Applications service state machine endpoint"""
        async def _make_request():
            base_url = await self._get_service_url()
            payload: Dict[str, Any] = {"action": action}
            if reason:
                payload["reason"] = reason

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{base_url}/api/applications/{application_id}/state",
                    json=payload,
                    headers=({"Authorization": authorization} if authorization else None)
                )

                if response.status_code in (200, 201):
                    return response.json()
                elif response.status_code == 400:
                    # Surface validation detail
                    raise HTTPException(status_code=400, detail=f"Invalid state transition: {response.text}")
                elif response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Application not found")
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"Applications service error: {response.text}")

        try:
            return await self.circuit_breaker.acall(_make_request)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for {self.service_name}: {e}")
            err = StandardErrorResponse(error="service_unavailable", message="Applications service temporarily unavailable", code=503)
            raise HTTPException(status_code=503, detail=err.model_dump())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Applications service call failed: {e}")
            err = StandardErrorResponse(error="service_error", message="Applications service error", code=503, details={"reason": str(e)})
            raise HTTPException(status_code=503, detail=err.model_dump())
