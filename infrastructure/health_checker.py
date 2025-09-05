"""
Health Check Chain Implementation - Dependency-aware health checking
"""
import asyncio
import logging
import time
from typing import Dict, List, Callable, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DependencyResult:
    """Result of a single dependency health check"""
    name: str
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class HealthCheckResult:
    """Complete health check result"""
    overall_status: HealthStatus
    response_time_ms: float
    dependencies: List[DependencyResult]
    timestamp: str
    service_name: str
    version: str = "1.1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "status": self.overall_status.value,
            "service": self.service_name,
            "version": self.version,
            "timestamp": self.timestamp,
            "response_time_ms": self.response_time_ms,
            "dependencies": {
                dep.name: {
                    "status": dep.status.value,
                    "response_time_ms": dep.response_time_ms,
                    "error": dep.error_message,
                    "details": dep.details
                } for dep in self.dependencies
            }
        }


class HealthChecker:
    """Dependency-aware health checker with chain propagation"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.dependencies: List[Tuple[str, Callable, Dict[str, Any]]] = []
        self._cache: Optional[HealthCheckResult] = None
        self._cache_ttl_seconds = 10  # Cache results for 10 seconds
        self._cache_timestamp = 0
        
    def add_dependency(
        self, 
        name: str, 
        check_func: Callable,
        timeout_seconds: float = 5.0,
        critical: bool = True
    ):
        """Add a dependency to check
        
        Args:
            name: Human-readable name for the dependency
            check_func: Async function that returns bool for health status
            timeout_seconds: Max time to wait for check
            critical: If True, failure causes overall UNHEALTHY status
        """
        config = {
            "timeout": timeout_seconds,
            "critical": critical
        }
        self.dependencies.append((name, check_func, config))
        logger.info(f"Added dependency '{name}' to health checker for {self.service_name}")
    
    async def _check_single_dependency(
        self, 
        name: str, 
        check_func: Callable, 
        config: Dict[str, Any]
    ) -> DependencyResult:
        """Check a single dependency with timeout and error handling"""
        start_time = time.time()
        
        try:
            # Apply timeout
            is_healthy = await asyncio.wait_for(
                check_func() if asyncio.iscoroutinefunction(check_func) else asyncio.create_task(asyncio.to_thread(check_func)),
                timeout=config["timeout"]
            )
            
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
            
            return DependencyResult(
                name=name,
                status=status,
                response_time_ms=response_time,
                details={"critical": config["critical"]}
            )
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return DependencyResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=f"Timeout after {config['timeout']}s",
                details={"critical": config["critical"]}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return DependencyResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                details={"critical": config["critical"]}
            )
    
    async def check_health(self, use_cache: bool = True) -> HealthCheckResult:
        """Perform comprehensive health check of all dependencies"""
        current_time = time.time()
        
        # Return cached result if still valid
        if (use_cache and self._cache and 
            (current_time - self._cache_timestamp) < self._cache_ttl_seconds):
            return self._cache
            
        start_time = current_time
        
        # Check all dependencies in parallel
        dependency_tasks = [
            self._check_single_dependency(name, check_func, config)
            for name, check_func, config in self.dependencies
        ]
        
        dependency_results = []
        if dependency_tasks:
            dependency_results = await asyncio.gather(*dependency_tasks, return_exceptions=True)
            
            # Handle any exceptions from gather
            for i, result in enumerate(dependency_results):
                if isinstance(result, Exception):
                    name = self.dependencies[i][0]
                    dependency_results[i] = DependencyResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=0,
                        error_message=f"Health check failed: {result}"
                    )
        
        # Determine overall status
        overall_status = self._calculate_overall_status(dependency_results)
        
        response_time = (time.time() - start_time) * 1000
        result = HealthCheckResult(
            overall_status=overall_status,
            response_time_ms=response_time,
            dependencies=dependency_results,
            timestamp=datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            service_name=self.service_name
        )
        
        # Cache the result
        self._cache = result
        self._cache_timestamp = current_time
        
        return result
    
    def _calculate_overall_status(self, dependency_results: List[DependencyResult]) -> HealthStatus:
        """Calculate overall health status based on dependency results"""
        if not dependency_results:
            return HealthStatus.HEALTHY
            
        critical_unhealthy = any(
            dep.status == HealthStatus.UNHEALTHY and dep.details.get("critical", True)
            for dep in dependency_results
        )
        
        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
            
        any_unhealthy = any(dep.status == HealthStatus.UNHEALTHY for dep in dependency_results)
        if any_unhealthy:
            return HealthStatus.DEGRADED
            
        return HealthStatus.HEALTHY
    
    def clear_cache(self):
        """Clear cached health check results"""
        self._cache = None
        self._cache_timestamp = 0


# Common dependency check functions
async def check_file_exists(file_path: str) -> bool:
    """Check if a file exists (useful for checking data files)"""
    from pathlib import Path
    return Path(file_path).exists()


async def check_http_endpoint(url: str, timeout: float = 5.0) -> bool:
    """Check if an HTTP endpoint is responding"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.status_code == 200
    except Exception:
        return False


async def check_redis_connection() -> bool:
    """Check Redis connection if available"""
    try:
        from infrastructure.event_bus import RedisEventBus
        bus = RedisEventBus()
        # Try to ensure connection (which includes ping)
        connected = await bus._ensure_connection()
        if connected:
            await bus.close()  # Clean up
        return connected
    except Exception:
        return False


async def check_retention_health() -> bool:
    """Check retention system health"""
    try:
        from infrastructure.retention_scheduler import retention_health_check
        health_result = await retention_health_check()
        return health_result["healthy"]
    except Exception:
        return False


async def check_event_store_size() -> Dict[str, Any]:
    """Check event store sizes and return retention recommendations"""
    try:
        from infrastructure.retention_manager import retention_manager
        status = await retention_manager.get_retention_status()
        
        # Check for files that need attention
        needs_attention = []
        total_size_mb = 0
        
        for filename, stats in status["file_stats"].items():
            if stats.get("exists", False):
                size_mb = stats.get("size_mb", 0)
                total_size_mb += size_mb
                old_events = stats.get("old_events_estimate", 0)
                
                if old_events > 500:  # Threshold for attention
                    needs_attention.append(f"{filename}: {old_events} old events")
        
        return {
            "healthy": len(needs_attention) < 3,  # Degraded if many files need attention
            "total_size_mb": total_size_mb,
            "files_needing_attention": len(needs_attention),
            "recommendations": needs_attention[:3]  # Limit to top 3
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}


def create_service_health_checker(service_name: str) -> HealthChecker:
    """Factory function to create a health checker for a service"""
    checker = HealthChecker(service_name)
    
    # Add common dependencies for all services
    checker.add_dependency(
        "event_store_files",
        lambda: check_file_exists("data/application_events.jsonl"),
        timeout_seconds=1.0,
        critical=False  # File missing is degraded, not unhealthy
    )
    
    # Add Redis dependency if available
    checker.add_dependency(
        "redis_event_bus",
        check_redis_connection,
        timeout_seconds=3.0,
        critical=False  # Redis failure is degraded, not unhealthy
    )
    
    # Add retention health check
    checker.add_dependency(
        "retention_scheduler",
        check_retention_health,
        timeout_seconds=2.0,
        critical=False
    )
    
    # Add event store size monitoring
    checker.add_dependency(
        "event_store_size",
        check_event_store_size,
        timeout_seconds=3.0,
        critical=False
    )
    
    # Add contract compliance monitoring
    checker.add_dependency(
        "contract_compliance",
        check_contract_compliance,
        timeout_seconds=2.0,
        critical=False
    )
    
    return checker


async def check_contract_compliance() -> Dict[str, Any]:
    """Check contract compliance monitoring health"""
    try:
        from infrastructure.contract_monitor import contract_compliance_health_check
        health_result = await contract_compliance_health_check()
        return health_result
    except Exception as e:
        return {"healthy": False, "error": str(e)}