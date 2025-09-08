"""
Redis Event Bus Usage Examples
Demonstrates how to use the event bus for cross-service communication
"""
import asyncio
from datetime import datetime, UTC

from infrastructure.event_bus import RedisEventBus, StreamEvent
from infrastructure.event_types import EventTypes


async def example_publisher():
    """Example of publishing events to the Redis stream"""
    print("=== EVENT PUBLISHING EXAMPLE ===")
    
    event_bus = RedisEventBus()
    
    # Example 1: Application submitted event
    application_data = {
        "applicationId": "app-12345",
        "volunteerId": "vol-67890",
        "organizationId": "org-11111",
        "opportunityId": "opp-22222",
        "submittedAt": datetime.now(UTC).isoformat(),
        "volunteerSkills": ["teaching", "communication"],
        "opportunityRequirements": ["education", "weekends"]
    }
    
    print("Publishing application submitted event...")
    stream_id = await event_bus.publish(
        EventTypes.APPLICATION_SUBMITTED,
        application_data,
        source_service="applications"
    )
    
    if stream_id:
        print(f"✓ Published to stream ID: {stream_id}")
    
    # Example 2: Match suggestions generated event
    match_data = {
        "volunteerId": "vol-67890",
        "matchCount": 3,
        "matches": [
            {
                "opportunityId": "opp-33333",
                "organizationId": "org-44444", 
                "score": 0.95,
                "explanation": "Perfect skill match and location proximity"
            },
            {
                "opportunityId": "opp-55555",
                "organizationId": "org-66666",
                "score": 0.87,
                "explanation": "Good skill alignment, different location"
            }
        ],
        "generatedAt": datetime.now(UTC).isoformat()
    }
    
    print("Publishing match suggestions event...")
    stream_id = await event_bus.publish(
        EventTypes.MATCH_SUGGESTIONS_GENERATED,
        match_data,
        source_service="matching"
    )
    
    if stream_id:
        print(f"✓ Published to stream ID: {stream_id}")
    
    # Example 3: User login event
    auth_data = {
        "userId": "user-99999",
        "email": "volunteer@example.com",
        "loginAt": datetime.now(UTC).isoformat(),
        "userAgent": "Mozilla/5.0...",
        "ipAddress": "192.168.1.100"
    }
    
    print("Publishing user login event...")
    stream_id = await event_bus.publish(
        EventTypes.USER_LOGIN,
        auth_data,
        source_service="auth"
    )
    
    if stream_id:
        print(f"✓ Published to stream ID: {stream_id}")
    
    await event_bus.close()


async def example_consumer():
    """Example of consuming events from different services"""
    print("\n=== EVENT CONSUMPTION EXAMPLE ===")
    
    event_bus = RedisEventBus()
    processed_events = []
    
    async def application_handler(event: StreamEvent):
        """Handle application-related events"""
        print(f"[APP-CONSUMER] Processing: {event.type}")
        
        if event.type == EventTypes.APPLICATION_SUBMITTED:
            # Trigger business logic
            app_id = event.payload.get("applicationId")
            vol_id = event.payload.get("volunteerId")
            
            print(f"  → New application {app_id} from volunteer {vol_id}")
            
            # Here you could:
            # - Send notification to organization
            # - Update search indexes
            # - Trigger matching workflow
            # - Update analytics
            
            processed_events.append(f"processed-app-{app_id}")
    
    try:
        # Create consumer group for this example
        await event_bus.create_consumer_group("example-consumers", "$")  # Start from newest
        
        print("Starting event consumer (will run for 3 seconds)...")
        
        # Start consumer task
        consumer_task = asyncio.create_task(
            event_bus.subscribe(
                group="example-consumers",
                consumer="example-consumer-1",
                event_types=[
                    EventTypes.APPLICATION_SUBMITTED,
                    EventTypes.MATCH_SUGGESTIONS_GENERATED,
                    EventTypes.USER_LOGIN
                ],
                handler=application_handler
            )
        )
        
        # Let it run for a few seconds
        await asyncio.sleep(3)
        
        # Stop consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        print(f"Consumer processed {len(processed_events)} events")
        
    finally:
        await event_bus.close()


async def example_health_monitoring():
    """Example of using event bus for health monitoring"""
    print("\n=== HEALTH MONITORING EXAMPLE ===")
    
    event_bus = RedisEventBus()
    
    # Get stream information
    stream_info = await event_bus.get_stream_info()
    print(f"Stream status: {'Connected' if stream_info.get('connected') else 'Disconnected'}")
    
    if stream_info.get('connected'):
        print(f"Stream length: {stream_info.get('length', 0)} events")
        print(f"Consumer groups: {stream_info.get('groups', 0)}")
    
    # Get recent events for debugging
    recent_events = await event_bus.get_recent_events(5)
    print(f"\nRecent events ({len(recent_events)}):")
    
    for event in recent_events:
        print(f"  {event.timestamp.strftime('%H:%M:%S')} - {event.type} from {event.source_service}")
    
    # Check consumer group status
    for group in ["applications", "matching", "auth"]:
        group_info = await event_bus.get_consumer_group_info(group)
        if group_info.get("connected"):
            print(f"\nConsumer group '{group}':")
            print(f"  Consumers: {group_info.get('consumers', 0)}")
            print(f"  Pending messages: {group_info.get('pending', 0)}")
            print(f"  Lag: {group_info.get('lag', 'unknown')}")
    
    await event_bus.close()


async def example_cross_service_workflow():
    """Example of a complete cross-service workflow using events"""
    print("\n=== CROSS-SERVICE WORKFLOW EXAMPLE ===")
    print("Simulating: Application submission → Match generation → Notification")
    
    event_bus = RedisEventBus()
    workflow_events = []
    
    async def workflow_handler(event: StreamEvent):
        """Handle workflow events across services"""
        workflow_events.append(event)
        
        if event.type == EventTypes.APPLICATION_SUBMITTED:
            print(f"[WORKFLOW] Step 1: Application received from {event.source_service}")
            volunteer_id = event.payload.get("volunteerId")
            
            # Simulate matching service responding to application
            await asyncio.sleep(0.1)  # Simulate processing time
            
            await event_bus.publish(
                EventTypes.MATCH_SUGGESTIONS_GENERATED,
                {
                    "volunteerId": volunteer_id,
                    "matchCount": 2,
                    "triggeredBy": "application_submitted",
                    "generatedAt": datetime.now(UTC).isoformat()
                },
                source_service="matching"
            )
            
        elif event.type == EventTypes.MATCH_SUGGESTIONS_GENERATED:
            print(f"[WORKFLOW] Step 2: Matches generated by {event.source_service}")
            volunteer_id = event.payload.get("volunteerId")
            match_count = event.payload.get("matchCount", 0)
            
            print(f"  → Generated {match_count} matches for volunteer {volunteer_id}")
            
            # Simulate notification service responding
            await asyncio.sleep(0.1)
            
            print("[WORKFLOW] Step 3: Sending notification to volunteer")
            # In real system, this would be a notification service event
    
    try:
        # Set up workflow consumer
        await event_bus.create_consumer_group("workflow-demo", "$")
        
        consumer_task = asyncio.create_task(
            event_bus.subscribe(
                group="workflow-demo",
                consumer="workflow-demo-1",
                event_types=[
                    EventTypes.APPLICATION_SUBMITTED,
                    EventTypes.MATCH_SUGGESTIONS_GENERATED
                ],
                handler=workflow_handler
            )
        )
        
        await asyncio.sleep(0.2)  # Let consumer start
        
        # Trigger the workflow
        print("[WORKFLOW] Starting workflow with application submission...")
        
        await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            {
                "applicationId": "workflow-demo-app",
                "volunteerId": "workflow-demo-vol",
                "organizationId": "workflow-demo-org",
                "submittedAt": datetime.now(UTC).isoformat()
            },
            source_service="applications"
        )
        
        # Let workflow complete
        await asyncio.sleep(2)
        
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        print(f"\n[WORKFLOW] Complete! Processed {len(workflow_events)} events")
        
    finally:
        await event_bus.close()


async def main():
    """Run all examples"""
    print("REDIS EVENT BUS EXAMPLES")
    print("=" * 40)
    
    # Check if Redis is available
    test_bus = RedisEventBus()
    connected = await test_bus._ensure_connection()
    await test_bus.close()
    
    if not connected:
        print("\n⚠️  Redis not available - examples will show fallback behavior")
        print("Start Redis with: docker run -d -p 6379:6379 redis:7-alpine")
        print()
    
    await example_publisher()
    await example_consumer()
    await example_health_monitoring()
    await example_cross_service_workflow()
    
    print("\n" + "=" * 40)
    print("Examples complete!")
    
    if connected:
        print("✓ Redis Event Bus is working properly")
    else:
        print("ℹ  Redis unavailable - services fell back gracefully")


if __name__ == "__main__":
    asyncio.run(main())