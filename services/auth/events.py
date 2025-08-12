"""
Auth domain event publisher
"""
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class AuthEventPublisher:
    """Publishes authentication domain events"""
    
    def __init__(self):
        self.event_log = Path("data/auth_domain_events.jsonl")
        self.event_log.parent.mkdir(exist_ok=True)
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an authentication event"""
        event = {
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        with open(self.event_log, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        print(f"Auth event published: {event_type}")
    
    async def publish_user_registered(self, user_id: str, email: str, name: str, role: str):
        """Publish user registration event"""
        await self.publish("user-registered", {
            "userId": user_id,
            "email": email,
            "name": name,
            "role": role,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_user_login(self, user_id: str, email: str):
        """Publish user login event"""
        await self.publish("user-login", {
            "userId": user_id,
            "email": email,
            "loginAt": datetime.utcnow().isoformat()
        })
    
    async def publish_user_password_changed(self, user_id: str):
        """Publish password change event"""
        await self.publish("user-password-changed", {
            "userId": user_id,
            "changedAt": datetime.utcnow().isoformat()
        })