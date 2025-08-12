"""
User repository implementing event sourcing pattern
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from services.shared.auth_models import User, UserRole


class UserRepository:
    """Repository for user data using JSONL event sourcing"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.data_dir / "auth_events.jsonl"
        self._state_cache: Dict[str, dict] = {}  # Store user data as dict
        self._rebuild_state()
    
    def _rebuild_state(self):
        """Rebuild current state from event log"""
        self._state_cache.clear()
        
        if not self.events_file.exists():
            return
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line.strip())
                    self._apply_event(event)
    
    def _apply_event(self, event: dict):
        """Apply an event to update the state"""
        event_type = event.get('type')
        user_id = event.get('userId')
        
        if event_type == 'user_registered':
            data = event['data']
            # Store user data as dict
            user_data = {
                'id': user_id,
                'email': data['email'],
                'name': data['name'],
                'role': data['role'],
                'isVerified': data.get('isVerified', True),
                'createdAt': data['createdAt'],
                'updatedAt': data.get('updatedAt'),
                'lastLoginAt': data.get('lastLoginAt'),
                'profileImageUrl': data.get('profileImageUrl'),
                # Internal fields not in public API
                'hashedPassword': data['hashedPassword'],
                'isActive': True
            }
            self._state_cache[user_id] = user_data
        
        elif event_type == 'user_password_updated':
            if user_id in self._state_cache:
                user_data = self._state_cache[user_id]
                user_data['hashedPassword'] = event['data']['hashedPassword']
                user_data['updatedAt'] = event['data']['updatedAt']
        
        elif event_type == 'user_deactivated':
            if user_id in self._state_cache:
                user_data = self._state_cache[user_id]
                user_data['isActive'] = False
                user_data['updatedAt'] = event['data']['updatedAt']
        
        elif event_type == 'user_login':
            if user_id in self._state_cache:
                user_data = self._state_cache[user_id]
                user_data['lastLoginAt'] = event['data']['loginAt']
    
    def _append_event(self, event: dict):
        """Append event to the event log"""
        with open(self.events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        # Apply to in-memory state
        self._apply_event(event)
    
    def _dict_to_user(self, user_data: dict) -> User:
        """Convert internal dict to User model"""
        return User(
            id=user_data['id'],
            email=user_data['email'],
            name=user_data['name'],
            role=UserRole(user_data['role']) if isinstance(user_data['role'], str) else user_data['role'],
            isVerified=user_data.get('isVerified', True),
            createdAt=datetime.fromisoformat(user_data['createdAt']) if isinstance(user_data['createdAt'], str) else user_data['createdAt'],
            updatedAt=datetime.fromisoformat(user_data['updatedAt']) if user_data.get('updatedAt') and isinstance(user_data['updatedAt'], str) else user_data.get('updatedAt'),
            lastLoginAt=datetime.fromisoformat(user_data['lastLoginAt']) if user_data.get('lastLoginAt') and isinstance(user_data['lastLoginAt'], str) else user_data.get('lastLoginAt'),
            profileImageUrl=user_data.get('profileImageUrl')
        )
    
    async def create(self, user_data: dict) -> User:
        """Create a new user from user data dict"""
        user_id = user_data['id']
        if user_id in self._state_cache:
            raise ValueError(f"User with id {user_id} already exists")
        
        # Check for email uniqueness
        if await self.find_by_email(user_data['email']):
            raise ValueError(f"User with email {user_data['email']} already exists")
        
        # Create registration event
        event = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "user_registered",
            "userId": user_id,
            "data": {
                "email": user_data['email'],
                "name": user_data['name'],
                "role": user_data['role'],
                "hashedPassword": user_data['hashedPassword'],
                "isVerified": user_data.get('isVerified', True),
                "createdAt": user_data['createdAt'].isoformat() if hasattr(user_data['createdAt'], 'isoformat') else user_data['createdAt'],
                "updatedAt": user_data.get('updatedAt').isoformat() if user_data.get('updatedAt') and hasattr(user_data.get('updatedAt'), 'isoformat') else user_data.get('updatedAt'),
                "lastLoginAt": user_data.get('lastLoginAt').isoformat() if user_data.get('lastLoginAt') and hasattr(user_data.get('lastLoginAt'), 'isoformat') else user_data.get('lastLoginAt'),
                "profileImageUrl": user_data.get('profileImageUrl')
            }
        }
        
        self._append_event(event)
        return self._dict_to_user(self._state_cache[user_id])
    
    async def get(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_data = self._state_cache.get(user_id)
        if user_data:
            return self._dict_to_user(user_data)
        return None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        for user_data in self._state_cache.values():
            if user_data['email'] == email and user_data.get('isActive', True):
                return self._dict_to_user(user_data)
        return None
    
    async def update_password(self, user_id: str, hashed_password: str) -> Optional[User]:
        """Update user password"""
        if user_id not in self._state_cache:
            return None
        
        event = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "user_password_updated",
            "userId": user_id,
            "data": {
                "hashedPassword": hashed_password,
                "updatedAt": datetime.utcnow().isoformat()
            }
        }
        
        self._append_event(event)
        return self._dict_to_user(self._state_cache[user_id])
    
    async def deactivate(self, user_id: str) -> Optional[User]:
        """Deactivate user"""
        if user_id not in self._state_cache:
            return None
        
        event = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "user_deactivated",
            "userId": user_id,
            "data": {
                "updatedAt": datetime.utcnow().isoformat()
            }
        }
        
        self._append_event(event)
        return self._dict_to_user(self._state_cache[user_id])
    
    async def record_login(self, user_id: str) -> Optional[User]:
        """Record user login timestamp"""
        if user_id not in self._state_cache:
            return None
        
        event = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "user_login",
            "userId": user_id,
            "data": {
                "loginAt": datetime.utcnow().isoformat()
            }
        }
        
        self._append_event(event)
        return self._dict_to_user(self._state_cache[user_id])
    
    async def list_all(self) -> List[User]:
        """List all active users"""
        return [self._dict_to_user(user_data) for user_data in self._state_cache.values() if user_data.get('isActive', True)]
    
    def get_internal_data(self, user_id: str) -> Optional[dict]:
        """Get internal user data (including hashedPassword)"""
        return self._state_cache.get(user_id)