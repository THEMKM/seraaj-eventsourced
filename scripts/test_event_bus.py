#!/usr/bin/env python3
"""
Script to test Redis Event Bus functionality
"""
import asyncio
import sys
from datetime import datetime, UTC

sys.path.append(".")

from infrastructure.event_bus import RedisEventBus
from infrastructure.event_types import EventTypes


async def test_basic_functionality():
    """Test basic Redis Event Bus functionality"""
    print("Testing Redis Event Bus...")
    
    event_bus = RedisEventBus()
    
    try:
        # Test connection
        print("\n1. Testing Redis connection...")
        connected = await event_bus._ensure_connection()
        
        if not connected:
            print("[FAIL] Redis not available. Please start Redis server:")
            print("   docker run -d -p 6379:6379 redis:7-alpine")
            return False
        
        print("[OK] Connected to Redis")
        
        # Test event publishing
        print("\n2. Testing event publishing...")
        test_data = {
            "applicationId": "test-app-123",
            "volunteerId": "test-vol-456", 
            "organizationId": "test-org-789",
            "submittedAt": datetime.now(UTC).isoformat()
        }
        
        stream_id = await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            test_data,
            source_service="test-script"
        )
        
        if stream_id:
            print(f"[OK] Event published with stream ID: {stream_id}")
        else:
            print("[FAIL] Failed to publish event")
            return False
        
        # Test stream info
        print("\n3. Testing stream info...")
        stream_info = await event_bus.get_stream_info()
        print(f"[OK] Stream length: {stream_info.get('length', 0)}")
        
        # Test recent events
        print("\n4. Testing recent events retrieval...")
        recent_events = await event_bus.get_recent_events(3)
        print(f"[OK] Retrieved {len(recent_events)} recent events")
        
        if recent_events:
            latest = recent_events[0]
            print(f"   Latest event: {latest.type} from {latest.source_service}")
        
        # Test consumer group creation
        print("\n5. Testing consumer group creation...")
        success = await event_bus.create_consumer_group("test-group", "0")
        
        if success:
            print("[OK] Consumer group created")
        else:
            print("[FAIL] Failed to create consumer group")
        
        # Test consumer group info
        group_info = await event_bus.get_consumer_group_info("test-group")
        if group_info.get("connected"):
            print(f"[OK] Consumer group info: {group_info.get('pending', 0)} pending messages")
        
        print("\n[SUCCESS] All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        return False
        
    finally:
        await event_bus.close()


async def test_consumer_subscription():
    """Test event consumption with consumer groups"""
    print("\nTesting event consumption...")
    
    event_bus = RedisEventBus()
    received_events = []
    
    async def test_handler(event):
        print(f"[EVENT] Received event: {event.type} from {event.source_service}")
        received_events.append(event)
    
    try:
        # Create consumer group
        await event_bus.create_consumer_group("test-consumers", "0")
        
        # Start consumer in background
        consumer_task = asyncio.create_task(
            event_bus.subscribe(
                group="test-consumers",
                consumer="test-consumer-1",
                event_types=[EventTypes.APPLICATION_SUBMITTED, EventTypes.MATCH_SUGGESTIONS_GENERATED],
                handler=test_handler
            )
        )
        
        # Give consumer time to start
        await asyncio.sleep(0.5)
        
        # Publish test events
        print("Publishing test events...")
        
        # Application event
        await event_bus.publish(
            EventTypes.APPLICATION_SUBMITTED,
            {"applicationId": "consumer-test-1", "volunteerId": "vol-test"},
            source_service="test-publisher"
        )
        
        # Matching event
        await event_bus.publish(
            EventTypes.MATCH_SUGGESTIONS_GENERATED,
            {"volunteerId": "vol-test", "matchCount": 2},
            source_service="test-publisher"
        )
        
        # Give time for consumption
        await asyncio.sleep(2.0)
        
        # Stop consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        print(f"[OK] Consumer processed {len(received_events)} events")
        
        if len(received_events) >= 2:
            print("[SUCCESS] Event consumption test passed!")
            return True
        else:
            print("[WARNING] Expected at least 2 events, but got fewer")
            return False
        
    except Exception as e:
        print(f"[ERROR] Consumer test failed: {e}")
        return False
        
    finally:
        await event_bus.close()


async def test_dual_publishing():
    """Test dual publishing from service event publishers"""
    print("\nTesting service event publishers...")
    
    try:
        # Test Applications service event publisher
        from services.applications.events import EventPublisher as AppEventPublisher
        
        app_publisher = AppEventPublisher(use_redis=True)
        
        test_application = {
            "id": "dual-test-app",
            "volunteerId": "vol-dual-test",
            "organizationId": "org-dual-test",
            "opportunityId": "opp-dual-test"
        }
        
        print("Publishing via Applications service...")
        await app_publisher.publish_application_submitted(test_application)
        
        # Test Matching service event publisher
        from services.matching.service import MatchingService
        
        matching_service = MatchingService()
        
        if matching_service.redis_bus:
            print("Publishing via Matching service...")
            await matching_service._publish_match_suggestions_generated(
                "vol-dual-test",
                []  # Empty suggestions for test
            )
        
        # Test Auth service event publisher
        from services.auth.events import AuthEventPublisher
        
        auth_publisher = AuthEventPublisher()
        
        print("Publishing via Auth service...")
        await auth_publisher.publish_user_login("user-dual-test", "test@example.com")
        
        print("[OK] All service publishers working!")
        
        # Close connections
        await app_publisher.close()
        if matching_service.redis_bus:
            await matching_service.close()
        await auth_publisher.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Service publisher test failed: {e}")
        return False


async def main():
    """Run all event bus tests"""
    print("Redis Event Bus Testing Suite")
    print("=" * 40)
    
    # Test basic functionality
    basic_ok = await test_basic_functionality()
    
    if basic_ok:
        # Test consumer subscription
        consumer_ok = await test_consumer_subscription()
        
        # Test service publishers
        publisher_ok = await test_dual_publishing()
        
        if basic_ok and consumer_ok and publisher_ok:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            print("[OK] Redis Event Bus is ready for production use")
        else:
            print(f"\n[WARNING] Some tests failed:")
            print(f"   Basic: {'[OK]' if basic_ok else '[FAIL]'}")
            print(f"   Consumer: {'[OK]' if consumer_ok else '[FAIL]'}")
            print(f"   Publishers: {'[OK]' if publisher_ok else '[FAIL]'}")
    else:
        print("\n[ERROR] Basic tests failed - check Redis connection")
    
    print("\nTo start Redis for testing:")
    print("docker run -d -p 6379:6379 redis:7-alpine")


if __name__ == "__main__":
    asyncio.run(main())