from typing import List, Dict, Any
from datetime import datetime
import json
import uuid

class EventStore:
    """Append-only event store"""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        
    async def append(self, event_type: str, aggregate_id: str, data: Dict[str, Any]) -> str:
        """Append event - NEVER modify or delete"""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "version": len([e for e in self.events if e["aggregate_id"] == aggregate_id]) + 1
        }
        
        self.events.append(event)
        
        # In production, this would persist to database
        # For now, append to file for audit trail
        with open(".agents/event_log.jsonl", "a") as f:
            f.write(json.dumps(event) + "\n")
            
        return event["event_id"]
        
    async def get_events(self, aggregate_id: str) -> List[Dict[str, Any]]:
        """Get all events for an aggregate"""
        return [e for e in self.events if e["aggregate_id"] == aggregate_id]
        
    async def replay(self, aggregate_id: str) -> Any:
        """Replay events to rebuild state"""
        events = await self.get_events(aggregate_id)
        # Implementation depends on aggregate type
        # This is where event sourcing magic happens
        pass