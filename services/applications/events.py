"""
Event publishing and event store for Applications service
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4


class EventPublisher:
    """Publishes domain events to file-based event store"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.event_log = self.data_dir / "application_events.jsonl"
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to the event store"""
        event = {
            "eventId": str(uuid4()),
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Append to event log (file-based event store)
        with open(self.event_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        print(f"[EVENT] Published event: {event_type}")
        return event