"""
Service-to-service authentication utilities
"""
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ServiceAuthManager:
    """Manages JWT tokens for service-to-service communication"""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.service_token_expire = timedelta(hours=1)  # Service tokens last 1 hour
        
    def generate_service_token(self, service_name: str, target_service: Optional[str] = None) -> str:
        """
        Generate a JWT token for service-to-service communication
        
        Args:
            service_name: Name of the calling service
            target_service: Name of the target service (optional)
        
        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        
        payload = {
            'service': service_name,
            'target': target_service,
            'exp': now + self.service_token_expire,
            'iat': now,
            'type': 'service',
            'iss': 'seraaj-platform'
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.debug(f"Generated service token for {service_name} -> {target_service or 'any'}")
        return token
    
    def verify_service_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a service JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Ensure it's a service token
            if payload.get('type') != 'service':
                logger.warning(f"Invalid token type: {payload.get('type')}")
                return None
                
            logger.debug(f"Verified service token from {payload.get('service')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Service token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid service token: {e}")
            return None
    
    def get_auth_header(self, service_name: str, target_service: Optional[str] = None) -> str:
        """
        Get Authorization header value for service requests
        
        Args:
            service_name: Name of the calling service
            target_service: Name of the target service (optional)
            
        Returns:
            Authorization header value (Bearer token)
        """
        token = self.generate_service_token(service_name, target_service)
        return f"Bearer {token}"
    
    def should_require_auth(self) -> bool:
        """Check if service authentication should be required"""
        return os.getenv('REQUIRE_SERVICE_AUTH', 'false').lower() == 'true'


# Global instance
service_auth_manager = ServiceAuthManager()


def get_service_auth_header(service_name: str, target_service: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get auth header if service auth is enabled
    
    Args:
        service_name: Name of the calling service
        target_service: Name of the target service (optional)
        
    Returns:
        Authorization header value if auth is required, None otherwise
    """
    if service_auth_manager.should_require_auth():
        return service_auth_manager.get_auth_header(service_name, target_service)
    return None


def verify_service_request(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Verify a service-to-service request
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Token payload if valid and required, None if not required or invalid
    """
    if not service_auth_manager.should_require_auth():
        return None  # Auth not required
        
    if not authorization or not authorization.startswith('Bearer '):
        logger.warning("Missing or invalid authorization header for service request")
        return None
        
    token = authorization.split(' ', 1)[1]
    return service_auth_manager.verify_service_token(token)