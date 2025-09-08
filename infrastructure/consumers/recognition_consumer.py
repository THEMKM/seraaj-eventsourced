"""
Recognition/Points consumer: listens for points.award events and updates volunteer profile points.

This is a minimal implementation to connect event-based point awards to the Auth profile store.
"""
import asyncio
import logging
from uuid import UUID

from infrastructure.event_types import EventTypes
from infrastructure.event_bus import RedisEventBus, StreamEvent
from services.auth.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)


async def handle_points_events(event: StreamEvent):
    try:
        if event.type == EventTypes.POINTS_AWARD:
            payload = event.payload or {}
            volunteer_id = payload.get("volunteerId")
            points = int(payload.get("points", 0))
            if volunteer_id and points > 0:
                repo = ProfileRepository()
                updated = repo.add_points(UUID(volunteer_id), points)
                logger.info(
                    "[RECOGNITION] Awarded points",
                    extra={
                        "volunteerId": volunteer_id,
                        "points": points,
                        "newTotal": updated.points,
                        "newLevel": updated.level,
                    },
                )
            else:
                logger.warning(f"[RECOGNITION] Invalid points.award payload: {payload}")
    except Exception as e:
        logger.error(f"[RECOGNITION] Error handling event {event.type}: {e}")


async def start_recognition_consumer():
    bus = RedisEventBus()
    try:
        await bus.create_consumer_group("recognition", "0")
        await bus.subscribe(
            group="recognition",
            consumer="recognition-consumer-1",
            event_types=[EventTypes.POINTS_AWARD],
            handler=handle_points_events,
        )
    finally:
        await bus.close()


if __name__ == "__main__":
    asyncio.run(start_recognition_consumer())

