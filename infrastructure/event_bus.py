"""
Redis Streams-based event bus for distributed cross-service communication
"""
import os
import json
import asyncio
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from uuid import uuid4
import logging

import redis.asyncio as redis
from redis.exceptions import ConnectionError, ResponseError

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Event structure for Redis Streams"""
    id: str
    type: str
    timestamp: datetime
    payload: dict
    source_service: str
    stream_id: Optional[str] = None  # Redis stream ID (auto-generated)

    def to_dict(self) -> dict:
        """Convert to dictionary for Redis"""
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "payload": json.dumps(self.payload),
            "source_service": self.source_service
        }

    @classmethod
    def from_dict(cls, data: dict, stream_id: str = None) -> 'StreamEvent':
        """Create from Redis dictionary"""
        return cls(
            id=data["id"].decode() if isinstance(data["id"], bytes) else data["id"],
            type=data["type"].decode() if isinstance(data["type"], bytes) else data["type"],
            timestamp=datetime.fromisoformat(
                data["timestamp"].decode() if isinstance(data["timestamp"], bytes) else data["timestamp"]
            ),
            payload=json.loads(
                data["payload"].decode() if isinstance(data["payload"], bytes) else data["payload"]
            ),
            source_service=data["source_service"].decode() if isinstance(data["source_service"], bytes) else data["source_service"],
            stream_id=stream_id
        )


class RedisEventBus:
    """Redis Streams-based event bus for cross-service communication"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.stream_name = os.getenv("REDIS_STREAM_NAME", "seraaj:events:global")
        self.max_entries = int(os.getenv("REDIS_MAX_ENTRIES", "10000"))
        self.connection_pool = None
        self.redis_client = None
        self._connected = False
        
    async def _ensure_connection(self) -> bool:
        """Ensure Redis connection is established"""
        if self._connected and self.redis_client:
            try:
                await self.redis_client.ping()
                return True
            except:
                self._connected = False
                
        try:
            if not self.connection_pool:
                self.connection_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=20,
                    retry_on_timeout=True
                )
            
            if not self.redis_client:
                self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info("Connected to Redis event bus")
            return True
            
        except ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Events will be handled locally.")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            self._connected = False
            return False

    async def publish(
        self, 
        event_type: str, 
        payload: dict, 
        source_service: str = "unknown"
    ) -> Optional[str]:
        """
        Publish event to Redis stream
        
        Returns:
            Stream ID if successful, None if Redis unavailable
        """
        event = StreamEvent(
            id=str(uuid4()),
            type=event_type,
            timestamp=datetime.now(UTC),
            payload=payload,
            source_service=source_service
        )
        
        # Try Redis first
        if await self._ensure_connection():
            try:
                stream_id = await self.redis_client.xadd(
                    self.stream_name,
                    event.to_dict(),
                    maxlen=self.max_entries
                )
                
                event.stream_id = stream_id.decode() if isinstance(stream_id, bytes) else stream_id
                
                logger.info(f"Published event to Redis: {event_type} from {source_service}")
                return event.stream_id
                
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")
                
        # Fallback: log the event attempt
        logger.warning(f"Redis unavailable, event not published: {event_type}")
        return None

    async def subscribe(
        self,
        group: str,
        consumer: str,
        event_types: List[str],
        handler: Callable[[StreamEvent], None],
        batch_size: int = 10
    ) -> None:
        """
        Subscribe to events with consumer group
        
        Args:
            group: Consumer group name
            consumer: Consumer name within group
            event_types: List of event types to filter
            handler: Event handler function
            batch_size: Number of events to process at once
        """
        if not await self._ensure_connection():
            logger.error("Cannot subscribe - Redis not available")
            return
            
        # Ensure consumer group exists
        await self.create_consumer_group(group)
        
        logger.info(f"Starting subscriber {consumer} in group {group} for events: {event_types}")
        
        while True:
            try:
                # Read from consumer group
                messages = await self.redis_client.xreadgroup(
                    group,
                    consumer,
                    {self.stream_name: '>'},
                    count=batch_size,
                    block=1000  # Block for 1 second
                )
                
                if not messages:
                    continue
                    
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        try:
                            event = StreamEvent.from_dict(fields, message_id.decode())
                            
                            # Filter by event type
                            if event.type in event_types:
                                await self._handle_event_safely(handler, event)
                                
                            # Acknowledge processing
                            await self.redis_client.xack(self.stream_name, group, message_id)
                            
                        except Exception as e:
                            logger.error(f"Error processing event {message_id}: {e}")
                            # Could implement dead letter queue here
                            
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(5)  # Backoff on error
                
                # Reconnect
                self._connected = False

    async def _handle_event_safely(self, handler: Callable[[StreamEvent], None], event: StreamEvent):
        """Handle event with error isolation"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Event handler error for {event.type}: {e}")

    async def create_consumer_group(self, group: str, start_id: str = "0") -> bool:
        """Create consumer group if it doesn't exist"""
        if not await self._ensure_connection():
            return False
            
        try:
            await self.redis_client.xgroup_create(
                self.stream_name,
                group,
                id=start_id,
                mkstream=True
            )
            logger.info(f"Created consumer group: {group}")
            return True
            
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists
                return True
            logger.error(f"Failed to create consumer group {group}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating group {group}: {e}")
            return False

    async def get_stream_info(self) -> dict:
        """Get stream information for monitoring"""
        if not await self._ensure_connection():
            return {"connected": False, "error": "Redis not available"}
            
        try:
            info = await self.redis_client.xinfo_stream(self.stream_name)
            return {
                "connected": True,
                "length": info[b'length'] if b'length' in info else 0,
                "first_entry": info[b'first-entry'][0].decode() if info.get(b'first-entry') else None,
                "last_entry": info[b'last-entry'][0].decode() if info.get(b'last-entry') else None,
                "groups": info[b'groups'] if b'groups' in info else 0
            }
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            return {"connected": False, "error": str(e)}

    async def get_consumer_group_info(self, group: str) -> dict:
        """Get consumer group status and lag"""
        if not await self._ensure_connection():
            return {"connected": False, "error": "Redis not available"}
            
        try:
            groups = await self.redis_client.xinfo_groups(self.stream_name)
            
            for group_info in groups:
                if group_info[b'name'].decode() == group:
                    return {
                        "connected": True,
                        "name": group,
                        "consumers": group_info[b'consumers'],
                        "pending": group_info[b'pending'],
                        "lag": group_info[b'lag'] if b'lag' in group_info else 0,
                        "last_delivered": group_info[b'last-delivered-id'].decode()
                    }
                    
            return {"connected": True, "error": f"Group {group} not found"}
            
        except Exception as e:
            logger.error(f"Error getting group info for {group}: {e}")
            return {"connected": False, "error": str(e)}

    async def get_recent_events(self, count: int = 10) -> List[StreamEvent]:
        """Get recent events from stream (for debugging/monitoring)"""
        if not await self._ensure_connection():
            return []
            
        try:
            messages = await self.redis_client.xrevrange(
                self.stream_name,
                count=count
            )
            
            events = []
            for message_id, fields in messages:
                try:
                    event = StreamEvent.from_dict(fields, message_id.decode())
                    events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing event {message_id}: {e}")
                    
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []

    async def close(self):
        """Close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        self._connected = False
        logger.info("Redis event bus connections closed")