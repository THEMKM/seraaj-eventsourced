"""
Circuit Breaker Pattern Implementation for fault tolerance
"""
import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures to trigger open
    success_threshold: int = 2          # Successes needed to close from half-open
    timeout: float = 60.0              # Seconds to wait before trying half-open
    expected_exception: type = Exception  # Exception type that counts as failure


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for service calls"""
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.name = "circuit_breaker"
    
    def _should_attempt_call(self) -> bool:
        """Determine if call should be attempted based on current state"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if timeout period has elapsed
            if time.time() - self.last_failure_time >= self.config.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _record_success(self):
        """Record a successful call"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker {self.name} closed after successful recovery")
    
    def _record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} opened from HALF_OPEN after failure")
        elif (self.state == CircuitState.CLOSED and 
              self.failure_count >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection (sync version)"""
        if not self._should_attempt_call():
            raise CircuitBreakerOpenException(
                f"Circuit breaker {self.name} is OPEN. Service calls are blocked."
            )
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.expected_exception as e:
            self._record_failure()
            raise e
    
    async def acall(self, func: Callable, *args, **kwargs) -> Any:
        """Execute an async function with circuit breaker protection"""
        if not self._should_attempt_call():
            raise CircuitBreakerOpenException(
                f"Circuit breaker {self.name} is OPEN. Service calls are blocked."
            )
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.expected_exception as e:
            self._record_failure()
            raise e
    
    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        return self.state == CircuitState.HALF_OPEN
    
    def reset(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker {self.name} manually reset")
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time
        }


class ServiceCircuitBreaker(CircuitBreaker):
    """Circuit breaker specifically for service calls with HTTP exceptions"""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig = None):
        # Default config for HTTP services
        if config is None:
            config = CircuitBreakerConfig(
                failure_threshold=3,     # Lower threshold for HTTP services
                success_threshold=2,
                timeout=30.0,           # Shorter timeout for HTTP
                expected_exception=Exception  # Catch all exceptions for HTTP calls
            )
        
        super().__init__(config)
        self.name = f"{service_name}_circuit_breaker"
        self.service_name = service_name


# Circuit breaker registry for services
_circuit_breakers: dict[str, ServiceCircuitBreaker] = {}


def get_service_circuit_breaker(service_name: str) -> ServiceCircuitBreaker:
    """Get or create a circuit breaker for a service"""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = ServiceCircuitBreaker(service_name)
    return _circuit_breakers[service_name]


def get_all_circuit_breaker_status() -> dict:
    """Get status of all circuit breakers"""
    return {name: cb.get_status() for name, cb in _circuit_breakers.items()}


def reset_all_circuit_breakers():
    """Reset all circuit breakers"""
    for cb in _circuit_breakers.values():
        cb.reset()
    logger.info("All circuit breakers reset")