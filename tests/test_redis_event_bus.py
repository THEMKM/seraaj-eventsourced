"""
Integration tests for Redis Event Bus
"""
import asyncio
import pytest
from datetime import datetime, UTC

from infrastructure.event_bus import RedisEventBus, StreamEvent
from infrastructure.event_types import EventTypes


@pytest.fixture
async def event_bus():
    """Create event bus instance for testing"""
    bus = RedisEventBus()
    yield bus
    await bus.close()


@pytest.fixture
def test_event_data():
    """Sample event data for testing"""
    return {
        "applicationId": "app-123",
        "volunteerId": "vol-456",
        "organizationId": "org-789",
        "submittedAt": datetime.now(UTC).isoformat()
    }


class TestRedisEventBus:
    """Test Redis Event Bus functionality"""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, event_bus):
        """Test Redis connection and basic operations"""
        connected = await event_bus._ensure_connection()
        
        if not connected:
            pytest.skip("Redis not available for testing")
            
        assert connected is True
        assert event_bus._connected is True
    
    @pytest.mark.asyncio 
    async def test_publish_event(self, event_bus, test_event_data):
        """Test event publishing to Redis stream"""
        # Publish an event
        stream_id = await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            test_event_data,
            source_service="applications"
        )
        
        if stream_id is None:
            pytest.skip("Redis not available - event not published")
            
        assert stream_id is not None
        assert isinstance(stream_id, str)
        
        # Verify stream info
        stream_info = await event_bus.get_stream_info()
        assert stream_info["connected"] is True
        assert stream_info["length"] >= 1
    
    @pytest.mark.asyncio
    async def test_consumer_group_creation(self, event_bus):
        """Test consumer group creation"""
        if not await event_bus._ensure_connection():
            pytest.skip("Redis not available")
            
        # Create a test consumer group
        success = await event_bus.create_consumer_group("test-group", "0")
        assert success is True
        
        # Try to create the same group again (should not fail)
        success = await event_bus.create_consumer_group("test-group", "0")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_recent_events(self, event_bus, test_event_data):
        """Test retrieving recent events from stream"""
        if not await event_bus._ensure_connection():
            pytest.skip("Redis not available")
            
        # Publish a test event
        await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            test_event_data,
            source_service="test"
        )
        
        # Get recent events
        events = await event_bus.get_recent_events(5)
        assert len(events) >= 1
        
        # Verify event structure
        latest_event = events[0]
        assert isinstance(latest_event, StreamEvent)
        assert latest_event.type == EventTypes.APPLICATION_SUBMITTED
        assert latest_event.source_service == "test"
        assert "applicationId" in latest_event.payload
    
    @pytest.mark.asyncio
    async def test_event_consumer_subscription(self, event_bus):
        """Test event consumption with consumer group"""
        if not await event_bus._ensure_connection():
            pytest.skip("Redis not available")
            
        received_events = []
        
        async def test_handler(event: StreamEvent):
            received_events.append(event)
            
        # Create consumer group
        await event_bus.create_consumer_group("test-consumer-group", "0")
        
        # Start consumer in background
        consumer_task = asyncio.create_task(
            event_bus.subscribe(
                group="test-consumer-group",
                consumer="test-consumer",
                event_types=[EventTypes.APPLICATION_SUBMITTED],
                handler=test_handler
            )
        )
        
        # Give consumer time to start
        await asyncio.sleep(0.1)
        
        # Publish an event
        test_data = {"testId": "123", "message": "test event"}
        await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            test_data,
            source_service="test"
        )
        
        # Give consumer time to process
        await asyncio.sleep(0.5)
        
        # Cancel consumer task
        consumer_task.cancel()
        
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Verify event was received
        assert len(received_events) >= 1
        received_event = received_events[-1]  # Get latest event
        assert received_event.type == EventTypes.APPLICATION_SUBMITTED
        assert received_event.payload["testId"] == "123"


class TestEventTypes:
    """Test event type constants and utilities"""
    
    def test_event_types_constants(self):
        """Test that all event types are properly defined"""
        assert EventTypes.APPLICATION_SUBMITTED == "application.submitted"
        assert EventTypes.MATCH_SUGGESTIONS_GENERATED == "match.suggestions.generated"
        assert EventTypes.USER_REGISTERED == "user.registered"
        assert EventTypes.SERVICE_STARTED == "service.started"
    
    def test_get_event_categories(self):
        """Test event type category methods"""
        app_events = EventTypes.get_application_events()
        assert EventTypes.APPLICATION_SUBMITTED in app_events
        assert EventTypes.APPLICATION_STATE_CHANGED in app_events
        
        match_events = EventTypes.get_matching_events()
        assert EventTypes.MATCH_SUGGESTIONS_GENERATED in match_events
        
        auth_events = EventTypes.get_auth_events()
        assert EventTypes.USER_REGISTERED in auth_events
        assert EventTypes.USER_LOGIN in auth_events
        
        system_events = EventTypes.get_system_events()
        assert EventTypes.SERVICE_STARTED in system_events


@pytest.mark.asyncio
async def test_end_to_end_event_flow():
    """
    End-to-end test: Publish application event and consume it
    Simulates real cross-service communication
    """
    # This test simulates the full event flow:
    # 1. Applications service publishes event
    # 2. Matching service receives and processes event
    
    event_bus = RedisEventBus()
    
    if not await event_bus._ensure_connection():
        pytest.skip("Redis not available for end-to-end test")
    
    try:
        consumed_events = []
        
        async def matching_service_handler(event: StreamEvent):
            """Simulate matching service processing application events"""
            if event.type == EventTypes.APPLICATION_SUBMITTED:
                # Matching service generates suggestions for new applications
                volunteer_id = event.payload.get("volunteerId")
                
                # Simulate match generation (simplified)
                await event_bus.publish(
                    EventTypes.MATCH_SUGGESTIONS_GENERATED,
                    {
                        "volunteerId": volunteer_id,
                        "matchCount": 3,
                        "matches": [
                            {"opportunityId": "opp-1", "score": 0.95},
                            {"opportunityId": "opp-2", "score": 0.87},
                            {"opportunityId": "opp-3", "score": 0.72}
                        ],
                        "generatedAt": datetime.now(UTC).isoformat()
                    },
                    source_service="matching"
                )
                
            consumed_events.append(event)
        
        # Set up consumer group for matching service
        await event_bus.create_consumer_group("matching-service", "0")
        
        # Start matching service consumer
        consumer_task = asyncio.create_task(
            event_bus.subscribe(
                group="matching-service",
                consumer="match-generator-1",
                event_types=[EventTypes.APPLICATION_SUBMITTED],
                handler=matching_service_handler
            )
        )
        
        # Give consumer time to start
        await asyncio.sleep(0.1)
        
        # Simulate applications service publishing event
        application_data = {
            "applicationId": "app-e2e-test",
            "volunteerId": "vol-123",
            "organizationId": "org-456",
            "opportunityId": "opp-789",
            "submittedAt": datetime.now(UTC).isoformat()
        }
        
        await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            application_data,
            source_service="applications"
        )
        
        # Give time for event processing
        await asyncio.sleep(1.0)
        
        # Stop consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Verify the flow
        assert len(consumed_events) >= 1
        
        # Check that application event was consumed
        app_event = consumed_events[0]
        assert app_event.type == EventTypes.APPLICATION_SUBMITTED
        assert app_event.payload["applicationId"] == "app-e2e-test"
        
        # Check that matching service generated follow-up event
        recent_events = await event_bus.get_recent_events(10)
        match_events = [e for e in recent_events if e.type == EventTypes.MATCH_SUGGESTIONS_GENERATED]
        
        assert len(match_events) >= 1
        match_event = match_events[0]
        assert match_event.source_service == "matching"
        assert match_event.payload["volunteerId"] == "vol-123"
        assert match_event.payload["matchCount"] == 3
        
        print("✅ End-to-end event flow test passed!")
        
    finally:
        await event_bus.close()


if __name__ == "__main__":
    # Run the end-to-end test directly
    asyncio.run(test_end_to_end_event_flow())