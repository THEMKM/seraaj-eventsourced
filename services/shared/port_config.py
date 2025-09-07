"""
Centralized Service Port Configuration
Manages dynamic port assignment with environment variable support
"""
import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    default_port: int
    default_host: str = "localhost"
    environment_port_var: Optional[str] = None
    environment_host_var: Optional[str] = None


class PortConfigManager:
    """Manages port configuration for all services"""
    
    # Default service configurations
    SERVICE_CONFIGS = {
        "applications": ServiceConfig(
            name="applications",
            default_port=8001,
            environment_port_var="APPLICATIONS_SERVICE_PORT",
            environment_host_var="APPLICATIONS_SERVICE_HOST"
        ),
        "matching": ServiceConfig(
            name="matching", 
            default_port=8003,
            environment_port_var="MATCHING_SERVICE_PORT",
            environment_host_var="MATCHING_SERVICE_HOST"
        ),
        "auth": ServiceConfig(
            name="auth",
            default_port=8004,
            environment_port_var="AUTH_SERVICE_PORT", 
            environment_host_var="AUTH_SERVICE_HOST"
        ),
        "volunteers": ServiceConfig(
            name="volunteers",
            default_port=8005,
            environment_port_var="VOLUNTEERS_SERVICE_PORT",
            environment_host_var="VOLUNTEERS_SERVICE_HOST"
        ),
        "opportunities": ServiceConfig(
            name="opportunities",
            default_port=8006,
            environment_port_var="OPPORTUNITIES_SERVICE_PORT",
            environment_host_var="OPPORTUNITIES_SERVICE_HOST"
        ),
        "organizations": ServiceConfig(
            name="organizations",
            default_port=8007,
            environment_port_var="ORGANIZATIONS_SERVICE_PORT",
            environment_host_var="ORGANIZATIONS_SERVICE_HOST"
        ),
        "bff": ServiceConfig(
            name="bff",
            default_port=8000,
            default_host="0.0.0.0",  # BFF binds to all interfaces
            environment_port_var="BFF_SERVICE_PORT",
            environment_host_var="BFF_SERVICE_HOST"
        )
    }
    
    @classmethod
    def get_service_config(cls, service_name: str) -> ServiceConfig:
        """Get configuration for a service"""
        if service_name not in cls.SERVICE_CONFIGS:
            logger.warning(f"Unknown service '{service_name}', using default config")
            return ServiceConfig(
                name=service_name,
                default_port=8000,
                environment_port_var=f"{service_name.upper()}_SERVICE_PORT",
                environment_host_var=f"{service_name.upper()}_SERVICE_HOST"
            )
        
        return cls.SERVICE_CONFIGS[service_name]
    
    @classmethod
    def get_port(cls, service_name: str) -> int:
        """Get the port for a service from environment or default"""
        config = cls.get_service_config(service_name)
        
        # Try generic SERVICE_PORT first
        port_str = os.getenv("SERVICE_PORT")
        if port_str:
            try:
                port = int(port_str)
                logger.info(f"Using generic SERVICE_PORT={port} for {service_name}")
                return port
            except ValueError:
                logger.warning(f"Invalid SERVICE_PORT value: {port_str}")
        
        # Try service-specific port
        if config.environment_port_var:
            port_str = os.getenv(config.environment_port_var)
            if port_str:
                try:
                    port = int(port_str)
                    logger.info(f"Using {config.environment_port_var}={port} for {service_name}")
                    return port
                except ValueError:
                    logger.warning(f"Invalid {config.environment_port_var} value: {port_str}")
        
        # Use default
        logger.info(f"Using default port {config.default_port} for {service_name}")
        return config.default_port
    
    @classmethod
    def get_host(cls, service_name: str) -> str:
        """Get the host for a service from environment or default"""
        config = cls.get_service_config(service_name)
        
        # Try generic SERVICE_HOST first
        host = os.getenv("SERVICE_HOST")
        if host:
            logger.info(f"Using generic SERVICE_HOST={host} for {service_name}")
            return host
        
        # Try service-specific host
        if config.environment_host_var:
            host = os.getenv(config.environment_host_var)
            if host:
                logger.info(f"Using {config.environment_host_var}={host} for {service_name}")
                return host
        
        # Use default
        logger.info(f"Using default host {config.default_host} for {service_name}")
        return config.default_host
    
    @classmethod
    def get_service_url(cls, service_name: str, protocol: str = "http") -> str:
        """Get the full URL for a service"""
        host = cls.get_host(service_name)
        port = cls.get_port(service_name)
        return f"{protocol}://{host}:{port}"
    
    @classmethod
    def get_all_service_urls(cls) -> Dict[str, str]:
        """Get URLs for all configured services"""
        return {
            name: cls.get_service_url(name)
            for name in cls.SERVICE_CONFIGS.keys()
        }
    
    @classmethod
    def validate_port_conflicts(cls) -> Dict[str, str]:
        """Check for port conflicts between services"""
        port_map = {}
        conflicts = {}
        
        for service_name in cls.SERVICE_CONFIGS.keys():
            port = cls.get_port(service_name)
            host = cls.get_host(service_name)
            
            key = f"{host}:{port}"
            if key in port_map:
                conflicts[key] = f"Conflict between {port_map[key]} and {service_name}"
            else:
                port_map[key] = service_name
        
        return conflicts
    
    @classmethod
    def print_service_configuration(cls):
        """Print current service configuration for debugging"""
        print("\n=== Service Configuration ===")
        for service_name in sorted(cls.SERVICE_CONFIGS.keys()):
            config = cls.get_service_config(service_name)
            host = cls.get_host(service_name)
            port = cls.get_port(service_name)
            url = cls.get_service_url(service_name)
            
            print(f"{service_name:>12}: {url}")
            
            # Show environment variable sources if used
            env_vars = []
            if config.environment_port_var and os.getenv(config.environment_port_var):
                env_vars.append(f"port from {config.environment_port_var}")
            if config.environment_host_var and os.getenv(config.environment_host_var):
                env_vars.append(f"host from {config.environment_host_var}")
            if os.getenv("SERVICE_PORT") or os.getenv("SERVICE_HOST"):
                env_vars.append("using generic SERVICE_* vars")
                
            if env_vars:
                print(f"{'':>15}({', '.join(env_vars)})")
        
        # Check for conflicts
        conflicts = cls.validate_port_conflicts()
        if conflicts:
            print("\nPORT CONFLICTS DETECTED:")
            for address, conflict in conflicts.items():
                print(f"  {address}: {conflict}")
        else:
            print("\nNo port conflicts detected")
        
        print("=" * 30)


def get_service_startup_config(service_name: str) -> tuple[str, int]:
    """
    Get host and port for service startup
    
    Returns:
        tuple: (host, port) for uvicorn.run()
    """
    manager = PortConfigManager()
    host = manager.get_host(service_name)
    port = manager.get_port(service_name)
    
    return host, port


# For backward compatibility
def get_port(service_name: str) -> int:
    """Get port for a service (backward compatibility)"""
    return PortConfigManager.get_port(service_name)


def get_host(service_name: str) -> str:
    """Get host for a service (backward compatibility)"""
    return PortConfigManager.get_host(service_name)


# Environment validation on import
def _validate_environment():
    """Validate environment configuration on import"""
    conflicts = PortConfigManager.validate_port_conflicts()
    if conflicts:
        logger.warning("Service port conflicts detected:")
        for address, conflict in conflicts.items():
            logger.warning(f"  {address}: {conflict}")


# Run validation
_validate_environment()