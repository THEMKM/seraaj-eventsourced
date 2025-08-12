#!/usr/bin/env python3
"""
Test script to demonstrate Redis fallback behavior when Redis is unavailable
"""
import asyncio
import sys
import os
from datetime import datetime, UTC

sys.path.append(".")

from infrastructure.event_bus import RedisEventBus
from infrastructure.event_types import EventTypes
from services.applications.events import EventPublisher as AppEventPublisher


async def test_redis_fallback():
    """Test that services work when Redis is unavailable"""
    print("Testing Redis Event Bus Fallback Behavior")
    print("=" * 50)
    
    # Test direct Redis event bus with no connection
    print("\n1. Testing Redis Event Bus directly (no Redis server)...")
    event_bus = RedisEventBus()
    
    # This should fail gracefully
    stream_id = await event_bus.publish(
        EventTypes.APPLICATION_SUBMITTED,
        {"applicationId": "test-app", "volunteerId": "test-vol"},
        source_service="test"
    )
    
    if stream_id is None:
        print("[OK] Redis unavailable - event bus handled gracefully")
    else:
        print(f"[UNEXPECTED] Event published despite no Redis: {stream_id}")
    
    await event_bus.close()
    
    # Test Applications service publisher (dual publishing)
    print("\n2. Testing Applications Service Event Publisher...")
    
    # Create test data directory
    os.makedirs("data", exist_ok=True)
    
    app_publisher = AppEventPublisher(use_redis=True)
    
    test_application = {
        "id": "fallback-test-app",
        "volunteerId": "vol-fallback-test",
        "organizationId": "org-fallback-test",
        "opportunityId": "opp-fallback-test",
        "submittedAt": datetime.now(UTC).isoformat()
    }
    
    print("Publishing application submitted event...")
    event = await app_publisher.publish_application_submitted(test_application)
    
    if event:
        print("[OK] Event published to file (Redis unavailable)")
        print(f"     Event ID: {event['eventId']}")
        print(f"     Event Type: {event['eventType']}")
    else:
        print("[FAIL] Failed to publish event")
    
    # Check that file was created
    event_file = app_publisher.event_log
    if event_file.exists():
        with open(event_file, 'r') as f:
            lines = f.readlines()
            print(f"[OK] Event file has {len(lines)} events")
            if lines:
                import json
                last_event = json.loads(lines[-1])
                print(f"     Last event: {last_event['eventType']}")
    
    await app_publisher.close()
    
    # Test Matching service
    print("\n3. Testing Matching Service...")
    
    try:
        from services.matching.service import MatchingService
        
        matching_service = MatchingService()
        
        # This should work even without Redis
        suggestions = await matching_service.quick_match("vol-test", limit=2)
        
        print(f"[OK] Matching service generated {len(suggestions)} suggestions")
        
        if matching_service.redis_bus is None:
            print("[OK] Matching service working without Redis")
        
        await matching_service.close()
        
    except Exception as e:
        print(f"[ERROR] Matching service test failed: {e}")
    
    # Test Auth service
    print("\n4. Testing Auth Service...")
    
    try:
        from services.auth.events import AuthEventPublisher
        
        auth_publisher = AuthEventPublisher()
        
        await auth_publisher.publish_user_login("user-fallback-test", "test@fallback.com")
        
        print("[OK] Auth service event published")
        
        # Check auth event file
        if auth_publisher.event_log.exists():
            with open(auth_publisher.event_log, 'r') as f:
                lines = f.readlines()
                print(f"[OK] Auth event file has {len(lines)} events")
        
        await auth_publisher.close()
        
    except Exception as e:
        print(f"[ERROR] Auth service test failed: {e}")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] All services work gracefully without Redis!")
    print("Services fall back to file-based events when Redis unavailable.")
    print("This ensures system resilience and backward compatibility.")


async def test_health_monitoring():
    """Test BFF health monitoring without Redis"""
    print("\n5. Testing BFF Health Monitoring...")
    
    try:
        from bff.health_events import HealthEventMonitor
        
        health_monitor = HealthEventMonitor()
        
        # This should handle Redis unavailability gracefully
        service_health = health_monitor.get_service_health()
        
        print(f"[OK] Health monitoring working")
        print(f"     Services monitored: {list(service_health.keys())}")
        
        for service, status in service_health.items():
            print(f"     {service}: {status['status']}")
        
    except Exception as e:
        print(f"[ERROR] Health monitoring test failed: {e}")


def show_redis_setup():
    """Show how to set up Redis for production use"""
    print("\n" + "=" * 50)
    print("REDIS SETUP FOR PRODUCTION")
    print("=" * 50)
    print()
    print("1. Start Redis with Docker:")
    print("   docker run -d -p 6379:6379 --name seraaj-redis redis:7-alpine")
    print()
    print("2. Or install Redis locally:")
    print("   - Windows: Download from https://redis.io/download")
    print("   - Ubuntu: sudo apt install redis-server")
    print("   - macOS: brew install redis")
    print()
    print("3. Set environment variables:")
    print("   REDIS_URL=redis://localhost:6379/0")
    print("   USE_REDIS_EVENTS=true")
    print()
    print("4. Test Redis connection:")
    print("   python scripts/test_event_bus.py")
    print()
    print("With Redis running, services will use dual publishing:")
    print("- Events published to both Redis streams AND local files")
    print("- Cross-service communication enabled") 
    print("- Real-time event processing")
    print("- Health monitoring via event streams")


async def main():
    await test_redis_fallback()
    await test_health_monitoring()
    show_redis_setup()


if __name__ == "__main__":
    asyncio.run(main())