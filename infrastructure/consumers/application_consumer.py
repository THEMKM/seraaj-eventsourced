"""
Example consumer for application events - demonstrates cross-service communication
"""
import asyncio
import logging
from datetime import datetime

from infrastructure.event_bus import RedisEventBus, StreamEvent
from infrastructure.event_types import EventTypes

logger = logging.getLogger(__name__)


async def handle_application_events(event: StreamEvent):
    """Example consumer for application events"""
    print(f"[APPLICATION CONSUMER] Received event: {event.type} from {event.source_service}")
    
    if event.type == EventTypes.APPLICATION_SUBMITTED:
        # Example: Could trigger notifications, update search indexes, etc.
        application_id = event.payload.get("applicationId")
        volunteer_id = event.payload.get("volunteerId")
        organization_id = event.payload.get("organizationId")
        
        print(f"  - New application submitted: {application_id}")
        print(f"  - Volunteer: {volunteer_id}, Organization: {organization_id}")
        
        # Simulate processing work
        await asyncio.sleep(0.1)
        
        # Here you could:
        # - Send notification to organization
        # - Update volunteer application count
        # - Index application for search
        # - Trigger matching service to generate suggestions
        
    elif event.type == EventTypes.APPLICATION_STATE_CHANGED:
        application_id = event.payload.get("applicationId")
        old_state = event.payload.get("oldState")
        new_state = event.payload.get("newState")
        
        print(f"  - Application {application_id} changed: {old_state} -> {new_state}")
        
        # Here you could:
        # - Send status update notification
        # - Update analytics/reporting
        # - Trigger workflow automation
        
    elif event.type == EventTypes.APPLICATION_COMPLETED:
        application_id = event.payload.get("applicationId")
        volunteer_id = event.payload.get("volunteerId")
        
        print(f"  - Application completed: {application_id}")
        
        # Here you could:
        # - Send completion certificate
        # - Update volunteer experience/points
        # - Generate completion report
        # - Update organization statistics


async def start_application_consumer():
    """Start the application events consumer"""
    event_bus = RedisEventBus()
    
    try:
        # Create consumer group if it doesn't exist
        await event_bus.create_consumer_group("applications", "0")
        
        print("Starting application event consumer...")
        
        # Subscribe to application events
        await event_bus.subscribe(
            group="applications",
            consumer="app-consumer-1",
            event_types=[
                EventTypes.APPLICATION_CREATED,
                EventTypes.APPLICATION_SUBMITTED,
                EventTypes.APPLICATION_STATE_CHANGED,
                EventTypes.APPLICATION_COMPLETED
            ],
            handler=handle_application_events
        )
        
    except Exception as e:
        logger.error(f"Application consumer error: {e}")
    finally:
        await event_bus.close()


if __name__ == "__main__":
    # Run the consumer
    asyncio.run(start_application_consumer())