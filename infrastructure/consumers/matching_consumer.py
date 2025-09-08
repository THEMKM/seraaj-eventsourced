"""
Example consumer for matching events - demonstrates cross-service communication
"""
import asyncio
import logging
from datetime import datetime

from infrastructure.event_bus import RedisEventBus, StreamEvent
from infrastructure.event_types import EventTypes

logger = logging.getLogger(__name__)


async def handle_matching_events(event: StreamEvent):
    """Example consumer for matching events"""
    print(f"[MATCHING CONSUMER] Received event: {event.type} from {event.source_service}")
    
    if event.type == EventTypes.MATCH_SUGGESTIONS_GENERATED:
        volunteer_id = event.payload.get("volunteerId")
        match_count = event.payload.get("matchCount", 0)
        
        print(f"  - Match suggestions generated for volunteer: {volunteer_id}")
        print(f"  - Number of matches: {match_count}")
        
        # Simulate processing work
        await asyncio.sleep(0.1)
        
        # Here you could:
        # - Send notification to volunteer about new matches
        # - Update volunteer dashboard cache
        # - Track matching algorithm performance
        # - Store matches in recommendation system
        
        if match_count > 0:
            matches = event.payload.get("matches", [])
            print(f"  - Top match opportunity ID: {matches[0].get('opportunityId') if matches else 'None'}")
        
    elif event.type == EventTypes.MATCH_SUGGESTION_APPLIED:
        suggestion_id = event.payload.get("suggestionId")
        volunteer_id = event.payload.get("volunteerId")
        opportunity_id = event.payload.get("opportunityId")
        
        print(f"  - Match suggestion applied: {suggestion_id}")
        print(f"  - Volunteer {volunteer_id} applied to opportunity {opportunity_id}")
        
        # Here you could:
        # - Update match success metrics
        # - Notify organization about application
        # - Remove suggestion from active suggestions
        # - Update matching algorithm feedback
        
    elif event.type == EventTypes.MATCH_SUGGESTION_ACCEPTED:
        suggestion_id = event.payload.get("suggestionId")
        
        print(f"  - Match suggestion accepted: {suggestion_id}")
        
        # Here you could:
        # - Celebrate successful match
        # - Update volunteer and organization records
        # - Trigger onboarding workflow
        
    elif event.type == EventTypes.MATCH_SUGGESTION_REJECTED:
        suggestion_id = event.payload.get("suggestionId")
        volunteer_id = event.payload.get("volunteerId")
        
        print(f"  - Match suggestion rejected by volunteer: {volunteer_id}")
        
        # Here you could:
        # - Learn from rejection to improve matching
        # - Generate alternative suggestions
        # - Update volunteer preferences


async def start_matching_consumer():
    """Start the matching events consumer"""
    event_bus = RedisEventBus()
    
    try:
        # Create consumer group if it doesn't exist
        await event_bus.create_consumer_group("matching", "0")
        
        print("Starting matching event consumer...")
        
        # Subscribe to matching events
        await event_bus.subscribe(
            group="matching",
            consumer="match-consumer-1", 
            event_types=[
                EventTypes.MATCH_SUGGESTIONS_GENERATED,
                EventTypes.MATCH_SUGGESTION_APPLIED,
                EventTypes.MATCH_SUGGESTION_ACCEPTED,
                EventTypes.MATCH_SUGGESTION_REJECTED,
                EventTypes.MATCH_SUGGESTION_EXPIRED
            ],
            handler=handle_matching_events
        )
        
    except Exception as e:
        logger.error(f"Matching consumer error: {e}")
    finally:
        await event_bus.close()


if __name__ == "__main__":
    # Run the consumer
    asyncio.run(start_matching_consumer())