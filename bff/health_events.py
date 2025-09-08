"""
BFF Health Events - Monitor service health via Redis event bus
"""
import asyncio
import logging
from datetime import datetime, UTC
from typing import Dict, Any, List
from fastapi import APIRouter

from infrastructure.event_bus import RedisEventBus, StreamEvent
from infrastructure.event_types import EventTypes

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthEventMonitor:
    """Monitor service health via Redis event bus"""
    
    def __init__(self):
        self.event_bus = RedisEventBus()
        self.service_status = {
            "applications": {"status": "unknown", "last_seen": None},
            "matching": {"status": "unknown", "last_seen": None},
            "auth": {"status": "unknown", "last_seen": None}
        }
        self.is_monitoring = False
        
    async def start_monitoring(self):
        """Start monitoring service health events"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        logger.info("Starting health event monitoring")
        
        # Create consumer group for BFF health monitoring
        await self.event_bus.create_consumer_group("bff-health")
        
        # Start monitoring task
        asyncio.create_task(self._monitor_health_events())
        
    async def _monitor_health_events(self):
        """Monitor health-related events from all services"""
        try:
            await self.event_bus.subscribe(
                group="bff-health",
                consumer="health-monitor-1",
                event_types=[
                    EventTypes.SERVICE_STARTED,
                    EventTypes.SERVICE_STOPPED,
                    EventTypes.SERVICE_HEALTH_CHECK,
                    EventTypes.APPLICATION_SUBMITTED,  # Applications service is alive
                    EventTypes.MATCH_SUGGESTIONS_GENERATED,  # Matching service is alive
                    EventTypes.USER_LOGIN  # Auth service is alive
                ],
                handler=self._handle_health_event
            )
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            self.is_monitoring = False
            
    async def _handle_health_event(self, event: StreamEvent):
        """Handle health-related events"""
        service = event.source_service
        current_time = datetime.now(UTC)
        
        if service in self.service_status:
            self.service_status[service]["last_seen"] = current_time.isoformat()
            
            # Update service status based on event type
            if event.type == EventTypes.SERVICE_STARTED:
                self.service_status[service]["status"] = "healthy"
            elif event.type == EventTypes.SERVICE_STOPPED:
                self.service_status[service]["status"] = "stopped"
            elif event.type == EventTypes.SERVICE_ERROR:
                self.service_status[service]["status"] = "error"
            else:
                # Any activity means the service is alive
                self.service_status[service]["status"] = "active"
                
        logger.debug(f"Health event received from {service}: {event.type}")
        
    def get_service_health(self) -> Dict[str, Any]:
        """Get current service health status"""
        current_time = datetime.now(UTC)
        health_status = {}
        
        for service, status in self.service_status.items():
            last_seen = status.get("last_seen")
            time_since_last_seen = None
            
            if last_seen:
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                time_since_last_seen = (current_time - last_seen_dt).total_seconds()
                
            # Consider service unhealthy if no activity for 5 minutes
            if time_since_last_seen and time_since_last_seen > 300:
                health_status[service] = {
                    "status": "inactive",
                    "last_seen": last_seen,
                    "seconds_since_last_seen": int(time_since_last_seen)
                }
            else:
                health_status[service] = {
                    "status": status["status"],
                    "last_seen": last_seen,
                    "seconds_since_last_seen": int(time_since_last_seen) if time_since_last_seen else None
                }
                
        return health_status


# Global health monitor instance
health_monitor = HealthEventMonitor()


@router.get("/health/events")
async def get_event_health():
    """Get Redis event bus health and consumer information"""
    try:
        # Check Redis connectivity
        await health_monitor.event_bus.redis_client.ping() if health_monitor.event_bus.redis_client else None
        
        # Get stream info
        stream_info = await health_monitor.event_bus.get_stream_info()
        
        # Get consumer group status
        groups_info = {}
        for group in ["applications", "matching", "auth", "bff-health"]:
            try:
                groups_info[group] = await health_monitor.event_bus.get_consumer_group_info(group)
            except Exception:
                groups_info[group] = {"status": "not_created"}
        
        # Get recent events for debugging
        recent_events = await health_monitor.event_bus.get_recent_events(5)
        
        return {
            "redis_connected": stream_info.get("connected", False),
            "stream_info": stream_info,
            "consumer_groups": groups_info,
            "recent_events": [
                {
                    "id": event.stream_id,
                    "type": event.type,
                    "source": event.source_service,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in recent_events
            ],
            "monitoring_active": health_monitor.is_monitoring,
            "last_check": datetime.now(UTC).isoformat()
        }
        
    except Exception as e:
        return {
            "redis_connected": False,
            "error": str(e),
            "monitoring_active": health_monitor.is_monitoring,
            "last_check": datetime.now(UTC).isoformat()
        }


@router.get("/health/services")
async def get_services_health():
    """Get aggregated service health from event monitoring"""
    if not health_monitor.is_monitoring:
        # Start monitoring if not already started
        await health_monitor.start_monitoring()
        
    service_health = health_monitor.get_service_health()
    
    # Calculate overall system health
    all_services_healthy = all(
        status["status"] in ["healthy", "active"] 
        for status in service_health.values()
    )
    
    return {
        "overall_status": "healthy" if all_services_healthy else "degraded",
        "services": service_health,
        "monitoring_active": health_monitor.is_monitoring,
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.post("/health/events/start")
async def start_event_monitoring():
    """Manually start health event monitoring"""
    await health_monitor.start_monitoring()
    return {
        "status": "started",
        "monitoring_active": health_monitor.is_monitoring
    }


@router.get("/health/events/recent")
async def get_recent_events(limit: int = 20):
    """Get recent events from the stream"""
    try:
        events = await health_monitor.event_bus.get_recent_events(limit)
        
        return {
            "events": [
                {
                    "stream_id": event.stream_id,
                    "event_id": event.id,
                    "type": event.type,
                    "source_service": event.source_service,
                    "timestamp": event.timestamp.isoformat(),
                    "payload": event.payload
                }
                for event in events
            ],
            "count": len(events),
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "events": [],
            "count": 0
        }


# Startup function to initialize monitoring
async def initialize_health_monitoring():
    """Initialize health monitoring on BFF startup"""
    try:
        await health_monitor.start_monitoring()
        logger.info("Health event monitoring initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize health monitoring: {e}")