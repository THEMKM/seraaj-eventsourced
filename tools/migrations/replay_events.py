#!/usr/bin/env python3
"""
Rebuild projections from event store.

Usage:
    python tools/migrations/replay_events.py [--from-timestamp TIMESTAMP] [--aggregate-type TYPE]
    
Arguments:
    --from-timestamp: Rebuild from this timestamp (ISO format)
    --aggregate-type: Only rebuild for this aggregate type
"""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.db.connection import init_database, close_database
from infrastructure.db.event_store import event_store
from infrastructure.db.projections import projection_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventReplayManager:
    """Manages event replay and projection rebuilding"""
    
    def __init__(self):
        pass
    
    async def replay_all_events(self) -> dict:
        """Replay all events to rebuild projections"""
        logger.info("Starting full event replay...")
        
        # Get event statistics first
        stats = await self._get_event_stats()
        logger.info(f"Event statistics: {stats}")
        
        # Rebuild all projections
        results = await projection_service.rebuild_all_projections()
        
        logger.info("Full event replay completed")
        return results
    
    async def replay_from_timestamp(self, from_timestamp: datetime) -> dict:
        """Replay events from a specific timestamp"""
        logger.info(f"Starting incremental event replay from {from_timestamp}")
        
        # Get events from timestamp
        events = await event_store.get_all_events(from_timestamp=from_timestamp)
        logger.info(f"Found {len(events)} events to replay from {from_timestamp}")
        
        if not events:
            logger.info("No events found to replay")
            return {}
        
        # Process events incrementally
        results = await projection_service.rebuild_projections_from_timestamp(from_timestamp)
        
        logger.info("Incremental event replay completed")
        return results
    
    async def replay_aggregate_type(self, aggregate_type: str, from_timestamp: Optional[datetime] = None) -> dict:
        """Replay events for a specific aggregate type"""
        logger.info(f"Starting event replay for aggregate type: {aggregate_type}")
        
        # Get events for the specific aggregate type
        events = await event_store.get_all_events(
            aggregate_type=aggregate_type,
            from_timestamp=from_timestamp
        )
        
        logger.info(f"Found {len(events)} {aggregate_type} events to replay")
        
        if not events:
            logger.info(f"No {aggregate_type} events found to replay")
            return {}
        
        # Get the appropriate handler
        handler = None
        for h in projection_service.handlers:
            if any(h.handles_event_type(event.event_type) for event in events):
                handler = h
                break
        
        if not handler:
            logger.error(f"No handler found for {aggregate_type} events")
            return {}
        
        # Rebuild projections for this aggregate type
        await handler.rebuild_from_events(events)
        
        results = {aggregate_type: len(events)}
        logger.info(f"Event replay completed for {aggregate_type}: {results}")
        return results
    
    async def _get_event_stats(self) -> dict:
        """Get event statistics from the store"""
        all_events = await event_store.get_all_events()
        
        stats = {
            'total_events': len(all_events),
            'by_aggregate_type': {},
            'by_event_type': {},
            'date_range': {}
        }
        
        if all_events:
            # Group by aggregate type
            for event in all_events:
                agg_type = event.aggregate_type
                if agg_type not in stats['by_aggregate_type']:
                    stats['by_aggregate_type'][agg_type] = 0
                stats['by_aggregate_type'][agg_type] += 1
                
                # Group by event type
                evt_type = event.event_type
                if evt_type not in stats['by_event_type']:
                    stats['by_event_type'][evt_type] = 0
                stats['by_event_type'][evt_type] += 1
            
            # Date range
            timestamps = [event.occurred_at for event in all_events]
            stats['date_range'] = {
                'earliest': min(timestamps).isoformat(),
                'latest': max(timestamps).isoformat()
            }
        
        return stats
    
    async def validate_projections(self) -> dict:
        """Validate that projections are consistent with events"""
        logger.info("Validating projections against event store...")
        
        validation_results = {}
        
        # Get all events grouped by aggregate
        all_events = await event_store.get_all_events()
        aggregates = {}
        
        for event in all_events:
            key = (event.aggregate_type, event.aggregate_id)
            if key not in aggregates:
                aggregates[key] = []
            aggregates[key].append(event)
        
        # Sort events by version within each aggregate
        for key in aggregates:
            aggregates[key].sort(key=lambda e: e.version)
        
        logger.info(f"Found {len(aggregates)} unique aggregates across {len(all_events)} events")
        
        # Validate each aggregate type
        application_aggregates = {k: v for k, v in aggregates.items() if k[0] == 'Application'}
        match_aggregates = {k: v for k, v in aggregates.items() if k[0] == 'MatchSuggestion'}
        
        validation_results['applications'] = {
            'aggregate_count': len(application_aggregates),
            'event_count': sum(len(events) for events in application_aggregates.values())
        }
        
        validation_results['match_suggestions'] = {
            'aggregate_count': len(match_aggregates),
            'event_count': sum(len(events) for events in match_aggregates.values())
        }
        
        # TODO: Add actual projection validation by querying the database
        # and comparing with expected state from events
        
        logger.info(f"Projection validation completed: {validation_results}")
        return validation_results

async def main():
    """Main replay function"""
    parser = argparse.ArgumentParser(description="Replay events to rebuild projections")
    parser.add_argument('--from-timestamp', help='Replay from this timestamp (ISO format)')
    parser.add_argument('--aggregate-type', help='Only replay for this aggregate type')
    parser.add_argument('--validate-only', action='store_true', help='Only validate projections')
    parser.add_argument('--stats-only', action='store_true', help='Only show event statistics')
    
    args = parser.parse_args()
    
    try:
        # Initialize database connection
        await init_database()
        logger.info("Database connection initialized")
        
        replay_manager = EventReplayManager()
        
        if args.stats_only:
            # Only show statistics
            stats = await replay_manager._get_event_stats()
            logger.info(f"Event store statistics: {stats}")
            return
        
        if args.validate_only:
            # Only validate projections
            validation_results = await replay_manager.validate_projections()
            logger.info(f"Validation results: {validation_results}")
            return
        
        # Parse timestamp if provided
        from_timestamp = None
        if args.from_timestamp:
            try:
                from_timestamp = datetime.fromisoformat(args.from_timestamp.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid timestamp format: {e}")
                return
        
        # Run replay based on arguments
        if args.aggregate_type:
            # Replay specific aggregate type
            results = await replay_manager.replay_aggregate_type(args.aggregate_type, from_timestamp)
        elif from_timestamp:
            # Replay from timestamp
            results = await replay_manager.replay_from_timestamp(from_timestamp)
        else:
            # Full replay
            results = await replay_manager.replay_all_events()
        
        logger.info(f"Event replay completed: {results}")
        
        # Validate after replay
        validation_results = await replay_manager.validate_projections()
        logger.info(f"Post-replay validation: {validation_results}")
        
    except Exception as e:
        logger.error(f"Event replay failed: {e}")
        raise
    finally:
        await close_database()

if __name__ == "__main__":
    asyncio.run(main())