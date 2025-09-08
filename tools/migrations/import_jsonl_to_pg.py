#!/usr/bin/env python3
"""
Import existing JSONL event logs to PostgreSQL event store.

Usage: 
    python tools/migrations/import_jsonl_to_pg.py [--dry-run] [--rebuild-projections]
    
Arguments:
    --dry-run: Show what would be imported without actually doing it
    --rebuild-projections: Rebuild projections after import
"""

import argparse
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.db.connection import init_database, close_database
from infrastructure.db.event_store import event_store
from infrastructure.db.projections import projection_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONLImporter:
    """Imports JSONL event files to PostgreSQL"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.data_dir = Path("data")
        
    async def import_events(self) -> Dict[str, int]:
        """Import all JSONL files found in the data directory"""
        if self.dry_run:
            logger.info("DRY RUN - No changes will be made")
        
        results = {}
        
        # Look for JSONL event files
        jsonl_files = list(self.data_dir.glob("*_events.jsonl"))
        if not jsonl_files:
            jsonl_files = list(self.data_dir.glob("*.jsonl"))
        
        logger.info(f"Found {len(jsonl_files)} JSONL files: {[f.name for f in jsonl_files]}")
        
        for jsonl_file in jsonl_files:
            aggregate_type = self._infer_aggregate_type(jsonl_file.name)
            count = await self._import_jsonl_file(jsonl_file, aggregate_type)
            results[jsonl_file.name] = count
        
        return results
    
    def _infer_aggregate_type(self, filename: str) -> str:
        """Infer aggregate type from filename"""
        if 'application' in filename.lower():
            return 'Application'
        elif 'match' in filename.lower():
            return 'MatchSuggestion'
        elif 'auth' in filename.lower() or 'user' in filename.lower():
            return 'User'
        else:
            # Default to capitalized filename without extension
            return filename.replace('_events.jsonl', '').replace('.jsonl', '').capitalize()
    
    async def _import_jsonl_file(self, file_path: Path, aggregate_type: str) -> int:
        """Import a single JSONL file"""
        logger.info(f"Processing {file_path.name} as {aggregate_type} events")
        
        if not file_path.exists():
            logger.warning(f"File {file_path} does not exist")
            return 0
        
        events_data = []
        line_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event_data = json.loads(line)
                        events_data.append(self._transform_event_data(event_data, aggregate_type, line_num))
                        line_count += 1
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in {file_path}:{line_num}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing line {line_num} in {file_path}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return 0
        
        logger.info(f"Parsed {line_count} events from {file_path.name}")
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would import {len(events_data)} events")
            return len(events_data)
        
        # Import events in batches
        batch_size = 100
        imported_count = 0
        
        for i in range(0, len(events_data), batch_size):
            batch = events_data[i:i + batch_size]
            try:
                await event_store.append_events_batch(batch)
                imported_count += len(batch)
                logger.info(f"Imported batch {i//batch_size + 1}: {len(batch)} events")
            except Exception as e:
                logger.error(f"Error importing batch {i//batch_size + 1}: {e}")
                # Continue with next batch
                continue
        
        logger.info(f"Successfully imported {imported_count} events from {file_path.name}")
        return imported_count
    
    def _transform_event_data(self, event_data: dict, aggregate_type: str, line_num: int) -> dict:
        """Transform JSONL event data to event store format"""
        # Extract event information
        event_type = event_data.get('eventType', event_data.get('type', 'unknown'))
        timestamp = event_data.get('timestamp', event_data.get('occurredAt', datetime.utcnow().isoformat()))
        
        # Parse timestamp
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                timestamp = datetime.utcnow()
        
        # Extract aggregate ID
        aggregate_id = None
        payload = event_data.get('payload', event_data.get('data', event_data))
        
        # Try various field names for aggregate ID
        for field in ['applicationId', 'matchId', 'suggestionId', 'id', 'aggregateId']:
            if field in payload:
                try:
                    aggregate_id = uuid.UUID(payload[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        if not aggregate_id:
            # Generate a new UUID if we can't find one
            aggregate_id = uuid.uuid4()
            logger.warning(f"No aggregate ID found in line {line_num}, generated {aggregate_id}")
        
        # Extract version
        version = event_data.get('version', line_num)  # Use line number as fallback version
        
        # Clean payload - remove metadata fields
        clean_payload = dict(payload)
        for field in ['timestamp', 'occurredAt', 'eventType', 'type', 'version']:
            clean_payload.pop(field, None)
        
        return {
            'aggregate_id': aggregate_id,
            'aggregate_type': aggregate_type,
            'event_type': event_type,
            'version': version,
            'payload': clean_payload,
            'occurred_at': timestamp,
            'contracts_version': event_data.get('contractsVersion', '1.0.0')
        }

async def validate_import() -> Dict[str, Any]:
    """Validate the imported data against original JSONL files"""
    logger.info("Validating imported data...")
    
    validation_results = {}
    data_dir = Path("data")
    
    # Count events in database
    all_events = await event_store.get_all_events()
    db_counts = {}
    for event in all_events:
        if event.aggregate_type not in db_counts:
            db_counts[event.aggregate_type] = 0
        db_counts[event.aggregate_type] += 1
    
    # Count events in JSONL files
    jsonl_files = list(data_dir.glob("*_events.jsonl"))
    if not jsonl_files:
        jsonl_files = list(data_dir.glob("*.jsonl"))
    
    jsonl_counts = {}
    for jsonl_file in jsonl_files:
        aggregate_type = JSONLImporter()._infer_aggregate_type(jsonl_file.name)
        try:
            with open(jsonl_file, 'r') as f:
                count = sum(1 for line in f if line.strip())
            jsonl_counts[aggregate_type] = count
        except Exception as e:
            logger.error(f"Error reading {jsonl_file}: {e}")
    
    # Compare counts
    all_types = set(db_counts.keys()) | set(jsonl_counts.keys())
    
    for aggregate_type in all_types:
        db_count = db_counts.get(aggregate_type, 0)
        jsonl_count = jsonl_counts.get(aggregate_type, 0)
        
        validation_results[aggregate_type] = {
            'jsonl_count': jsonl_count,
            'db_count': db_count,
            'match': db_count == jsonl_count
        }
        
        if db_count == jsonl_count:
            logger.info(f"✓ {aggregate_type}: {db_count} events match")
        else:
            logger.warning(f"✗ {aggregate_type}: JSONL={jsonl_count}, DB={db_count}")
    
    return validation_results

async def main():
    """Main import function"""
    parser = argparse.ArgumentParser(description="Import JSONL events to PostgreSQL")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without doing it')
    parser.add_argument('--rebuild-projections', action='store_true', help='Rebuild projections after import')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing import')
    
    args = parser.parse_args()
    
    try:
        # Initialize database connection
        await init_database()
        logger.info("Database connection initialized")
        
        if args.validate_only:
            # Only run validation
            validation_results = await validate_import()
            logger.info(f"Validation complete: {validation_results}")
            return
        
        # Run import
        importer = JSONLImporter(dry_run=args.dry_run)
        results = await importer.import_events()
        
        logger.info(f"Import complete: {results}")
        
        if not args.dry_run:
            # Validate the import
            validation_results = await validate_import()
            logger.info(f"Validation results: {validation_results}")
            
            # Rebuild projections if requested
            if args.rebuild_projections:
                logger.info("Rebuilding projections...")
                projection_results = await projection_service.rebuild_all_projections()
                logger.info(f"Projection rebuild complete: {projection_results}")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise
    finally:
        await close_database()

if __name__ == "__main__":
    asyncio.run(main())