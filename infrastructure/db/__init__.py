"""
Database infrastructure module for Seraaj event store
"""

from .connection import (
    DatabaseConnection,
    DatabaseConfig,
    db_connection,
    get_db_session,
    init_database,
    close_database,
    default_retry
)

from .event_store import (
    EventStore,
    StoredEvent,
    ConcurrencyError,
    event_store
)

from .projections import (
    ProjectionHandler,
    ApplicationProjectionHandler,
    MatchSuggestionProjectionHandler,
    ProjectionService,
    projection_service
)

__all__ = [
    # Connection
    'DatabaseConnection',
    'DatabaseConfig',
    'db_connection',
    'get_db_session',
    'init_database',
    'close_database',
    'default_retry',
    
    # Event Store
    'EventStore',
    'StoredEvent',
    'ConcurrencyError',
    'event_store',
    
    # Projections
    'ProjectionHandler',
    'ApplicationProjectionHandler',
    'MatchSuggestionProjectionHandler',
    'ProjectionService',
    'projection_service'
]