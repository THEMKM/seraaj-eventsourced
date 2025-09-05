"""
Service Discovery Registry for dynamic service URL resolution
"""
import asyncio
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

@dataclass
class ServiceInfo:
    """Service information for registry"""
    name: str
    host: str
    port: int
    health_endpoint: str = None
    status: str = 'unknown'
    last_check: float = 0
    
    def __post_init__(self):
        if self.health_endpoint is None:
            self.health_endpoint = f"http://{self.host}:{self.port}/health"


class ServiceUnavailableError(Exception):
    """Raised when a service is not available"""
    pass


class ServiceRegistry:
    """Dynamic service registry with health checking"""
    
    def __init__(self, health_check_timeout: float = 2.0, check_interval: float = 30.0):
        self.services: Dict[str, ServiceInfo] = {}
        self.health_check_timeout = health_check_timeout
        self.check_interval = check_interval
        self._health_check_task = None
        
    def register_service(self, name: str, host: str, port: int, health_endpoint: str = None):
        """Register a service in the registry"""
        service = ServiceInfo(
            name=name,
            host=host, 
            port=port,
            health_endpoint=health_endpoint
        )
        self.services[name] = service
        logger.info(f"Registered service: {name} at {host}:{port}")
        
    def register_default_services(self):
        """Register default services with standard ports"""
        default_services = [
            ("applications", "localhost", 8001),
            ("matching", "localhost", 8003), 
            ("auth", "localhost", 8004),
            ("volunteers", "localhost", 8005),
            ("opportunities", "localhost", 8006),
            ("organizations", "localhost", 8007)
        ]
        
        for name, host, port in default_services:
            self.register_service(name, host, port)
    
    async def get_service_url(self, service_name: str) -> str:
        """Get service URL with health check"""
        service = self.services.get(service_name)
        if not service:
            raise ServiceUnavailableError(f"Service '{service_name}' not registered")
            
        # Check if service is healthy
        is_healthy = await self.check_health(service)
        if not is_healthy:
            raise ServiceUnavailableError(f"Service '{service_name}' is not healthy")
            
        return f"http://{service.host}:{service.port}"
    
    async def check_health(self, service: ServiceInfo) -> bool:
        """Check if a service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=self.health_check_timeout) as client:
                response = await client.get(service.health_endpoint)
                is_healthy = response.status_code == 200
                service.status = 'healthy' if is_healthy else 'unhealthy'
                return is_healthy
        except Exception as e:
            logger.debug(f"Health check failed for {service.name}: {e}")
            service.status = 'unhealthy'
            return False
    
    async def health_check_all(self):
        """Check health of all registered services"""
        tasks = []
        for service in self.services.values():
            tasks.append(self.check_health(service))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_healthy_services(self) -> List[str]:
        """Get list of healthy service names"""
        return [name for name, service in self.services.items() if service.status == 'healthy']
    
    def get_service_status(self) -> Dict[str, str]:
        """Get status of all services"""
        return {name: service.status for name, service in self.services.items()}
    
    async def start_health_monitor(self):
        """Start background health monitoring"""
        if self._health_check_task and not self._health_check_task.done():
            return
            
        async def monitor():
            while True:
                try:
                    await self.health_check_all()
                    await asyncio.sleep(self.check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
                    await asyncio.sleep(5)  # Brief pause on error
        
        self._health_check_task = asyncio.create_task(monitor())
        logger.info("Started service health monitoring")
    
    async def stop_health_monitor(self):
        """Stop background health monitoring"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped service health monitoring")


# Global registry instance
service_registry = ServiceRegistry()