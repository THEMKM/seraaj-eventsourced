"""
Matching service adapter for BFF with service discovery and circuit breaker
"""
import httpx
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from services.shared.models import StandardErrorResponse

from infrastructure.service_registry import ServiceRegistry, ServiceUnavailableError
from infrastructure.circuit_breaker import get_service_circuit_breaker, CircuitBreakerOpenException

logger = logging.getLogger(__name__)


class MatchingAdapter:
    """HTTP client adapter for Matching service with fault tolerance"""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.service_name = "matching"
        self.circuit_breaker = get_service_circuit_breaker(self.service_name)
        import os
        self.timeout = float(os.getenv('MATCHING_HTTP_TIMEOUT', os.getenv('BFF_HTTP_TIMEOUT', '30.0')))
        
    async def _get_service_url(self) -> str:
        """Get the service URL from service discovery"""
        try:
            return await self.service_registry.get_service_url(self.service_name)
        except ServiceUnavailableError as e:
            logger.error(f"Service discovery failed for {self.service_name}: {e}")
            raise HTTPException(status_code=503, detail=f"Matching service unavailable: {e}")
    
    async def quick_match(self, volunteer_id: str, limit: int = 10, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get quick match suggestions from Matching service
        Maps BFF request to Matching service format
        """
        async def _make_request():
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/quick-match",
                    params={
                        "volunteer_id": volunteer_id,
                        "limit": limit
                    },
                    headers=({"Authorization": authorization} if authorization else None)
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    err = StandardErrorResponse(error="not_found", message="No suitable matches found for this volunteer", code=404)
                    raise HTTPException(status_code=404, detail=err.model_dump())
                else:
                    err = StandardErrorResponse(error="upstream_error", message="Matching service error", code=response.status_code, details={"body": response.text})
                    raise HTTPException(status_code=response.status_code, detail=err.model_dump())
        
        try:
            return await self.circuit_breaker.acall(_make_request)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for {self.service_name}: {e}")
            err = StandardErrorResponse(error="service_unavailable", message="Matching service temporarily unavailable", code=503)
            raise HTTPException(status_code=503, detail=err.model_dump())
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Matching service call failed: {e}")
            err = StandardErrorResponse(error="service_error", message="Matching service error", code=503, details={"reason": str(e)})
            raise HTTPException(status_code=503, detail=err.model_dump())
    
    async def get_suggestions(self, volunteer_id: str, authorization: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get existing suggestions for a volunteer from Matching service
        """
        async def _make_request():
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{base_url}/suggestions/{volunteer_id}",
                    headers=({"Authorization": authorization} if authorization else None)
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Return empty list if no suggestions found
                    return []
                else:
                    err = StandardErrorResponse(error="upstream_error", message="Matching service error", code=response.status_code, details={"body": response.text})
                    raise HTTPException(status_code=response.status_code, detail=err.model_dump())
        
        try:
            return await self.circuit_breaker.acall(_make_request)
        except CircuitBreakerOpenException as e:
            logger.warning(f"Circuit breaker open for {self.service_name}, returning empty list: {e}")
            return []  # Graceful degradation
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Matching service call failed, returning empty list: {e}")
            return []  # Graceful degradation
    
    async def health_check(self) -> bool:
        """Check if Matching service is healthy"""
        try:
            base_url = await self._get_service_url()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
