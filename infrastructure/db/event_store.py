"""
PostgreSQL-based event store implementation for Seraaj
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .connection import db_connection, default_retry
import logging

logger = logging.getLogger(__name__)

@dataclass
class StoredEvent:
    """Represents an event stored in the event store"""
    event_id: uuid.UUID
    aggregate_type: str
    aggregate_id: uuid.UUID
    event_type: str
    occurred_at: datetime
    version: int
    payload: dict
    contracts_version: str

class EventStore:
    """PostgreSQL-based event store implementation"""
    
    def __init__(self):
        self.connection = db_connection
    
    async def append_event(
        self, 
        aggregate_id: uuid.UUID, 
        aggregate_type: str,
        event_type: str, 
        payload: dict, 
        expected_version: Optional[int] = None,
        contracts_version: str = "1.0.0"
    ) -> StoredEvent:
        """
        Append an event to the store with optimistic concurrency control
        
        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Type of the aggregate (e.g., 'Application', 'MatchSuggestion')
            event_type: Type of the event
            payload: Event payload data
            expected_version: Expected current version for optimistic locking
            contracts_version: Version of the contracts
            
        Returns:
            The stored event
            
        Raises:
            ConcurrencyError: If expected_version doesn't match actual version
        """
        
        async def _append():
            async with self.connection.get_session() as session:
                # Get current version if expected version is specified
                if expected_version is not None:
                    current_version = await self._get_current_version(session, aggregate_id)
                    if current_version != expected_version:
                        raise ConcurrencyError(
                            f"Expected version {expected_version}, but current version is {current_version}"
                        )
                    next_version = expected_version + 1
                else:
                    # Auto-increment version
                    current_version = await self._get_current_version(session, aggregate_id)
                    next_version = current_version + 1
                
                # Generate event ID
                event_id = uuid.uuid4()
                occurred_at = datetime.utcnow()
                
                # Insert the event
                query = text("""
                    INSERT INTO events (event_id, aggregate_type, aggregate_id, event_type, 
                                      occurred_at, version, payload, contracts_version)
                    VALUES (:event_id, :aggregate_type, :aggregate_id, :event_type,
                            :occurred_at, :version, :payload, :contracts_version)
                """)
                
                try:
                    await session.execute(query, {
                        'event_id': event_id,
                        'aggregate_type': aggregate_type,
                        'aggregate_id': aggregate_id,
                        'event_type': event_type,
                        'occurred_at': occurred_at,
                        'version': next_version,
                        'payload': json.dumps(payload),
                        'contracts_version': contracts_version
                    })
                    
                    return StoredEvent(
                        event_id=event_id,
                        aggregate_type=aggregate_type,
                        aggregate_id=aggregate_id,
                        event_type=event_type,
                        occurred_at=occurred_at,
                        version=next_version,
                        payload=payload,
                        contracts_version=contracts_version
                    )
                
                except IntegrityError as e:
                    if "events_aggregate_version_unique" in str(e):
                        raise ConcurrencyError(
                            f"Version {next_version} already exists for aggregate {aggregate_id}"
                        )
                    raise
        
        return await default_retry.execute(_append)
    
    async def get_events(
        self, 
        aggregate_id: uuid.UUID, 
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[StoredEvent]:
        """
        Get events for an aggregate
        
        Args:
            aggregate_id: ID of the aggregate
            from_version: Starting version (inclusive)
            to_version: Ending version (inclusive), None for all
            
        Returns:
            List of events ordered by version
        """
        
        async def _get_events():
            async with self.connection.get_session() as session:
                query = text("""
                    SELECT event_id, aggregate_type, aggregate_id, event_type,
                           occurred_at, version, payload, contracts_version
                    FROM events
                    WHERE aggregate_id = :aggregate_id 
                    AND version >= :from_version
                    """ + ("AND version <= :to_version" if to_version is not None else "") + """
                    ORDER BY version
                """)
                
                params = {
                    'aggregate_id': aggregate_id,
                    'from_version': from_version
                }
                if to_version is not None:
                    params['to_version'] = to_version
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [
                    StoredEvent(
                        event_id=row.event_id,
                        aggregate_type=row.aggregate_type,
                        aggregate_id=row.aggregate_id,
                        event_type=row.event_type,
                        occurred_at=row.occurred_at,
                        version=row.version,
                        payload=json.loads(row.payload),
                        contracts_version=row.contracts_version
                    )
                    for row in rows
                ]
        
        return await default_retry.execute(_get_events)
    
    async def get_events_by_type(
        self,
        event_type: str,
        aggregate_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[StoredEvent]:
        """
        Get events by type for projection building
        
        Args:
            event_type: Type of events to retrieve
            aggregate_type: Optional aggregate type filter
            from_timestamp: Optional timestamp filter
            limit: Optional limit on number of events
            
        Returns:
            List of events ordered by occurred_at
        """
        
        async def _get_events_by_type():
            async with self.connection.get_session() as session:
                where_clauses = ["event_type = :event_type"]
                params = {'event_type': event_type}
                
                if aggregate_type:
                    where_clauses.append("aggregate_type = :aggregate_type")
                    params['aggregate_type'] = aggregate_type
                
                if from_timestamp:
                    where_clauses.append("occurred_at >= :from_timestamp")
                    params['from_timestamp'] = from_timestamp
                
                query = text(f"""
                    SELECT event_id, aggregate_type, aggregate_id, event_type,
                           occurred_at, version, payload, contracts_version
                    FROM events
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY occurred_at
                    {f'LIMIT {limit}' if limit else ''}
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [
                    StoredEvent(
                        event_id=row.event_id,
                        aggregate_type=row.aggregate_type,
                        aggregate_id=row.aggregate_id,
                        event_type=row.event_type,
                        occurred_at=row.occurred_at,
                        version=row.version,
                        payload=json.loads(row.payload),
                        contracts_version=row.contracts_version
                    )
                    for row in rows
                ]
        
        return await default_retry.execute(_get_events_by_type)
    
    async def get_all_events(
        self,
        aggregate_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[StoredEvent]:
        """Get all events, optionally filtered"""
        
        async def _get_all_events():
            async with self.connection.get_session() as session:
                where_clauses = []
                params = {}
                
                if aggregate_type:
                    where_clauses.append("aggregate_type = :aggregate_type")
                    params['aggregate_type'] = aggregate_type
                
                if from_timestamp:
                    where_clauses.append("occurred_at >= :from_timestamp")
                    params['from_timestamp'] = from_timestamp
                
                where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
                
                query = text(f"""
                    SELECT event_id, aggregate_type, aggregate_id, event_type,
                           occurred_at, version, payload, contracts_version
                    FROM events
                    {where_sql}
                    ORDER BY occurred_at
                    {f'LIMIT {limit}' if limit else ''}
                """)
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                return [
                    StoredEvent(
                        event_id=row.event_id,
                        aggregate_type=row.aggregate_type,
                        aggregate_id=row.aggregate_id,
                        event_type=row.event_type,
                        occurred_at=row.occurred_at,
                        version=row.version,
                        payload=json.loads(row.payload),
                        contracts_version=row.contracts_version
                    )
                    for row in rows
                ]
        
        return await default_retry.execute(_get_all_events)
    
    async def append_events_batch(self, events_data: List[Dict[str, Any]]) -> List[StoredEvent]:
        """Append multiple events in a single transaction"""
        
        async def _append_batch():
            async with self.connection.get_session() as session:
                stored_events = []
                
                for event_data in events_data:
                    event_id = uuid.uuid4()
                    occurred_at = event_data.get('occurred_at', datetime.utcnow())
                    
                    query = text("""
                        INSERT INTO events (event_id, aggregate_type, aggregate_id, event_type, 
                                          occurred_at, version, payload, contracts_version)
                        VALUES (:event_id, :aggregate_type, :aggregate_id, :event_type,
                                :occurred_at, :version, :payload, :contracts_version)
                    """)
                    
                    await session.execute(query, {
                        'event_id': event_id,
                        'aggregate_type': event_data['aggregate_type'],
                        'aggregate_id': event_data['aggregate_id'],
                        'event_type': event_data['event_type'],
                        'occurred_at': occurred_at,
                        'version': event_data['version'],
                        'payload': json.dumps(event_data['payload']),
                        'contracts_version': event_data.get('contracts_version', '1.0.0')
                    })
                    
                    stored_events.append(StoredEvent(
                        event_id=event_id,
                        aggregate_type=event_data['aggregate_type'],
                        aggregate_id=event_data['aggregate_id'],
                        event_type=event_data['event_type'],
                        occurred_at=occurred_at,
                        version=event_data['version'],
                        payload=event_data['payload'],
                        contracts_version=event_data.get('contracts_version', '1.0.0')
                    ))
                
                return stored_events
        
        return await default_retry.execute(_append_batch)
    
    async def _get_current_version(self, session: AsyncSession, aggregate_id: uuid.UUID) -> int:
        """Get the current version for an aggregate"""
        query = text("""
            SELECT COALESCE(MAX(version), 0) as current_version
            FROM events
            WHERE aggregate_id = :aggregate_id
        """)
        
        result = await session.execute(query, {'aggregate_id': aggregate_id})
        row = result.fetchone()
        return row.current_version if row else 0
    
    async def get_aggregate_version(self, aggregate_id: uuid.UUID) -> int:
        """Get the current version for an aggregate (public method)"""
        async with self.connection.get_session() as session:
            return await self._get_current_version(session, aggregate_id)

class ConcurrencyError(Exception):
    """Raised when optimistic concurrency control fails"""
    pass

# Global event store instance
event_store = EventStore()