"""
Repository for Application aggregate with event sourcing support
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from services.shared.models import Application
from .events import EventPublisher


class ApplicationRepository:
    """Repository for Application aggregate with dual backend support"""
    
    def __init__(self, data_dir: str = "data", storage_backend: Optional[str] = None):
        # Determine storage backend
        self.storage_backend = storage_backend or self._detect_storage_backend()
        
        if self.storage_backend == "postgres":
            self._init_postgres()
        else:
            self._init_file_storage(data_dir)
    
    def _detect_storage_backend(self) -> str:
        """Detect which storage backend to use based on environment"""
        if os.getenv('DATABASE_URL') or os.getenv('DB_HOST'):
            return "postgres"
        return "file"
    
    def _init_postgres(self):
        """Initialize PostgreSQL backend"""
        from infrastructure.db.connection import db_connection
        from infrastructure.db.event_store import event_store
        from infrastructure.db.projections import projection_service
        
        self.db_connection = db_connection
        self.event_store = event_store
        self.projection_service = projection_service
        print(f"[INFO] ApplicationRepository using PostgreSQL backend")
    
    def _init_file_storage(self, data_dir: str):
        """Initialize file-based storage backend"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / "applications.json"
        self.event_publisher = EventPublisher(data_dir)
        self._cache: Dict[str, Application] = {}
        self._load()
        print(f"[INFO] ApplicationRepository using file-based backend")
    
    def _load(self):
        """Load applications from JSON storage (file backend only)"""
        if self.storage_backend != "file":
            return
            
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
                        
                print(f"[INFO] Loaded {len(self._cache)} applications from file storage")
            except Exception as e:
                print(f"[WARNING] Error loading applications: {e}")
                self._cache = {}
    
    def _save(self):
        """Persist applications to JSON storage (file backend only)"""
        if self.storage_backend != "file":
            return
            
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
                
            print(f"[INFO] Saved {len(data)} applications to file storage")
        except Exception as e:
            print(f"[WARNING] Error saving applications: {e}")
            raise
    
    async def create(self, application: Application) -> Application:
        """Create new application with event logging"""
        if self.storage_backend == "postgres":
            return await self._create_postgres(application)
        else:
            return await self._create_file(application)
    
    async def _create_postgres(self, application: Application) -> Application:
        """Create application using PostgreSQL backend"""
        # Check if application exists
        existing = await self._get_postgres(application.id)
        if existing:
            raise ValueError(f"Application {application.id} already exists")
        
        # Store event
        event = await self.event_store.append_event(
            aggregate_id=uuid.UUID(application.id),
            aggregate_type="Application",
            event_type="application.created",
            payload={
                "applicationId": application.id,
                "volunteerId": application.volunteerId,
                "opportunityId": application.opportunityId,
                "organizationId": application.organizationId,
                "status": application.status,
                "coverLetter": application.coverLetter,
                "submittedAt": application.submittedAt.isoformat() if application.submittedAt else None,
                "reviewedAt": application.reviewedAt.isoformat() if application.reviewedAt else None,
                "createdAt": application.createdAt.isoformat(),
                "updatedAt": application.updatedAt.isoformat()
            },
            expected_version=0
        )
        
        # Update projection
        await self.projection_service.handle_event(event)
        
        return application
    
    async def _create_file(self, application: Application) -> Application:
        """Create application using file backend"""
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
        if self.storage_backend == "postgres":
            return await self._get_postgres(application_id)
        else:
            return self._cache.get(application_id)
    
    async def _get_postgres(self, application_id: str) -> Optional[Application]:
        """Get application using PostgreSQL backend"""
        try:
            from sqlalchemy import text
            async with self.db_connection.get_session() as session:
                query = text("SELECT * FROM applications WHERE id = :id")
                result = await session.execute(query, {"id": application_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                return Application(
                    id=str(row.id),
                    volunteerId=str(row.volunteer_id),
                    opportunityId=str(row.opportunity_id),
                    organizationId=str(row.organization_id) if row.organization_id else None,
                    status=row.status,
                    coverLetter=row.cover_letter,
                    submittedAt=row.submitted_at,
                    reviewedAt=row.reviewed_at,
                    createdAt=row.created_at,
                    updatedAt=row.updated_at
                )
        except Exception as e:
            print(f"[WARNING] Error getting application {application_id}: {e}")
            return None
    
    async def update(self, application: Application) -> Application:
        """Update existing application with event logging"""
        if self.storage_backend == "postgres":
            return await self._update_postgres(application)
        else:
            return await self._update_file(application)
    
    async def _update_postgres(self, application: Application) -> Application:
        """Update application using PostgreSQL backend"""
        # Get current application
        old_application = await self._get_postgres(application.id)
        if not old_application:
            raise ValueError(f"Application {application.id} not found")
        
        old_status = old_application.status
        application.updatedAt = datetime.utcnow()
        
        # Get current version
        current_version = await self.event_store.get_aggregate_version(uuid.UUID(application.id))
        
        # Store update event
        if old_status != application.status:
            event = await self.event_store.append_event(
                aggregate_id=uuid.UUID(application.id),
                aggregate_type="Application",
                event_type="application.state.changed",
                payload={
                    "applicationId": application.id,
                    "volunteerId": application.volunteerId,
                    "opportunityId": application.opportunityId,
                    "previousState": old_status,
                    "newState": application.status,
                    "timestamp": application.updatedAt.isoformat()
                },
                expected_version=current_version
            )
        else:
            event = await self.event_store.append_event(
                aggregate_id=uuid.UUID(application.id),
                aggregate_type="Application",
                event_type="application.updated",
                payload={
                    "applicationId": application.id,
                    "coverLetter": application.coverLetter,
                    "organizationId": application.organizationId,
                    "updatedAt": application.updatedAt.isoformat()
                },
                expected_version=current_version
            )
        
        # Update projection
        await self.projection_service.handle_event(event)
        
        return application
    
    async def _update_file(self, application: Application) -> Application:
        """Update application using file backend"""
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
        if self.storage_backend == "postgres":
            return await self._find_by_volunteer_postgres(volunteer_id)
        else:
            return [
                app for app in self._cache.values()
                if app.volunteerId == volunteer_id
            ]
    
    async def _find_by_volunteer_postgres(self, volunteer_id: str) -> List[Application]:
        """Find applications by volunteer ID using PostgreSQL"""
        try:
            from sqlalchemy import text
            async with self.db_connection.get_session() as session:
                query = text("SELECT * FROM applications WHERE volunteer_id = :volunteer_id")
                result = await session.execute(query, {"volunteer_id": volunteer_id})
                rows = result.fetchall()
                
                return [
                    Application(
                        id=str(row.id),
                        volunteerId=str(row.volunteer_id),
                        opportunityId=str(row.opportunity_id),
                        organizationId=str(row.organization_id) if row.organization_id else None,
                        status=row.status,
                        coverLetter=row.cover_letter,
                        submittedAt=row.submitted_at,
                        reviewedAt=row.reviewed_at,
                        createdAt=row.created_at,
                        updatedAt=row.updated_at
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"[WARNING] Error finding applications for volunteer {volunteer_id}: {e}")
            return []
    
    async def find_by_opportunity(self, opportunity_id: str) -> List[Application]:
        """Find all applications for an opportunity"""
        if self.storage_backend == "postgres":
            return await self._find_by_opportunity_postgres(opportunity_id)
        else:
            return [
                app for app in self._cache.values()
                if app.opportunityId == opportunity_id
            ]
    
    async def _find_by_opportunity_postgres(self, opportunity_id: str) -> List[Application]:
        """Find applications by opportunity ID using PostgreSQL"""
        try:
            from sqlalchemy import text
            async with self.db_connection.get_session() as session:
                query = text("SELECT * FROM applications WHERE opportunity_id = :opportunity_id")
                result = await session.execute(query, {"opportunity_id": opportunity_id})
                rows = result.fetchall()
                
                return [
                    Application(
                        id=str(row.id),
                        volunteerId=str(row.volunteer_id),
                        opportunityId=str(row.opportunity_id),
                        organizationId=str(row.organization_id) if row.organization_id else None,
                        status=row.status,
                        coverLetter=row.cover_letter,
                        submittedAt=row.submitted_at,
                        reviewedAt=row.reviewed_at,
                        createdAt=row.created_at,
                        updatedAt=row.updated_at
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"[WARNING] Error finding applications for opportunity {opportunity_id}: {e}")
            return []
    
    async def list_all(self) -> List[Application]:
        """List all applications"""
        if self.storage_backend == "postgres":
            return await self._list_all_postgres()
        else:
            return list(self._cache.values())
    
    async def _list_all_postgres(self) -> List[Application]:
        """List all applications using PostgreSQL"""
        try:
            from sqlalchemy import text
            async with self.db_connection.get_session() as session:
                query = text("SELECT * FROM applications ORDER BY created_at DESC")
                result = await session.execute(query)
                rows = result.fetchall()
                
                return [
                    Application(
                        id=str(row.id),
                        volunteerId=str(row.volunteer_id),
                        opportunityId=str(row.opportunity_id),
                        organizationId=str(row.organization_id) if row.organization_id else None,
                        status=row.status,
                        coverLetter=row.cover_letter,
                        submittedAt=row.submitted_at,
                        reviewedAt=row.reviewed_at,
                        createdAt=row.created_at,
                        updatedAt=row.updated_at
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"[WARNING] Error listing applications: {e}")
            return []
    
    async def health_check(self) -> dict:
        """Health check for repository"""
        if self.storage_backend == "postgres":
            try:
                health = await self.db_connection.health_check()
                return {
                    'status': 'healthy' if health['status'] == 'healthy' else 'unhealthy',
                    'backend': 'postgres',
                    'database': health
                }
            except Exception as e:
                return {
                    'status': 'unhealthy',
                    'backend': 'postgres',
                    'error': str(e)
                }
        else:
            return {
                'status': 'healthy',
                'backend': 'file',
                'cache_size': len(self._cache) if hasattr(self, '_cache') else 0
            }