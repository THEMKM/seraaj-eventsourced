"""
Repository for Application aggregate with event sourcing support
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from services.shared.models import Application
from .events import EventPublisher


class ApplicationRepository:
    """Repository for Application aggregate with file-based storage"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / "applications.json"
        self.event_publisher = EventPublisher(data_dir)
        self._cache: Dict[str, Application] = {}
        self._load()
    
    def _load(self):
        """Load applications from JSON storage"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        # Convert string dates back to datetime objects
                        if isinstance(item.get('createdAt'), str):
                            item['createdAt'] = datetime.fromisoformat(item['createdAt'].replace('Z', '+00:00'))
                        if isinstance(item.get('updatedAt'), str):
                            item['updatedAt'] = datetime.fromisoformat(item['updatedAt'].replace('Z', '+00:00'))
                        if isinstance(item.get('submittedAt'), str):
                            item['submittedAt'] = datetime.fromisoformat(item['submittedAt'].replace('Z', '+00:00'))
                        if isinstance(item.get('reviewedAt'), str):
                            item['reviewedAt'] = datetime.fromisoformat(item['reviewedAt'].replace('Z', '+00:00'))
                        
                        app = Application(**item)
                        self._cache[app.id] = app
                        
                print(f"[INFO] Loaded {len(self._cache)} applications from storage")
            except Exception as e:
                print(f"[WARNING] Error loading applications: {e}")
                self._cache = {}
    
    def _save(self):
        """Persist applications to JSON storage"""
        try:
            data = []
            for app in self._cache.values():
                app_dict = app.dict()
                # Convert datetime objects to ISO strings for JSON serialization
                for field in ['createdAt', 'updatedAt', 'submittedAt', 'reviewedAt']:
                    if app_dict.get(field):
                        app_dict[field] = app_dict[field].isoformat()
                data.append(app_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"[INFO] Saved {len(data)} applications to storage")
        except Exception as e:
            print(f"[WARNING] Error saving applications: {e}")
            raise
    
    async def create(self, application: Application) -> Application:
        """Create new application with event logging"""
        if application.id in self._cache:
            raise ValueError(f"Application {application.id} already exists")
        
        self._cache[application.id] = application
        self._save()
        
        # Publish creation event
        await self.event_publisher.publish(
            "application.created",
            {
                "applicationId": application.id,
                "volunteerId": application.volunteerId,
                "opportunityId": application.opportunityId,
                "status": application.status
            }
        )
        
        return application
    
    async def get(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        return self._cache.get(application_id)
    
    async def update(self, application: Application) -> Application:
        """Update existing application with event logging"""
        if application.id not in self._cache:
            raise ValueError(f"Application {application.id} not found")
        
        old_application = self._cache[application.id]
        old_status = old_application.status
        
        # Update the application
        application.updatedAt = datetime.utcnow()
        self._cache[application.id] = application
        self._save()
        
        # Publish state change event if status changed
        if old_status != application.status:
            await self.event_publisher.publish(
                "application.state.changed",
                {
                    "applicationId": application.id,
                    "volunteerId": application.volunteerId,
                    "opportunityId": application.opportunityId,
                    "previousState": old_status,
                    "newState": application.status,
                    "timestamp": application.updatedAt.isoformat()
                }
            )
        
        return application
    
    async def find_by_volunteer(self, volunteer_id: str) -> List[Application]:
        """Find all applications by volunteer ID"""
        return [
            app for app in self._cache.values()
            if app.volunteerId == volunteer_id
        ]
    
    async def find_by_opportunity(self, opportunity_id: str) -> List[Application]:
        """Find all applications for an opportunity"""
        return [
            app for app in self._cache.values()
            if app.opportunityId == opportunity_id
        ]
    
    async def list_all(self) -> List[Application]:
        """List all applications"""
        return list(self._cache.values())