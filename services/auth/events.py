"""
Auth domain event publisher
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

try:
    from infrastructure.event_bus import RedisEventBus
    from infrastructure.event_types import EventTypes
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AuthEventPublisher:
    """Publishes authentication domain events to both file and Redis"""
    
    def __init__(self):
        # File-based logging (for backward compatibility)
        self.event_log = Path("data/auth_domain_events.jsonl")
        self.event_log.parent.mkdir(exist_ok=True)
        
        # Redis event bus
        self.use_redis = os.getenv("USE_REDIS_EVENTS", "true").lower() == "true"
        self.redis_bus = None
        
        if self.use_redis and REDIS_AVAILABLE:
            try:
                self.redis_bus = RedisEventBus()
            except Exception as e:
                logger.warning(f"Failed to initialize Redis event bus: {e}")
                self.redis_bus = None
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an authentication event to both file and Redis"""
        event = {
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # 1. File-based publishing (existing functionality)
        with open(self.event_log, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        # 2. Redis publishing (new functionality)
        redis_published = False
        if self.redis_bus:
            try:
                stream_id = await self.redis_bus.publish(
                    event_type,
                    data,
                    source_service="auth"
                )
                redis_published = stream_id is not None
            except Exception as e:
                logger.warning(f"Redis event publishing failed: {e}")
        
        status = "DUAL" if redis_published else "FILE"
        print(f"[AUTH-{status}] Event published: {event_type}")
    
    async def publish_user_registered(self, user_id: str, email: str, name: str, role: str):
        """Publish user registration event"""
        await self.publish(EventTypes.USER_REGISTERED, {
            "userId": user_id,
            "email": email,
            "name": name,
            "role": role,
            "registeredAt": datetime.utcnow().isoformat()
        })
    
    async def publish_user_login(self, user_id: str, email: str):
        """Publish user login event"""
        await self.publish(EventTypes.USER_LOGIN, {
            "userId": user_id,
            "email": email,
            "loginAt": datetime.utcnow().isoformat()
        })
    
    async def publish_user_password_changed(self, user_id: str):
        """Publish password change event"""
        await self.publish(EventTypes.USER_PASSWORD_CHANGED, {
            "userId": user_id,
            "changedAt": datetime.utcnow().isoformat()
        })
    
    async def close(self):
        """Close event bus connections"""
        if self.redis_bus:
            await self.redis_bus.close()