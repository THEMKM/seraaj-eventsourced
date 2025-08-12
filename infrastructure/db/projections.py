"""
Projection handlers for Seraaj event store
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Type
from abc import ABC, abstractmethod
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from .connection import db_connection, default_retry
from .event_store import StoredEvent, event_store
import logging

logger = logging.getLogger(__name__)

class ProjectionHandler(ABC):
    """Base class for projection handlers"""
    
    def __init__(self):
        self.connection = db_connection
    
    @abstractmethod
    async def handle_event(self, event: StoredEvent) -> None:
        """Handle a single event to update projections"""
        pass
    
    @abstractmethod
    async def rebuild_from_events(self, events: List[StoredEvent]) -> None:
        """Rebuild projections from a list of events"""
        pass
    
    @abstractmethod
    def handles_event_type(self, event_type: str) -> bool:
        """Check if this handler processes the given event type"""
        pass

class ApplicationProjectionHandler(ProjectionHandler):
    """Handles application projections"""
    
    def handles_event_type(self, event_type: str) -> bool:
        """Check if this handler processes application events"""
        return event_type.startswith('application.')
    
    async def handle_event(self, event: StoredEvent) -> None:
        """Handle a single application event"""
        if event.aggregate_type != 'Application':
            return
        
        async with self.connection.get_session() as session:
            if event.event_type == 'application.created':
                await self._handle_created(session, event)
            elif event.event_type == 'application.state.changed':
                await self._handle_state_changed(session, event)
            elif event.event_type == 'application.updated':
                await self._handle_updated(session, event)
    
    async def _handle_created(self, session: AsyncSession, event: StoredEvent) -> None:
        """Handle application created event"""
        payload = event.payload
        
        # Extract application data from payload
        application_data = {
            'id': event.aggregate_id,
            'volunteer_id': uuid.UUID(payload['volunteerId']),
            'opportunity_id': uuid.UUID(payload['opportunityId']),
            'organization_id': uuid.UUID(payload.get('organizationId')) if payload.get('organizationId') else None,
            'status': payload['status'],
            'cover_letter': payload.get('coverLetter'),
            'submitted_at': datetime.fromisoformat(payload['submittedAt'].replace('Z', '+00:00')) if payload.get('submittedAt') else None,
            'reviewed_at': datetime.fromisoformat(payload['reviewedAt'].replace('Z', '+00:00')) if payload.get('reviewedAt') else None,
            'created_at': event.occurred_at,
            'updated_at': event.occurred_at,
            'version': event.version
        }
        
        # Use PostgreSQL UPSERT to handle conflicts
        stmt = insert(text("""
            INSERT INTO applications (id, volunteer_id, opportunity_id, organization_id, 
                                    status, cover_letter, submitted_at, reviewed_at,
                                    created_at, updated_at, version)
            VALUES (:id, :volunteer_id, :opportunity_id, :organization_id,
                    :status, :cover_letter, :submitted_at, :reviewed_at,
                    :created_at, :updated_at, :version)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                cover_letter = EXCLUDED.cover_letter,
                submitted_at = EXCLUDED.submitted_at,
                reviewed_at = EXCLUDED.reviewed_at,
                updated_at = EXCLUDED.updated_at,
                version = EXCLUDED.version
        """))
        
        await session.execute(stmt, application_data)
    
    async def _handle_state_changed(self, session: AsyncSession, event: StoredEvent) -> None:
        """Handle application state changed event"""
        payload = event.payload
        
        # Update application status and timestamps
        updates = {
            'status': payload['newState'],
            'updated_at': event.occurred_at,
            'version': event.version
        }
        
        # Set reviewed_at for reviewing state
        if payload['newState'] == 'reviewing':
            updates['reviewed_at'] = event.occurred_at
        
        query = text("""
            UPDATE applications 
            SET status = :status, updated_at = :updated_at, version = :version
                """ + (", reviewed_at = :reviewed_at" if 'reviewed_at' in updates else "") + """
            WHERE id = :id
        """)
        
        params = {
            'id': event.aggregate_id,
            **updates
        }
        
        await session.execute(query, params)
    
    async def _handle_updated(self, session: AsyncSession, event: StoredEvent) -> None:
        """Handle application updated event"""
        payload = event.payload
        
        # Build update query dynamically based on payload
        update_fields = []
        params = {'id': event.aggregate_id, 'updated_at': event.occurred_at, 'version': event.version}
        
        if 'coverLetter' in payload:
            update_fields.append("cover_letter = :cover_letter")
            params['cover_letter'] = payload['coverLetter']
        
        if 'organizationId' in payload:
            update_fields.append("organization_id = :organization_id")
            params['organization_id'] = uuid.UUID(payload['organizationId']) if payload['organizationId'] else None
        
        if update_fields:
            query = text(f"""
                UPDATE applications 
                SET {', '.join(update_fields)}, updated_at = :updated_at, version = :version
                WHERE id = :id
            """)
            
            await session.execute(query, params)
    
    async def rebuild_from_events(self, events: List[StoredEvent]) -> None:
        """Rebuild application projections from events"""
        async with self.connection.get_session() as session:
            # Clear existing projections
            await session.execute(text("DELETE FROM applications"))
            
            # Process events in order
            for event in sorted(events, key=lambda e: (e.aggregate_id, e.version)):
                if event.aggregate_type == 'Application':
                    await self.handle_event(event)

class MatchSuggestionProjectionHandler(ProjectionHandler):
    """Handles match suggestion projections"""
    
    def handles_event_type(self, event_type: str) -> bool:
        """Check if this handler processes match suggestion events"""
        return event_type.startswith('match.') or event_type.startswith('suggestion.')
    
    async def handle_event(self, event: StoredEvent) -> None:
        """Handle a single match suggestion event"""
        if event.aggregate_type != 'MatchSuggestion':
            return
        
        async with self.connection.get_session() as session:
            if event.event_type == 'match.suggestion.created':
                await self._handle_created(session, event)
            elif event.event_type == 'match.suggestion.status.changed':
                await self._handle_status_changed(session, event)
    
    async def _handle_created(self, session: AsyncSession, event: StoredEvent) -> None:
        """Handle match suggestion created event"""
        payload = event.payload
        
        suggestion_data = {
            'id': event.aggregate_id,
            'volunteer_id': uuid.UUID(payload['volunteerId']),
            'opportunity_id': uuid.UUID(payload['opportunityId']),
            'organization_id': uuid.UUID(payload['organizationId']),
            'score': float(payload['score']),
            'score_components': json.dumps(payload['scoreComponents']),
            'explanation': json.dumps(payload['explanation']),
            'generated_at': datetime.fromisoformat(payload['generatedAt'].replace('Z', '+00:00')),
            'status': payload.get('status', 'active'),
            'created_at': event.occurred_at
        }
        
        query = text("""
            INSERT INTO match_suggestions (id, volunteer_id, opportunity_id, organization_id,
                                         score, score_components, explanation, generated_at,
                                         status, created_at)
            VALUES (:id, :volunteer_id, :opportunity_id, :organization_id,
                    :score, :score_components, :explanation, :generated_at,
                    :status, :created_at)
            ON CONFLICT (id) DO UPDATE SET
                score = EXCLUDED.score,
                score_components = EXCLUDED.score_components,
                explanation = EXCLUDED.explanation,
                status = EXCLUDED.status
        """)
        
        await session.execute(query, suggestion_data)
    
    async def _handle_status_changed(self, session: AsyncSession, event: StoredEvent) -> None:
        """Handle match suggestion status changed event"""
        payload = event.payload
        
        query = text("""
            UPDATE match_suggestions
            SET status = :status
            WHERE id = :id
        """)
        
        await session.execute(query, {
            'id': event.aggregate_id,
            'status': payload['newStatus']
        })
    
    async def rebuild_from_events(self, events: List[StoredEvent]) -> None:
        """Rebuild match suggestion projections from events"""
        async with self.connection.get_session() as session:
            # Clear existing projections
            await session.execute(text("DELETE FROM match_suggestions"))
            
            # Process events in order
            for event in sorted(events, key=lambda e: (e.aggregate_id, e.version)):
                if event.aggregate_type == 'MatchSuggestion':
                    await self.handle_event(event)

class ProjectionService:
    """Service for managing projections"""
    
    def __init__(self):
        self.handlers: List[ProjectionHandler] = [
            ApplicationProjectionHandler(),
            MatchSuggestionProjectionHandler()
        ]
    
    async def handle_event(self, event: StoredEvent) -> None:
        """Handle an event by passing it to appropriate handlers"""
        for handler in self.handlers:
            if handler.handles_event_type(event.event_type):
                try:
                    await handler.handle_event(event)
                    logger.debug(f"Successfully handled event {event.event_type} with {handler.__class__.__name__}")
                except Exception as e:
                    logger.error(f"Error handling event {event.event_type} with {handler.__class__.__name__}: {e}")
                    raise
    
    async def rebuild_all_projections(self) -> Dict[str, int]:
        """Rebuild all projections from the event store"""
        logger.info("Starting projection rebuild...")
        
        # Get all events
        all_events = await event_store.get_all_events()
        logger.info(f"Found {len(all_events)} events to process")
        
        results = {}
        
        # Rebuild application projections
        application_events = [e for e in all_events if e.aggregate_type == 'Application']
        if application_events:
            handler = ApplicationProjectionHandler()
            await handler.rebuild_from_events(application_events)
            results['applications'] = len(application_events)
            logger.info(f"Rebuilt application projections from {len(application_events)} events")
        
        # Rebuild match suggestion projections
        match_events = [e for e in all_events if e.aggregate_type == 'MatchSuggestion']
        if match_events:
            handler = MatchSuggestionProjectionHandler()
            await handler.rebuild_from_events(match_events)
            results['match_suggestions'] = len(match_events)
            logger.info(f"Rebuilt match suggestion projections from {len(match_events)} events")
        
        logger.info(f"Projection rebuild complete: {results}")
        return results
    
    async def rebuild_projections_from_timestamp(self, from_timestamp: datetime) -> Dict[str, int]:
        """Rebuild projections from a specific timestamp"""
        logger.info(f"Starting projection rebuild from {from_timestamp}")
        
        # Get events from timestamp
        events = await event_store.get_all_events(from_timestamp=from_timestamp)
        logger.info(f"Found {len(events)} events to process from {from_timestamp}")
        
        results = {}
        
        # Process events by type
        for event in events:
            await self.handle_event(event)
        
        # Count events by type
        for event in events:
            if event.aggregate_type not in results:
                results[event.aggregate_type] = 0
            results[event.aggregate_type] += 1
        
        logger.info(f"Incremental projection rebuild complete: {results}")
        return results

# Global projection service instance
projection_service = ProjectionService()