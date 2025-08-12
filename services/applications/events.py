"""
Event publishing and event store for Applications service
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4
import logging

try:
    from infrastructure.event_bus import RedisEventBus
    from infrastructure.event_types import EventTypes
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes domain events to both file-based store and Redis event bus"""
    
    def __init__(self, data_dir: str = "data", use_redis: bool = None):
        # File-based event store (for backward compatibility)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.event_log = self.data_dir / "application_events.jsonl"
        
        # Redis event bus (for cross-service communication)
        self.use_redis = use_redis if use_redis is not None else os.getenv("USE_REDIS_EVENTS", "true").lower() == "true"
        self.redis_bus = None
        
        if self.use_redis and REDIS_AVAILABLE:
            try:
                self.redis_bus = RedisEventBus()
            except Exception as e:
                logger.warning(f"Failed to initialize Redis event bus: {e}")
                self.redis_bus = None
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to both file store and Redis (dual publishing)"""
        event = {
            "eventId": str(uuid4()),
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # 1. File-based publishing (existing functionality)
        with open(self.event_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        # 2. Redis publishing (new functionality)
        redis_published = False
        if self.redis_bus:
            try:
                stream_id = await self.redis_bus.publish(
                    event_type,
                    data,
                    source_service="applications"
                )
                redis_published = stream_id is not None
            except Exception as e:
                logger.warning(f"Redis event publishing failed: {e}")
        
        status = "DUAL" if redis_published else "FILE"
        print(f"[EVENT-{status}] Published event: {event_type}")
        return event
    
    # Convenience methods using standard event types
    async def publish_application_created(self, application_data: Dict[str, Any]):
        """Publish application created event"""
        return await self.publish(EventTypes.APPLICATION_CREATED, application_data)
    
    async def publish_application_submitted(self, application_data: Dict[str, Any]):
        """Publish application submitted event"""
        return await self.publish(EventTypes.APPLICATION_SUBMITTED, {
            "applicationId": application_data.get("id"),
            "volunteerId": application_data.get("volunteerId"), 
            "organizationId": application_data.get("organizationId"),
            "opportunityId": application_data.get("opportunityId"),
            "submittedAt": application_data.get("submittedAt", datetime.utcnow().isoformat()),
            "details": application_data
        })
    
    async def publish_application_state_changed(self, application_id: str, old_state: str, new_state: str, details: Dict[str, Any] = None):
        """Publish application state change event"""
        return await self.publish(EventTypes.APPLICATION_STATE_CHANGED, {
            "applicationId": application_id,
            "oldState": old_state,
            "newState": new_state,
            "changedAt": datetime.utcnow().isoformat(),
            "details": details or {}
        })
    
    async def publish_application_completed(self, application_data: Dict[str, Any]):
        """Publish application completed event"""
        return await self.publish(EventTypes.APPLICATION_COMPLETED, {
            "applicationId": application_data.get("id"),
            "volunteerId": application_data.get("volunteerId"),
            "organizationId": application_data.get("organizationId"),
            "completedAt": datetime.utcnow().isoformat(),
            "details": application_data
        })
    
    async def close(self):
        """Close event bus connections"""
        if self.redis_bus:
            await self.redis_bus.close()