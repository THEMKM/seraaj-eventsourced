#!/usr/bin/env python3
"""
Service Health Aggregator for CI/CD Pipeline

Validates that all services are healthy before deployment.
Provides comprehensive health checking across the entire system.
"""

import asyncio
import httpx
import json
import time
import sys
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"

@dataclass
class ServiceHealth:
    name: str
    url: str
    status: HealthStatus
    response_time_ms: Optional[int] = None
    error: Optional[str] = None
    details: Optional[Dict] = None

class HealthAggregator:
    """Aggregate health status from multiple services"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def check_service_health(self, name: str, url: str) -> ServiceHealth:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            logger.debug(f"Checking health of {name} at {url}")
            response = await self.client.get(url)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                try:
                    details = response.json()
                    return ServiceHealth(
                        name=name,
                        url=url,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time_ms,
                        details=details
                    )
                except json.JSONDecodeError:
                    return ServiceHealth(
                        name=name,
                        url=url,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time_ms
                    )
            else:
                return ServiceHealth(
                    name=name,
                    url=url,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}"
                )
                
        except httpx.TimeoutException:
            response_time_ms = int((time.time() - start_time) * 1000)
            return ServiceHealth(
                name=name,
                url=url,
                status=HealthStatus.TIMEOUT,
                response_time_ms=response_time_ms,
                error="Request timeout"
            )
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            return ServiceHealth(
                name=name,
                url=url,
                status=HealthStatus.UNKNOWN,
                response_time_ms=response_time_ms,
                error=str(e)
            )
    
    async def check_all_services(self, services: Dict[str, str]) -> List[ServiceHealth]:
        """Check health of all services concurrently"""
        logger.info(f"Checking health of {len(services)} services...")
        
        tasks = [
            self.check_service_health(name, url)
            for name, url in services.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(services.keys())[i]
                service_url = list(services.values())[i]
                health_results.append(ServiceHealth(
                    name=service_name,
                    url=service_url,
                    status=HealthStatus.UNKNOWN,
                    error=str(result)
                ))
            else:
                health_results.append(result)
        
        return health_results
    
    async def wait_for_services(self, services: Dict[str, str], max_wait: int = 120) -> bool:
        """Wait for all services to become healthy"""
        logger.info(f"Waiting up to {max_wait}s for all services to become healthy...")
        
        start_time = time.time()
        attempt = 1
        
        while time.time() - start_time < max_wait:
            logger.info(f"Health check attempt {attempt}")
            
            health_results = await self.check_all_services(services)
            
            # Check if all services are healthy
            healthy_services = [h for h in health_results if h.status == HealthStatus.HEALTHY]
            unhealthy_services = [h for h in health_results if h.status != HealthStatus.HEALTHY]
            
            logger.info(f"Healthy: {len(healthy_services)}, Unhealthy: {len(unhealthy_services)}")
            
            if not unhealthy_services:
                logger.info("✅ All services are healthy!")
                return True
            
            # Log unhealthy services
            for service in unhealthy_services:
                logger.warning(f"❌ {service.name}: {service.status.value} - {service.error or 'Unknown error'}")
            
            # Wait before next attempt
            if time.time() - start_time < max_wait:
                wait_time = min(10, max_wait - (time.time() - start_time))
                logger.info(f"Waiting {wait_time:.1f}s before next attempt...")
                await asyncio.sleep(wait_time)
                attempt += 1
        
        logger.error("❌ Timeout waiting for services to become healthy")
        return False
    
    def generate_health_report(self, health_results: List[ServiceHealth]) -> Dict:
        """Generate comprehensive health report"""
        healthy_count = sum(1 for h in health_results if h.status == HealthStatus.HEALTHY)
        total_count = len(health_results)
        
        overall_status = "healthy" if healthy_count == total_count else "degraded"
        
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "overall_status": overall_status,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": {}
        }
        
        for health in health_results:
            service_report = {
                "status": health.status.value,
                "response_time_ms": health.response_time_ms,
                "url": health.url
            }
            
            if health.error:
                service_report["error"] = health.error
            
            if health.details:
                service_report["details"] = health.details
            
            report["services"][health.name] = service_report
        
        return report
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main health checking function"""
    # Define services to check
    services = {
        "applications": "http://127.0.0.1:8001/health",
        "matching": "http://127.0.0.1:8002/health", 
        "auth": "http://127.0.0.1:8004/health",
        "bff": "http://127.0.0.1:8000/api/health"
    }
    
    # Override with environment variables if provided
    import os
    base_urls = {
        "applications": os.getenv("APPLICATIONS_URL", "http://127.0.0.1:8001"),
        "matching": os.getenv("MATCHING_URL", "http://127.0.0.1:8002"),
        "auth": os.getenv("AUTH_URL", "http://127.0.0.1:8004"),
        "bff": os.getenv("BFF_URL", "http://127.0.0.1:8000")
    }
    
    services = {
        "applications": f"{base_urls['applications']}/health",
        "matching": f"{base_urls['matching']}/health",
        "auth": f"{base_urls['auth']}/health", 
        "bff": f"{base_urls['bff']}/api/health"
    }
    
    aggregator = HealthAggregator(timeout=15)
    
    try:
        # Check if we should wait for services or just check once
        wait_for_healthy = os.getenv("WAIT_FOR_HEALTHY", "false").lower() == "true"
        
        if wait_for_healthy:
            # Wait for all services to become healthy
            all_healthy = await aggregator.wait_for_services(services, max_wait=180)
            if not all_healthy:
                logger.error("Not all services became healthy in time")
                sys.exit(1)
        else:
            # Single health check
            health_results = await aggregator.check_all_services(services)
            
            # Generate and display report
            report = aggregator.generate_health_report(health_results)
            
            print(json.dumps(report, indent=2))
            
            # Log summary
            logger.info(f"Health check summary: {report['healthy_services']}/{report['total_services']} services healthy")
            
            # Exit with appropriate code
            if report['overall_status'] == 'healthy':
                logger.info("✅ All services are healthy")
                sys.exit(0)
            else:
                logger.error("❌ Some services are unhealthy")
                sys.exit(1)
    
    finally:
        await aggregator.close()

if __name__ == "__main__":
    asyncio.run(main())