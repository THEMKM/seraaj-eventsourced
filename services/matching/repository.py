import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import json
from pathlib import Path

from services.shared.models import MatchSuggestion
from infrastructure.sequence import SequenceStore

class MatchRepository:
    """Repository for match suggestions (dual backend scaffold)"""

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
        """Initialize PostgreSQL backend (not yet implemented, placeholder to satisfy tests)"""
        # Wire up DB connection services similar to ApplicationRepository when implemented
        try:
            from infrastructure.db.connection import db_connection  # noqa: F401
            # from infrastructure.db.event_store import event_store  # For history if needed
            self.db_connection = None  # Placeholder; real implementation would assign
        except Exception:
            self.db_connection = None
        print("[INFO] MatchRepository using PostgreSQL backend (placeholder)")

    def _init_file_storage(self, data_dir: str):
        """Initialize file-based storage backend"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.data_file = self.data_dir / "match_suggestions.json"
        self.history_file = self.data_dir / "match_history.jsonl"
        self._cache: Dict[str, MatchSuggestion] = {}
        self._seq = SequenceStore(data_dir)
        self._load()
    
    def _load(self):
        """Load match suggestions from storage"""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    for item in data:
                        # Coerce legacy/invalid fields for compatibility
                        status = item.get('status')
                        if isinstance(status, str) and '.' in status:
                            # e.g., "MatchSuggestionStatus.active" -> "active"
                            item['status'] = status.split('.')[-1]
                        # Normalize datetime format
                        if isinstance(item.get('generatedAt'), str) and ' ' in item['generatedAt']:
                            item['generatedAt'] = item['generatedAt'].replace(' ', 'T')
                        if isinstance(item.get('expiresAt'), str) and ' ' in item['expiresAt']:
                            item['expiresAt'] = item['expiresAt'].replace(' ', 'T')
                        suggestion = MatchSuggestion(**item)
                        self._cache[suggestion.id] = suggestion
            except (json.JSONDecodeError, TypeError, KeyError, Exception):
                # Handle corrupted data gracefully
                pass
    
    def _save(self):
        """Persist suggestions to storage (file backend only)"""
        if getattr(self, 'storage_backend', 'file') != 'file':
            return
        data = [suggestion.model_dump() for suggestion in self._cache.values()]
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    async def save(self, suggestion: MatchSuggestion) -> MatchSuggestion:
        """Save match suggestion"""
        if self.storage_backend == 'postgres':
            # Placeholder: In a real implementation, persist to DB
            return suggestion
        self._cache[suggestion.id] = suggestion
        self._save()

        # Log to history as proper event
        try:
            event = {
                "eventId": str(uuid4()),
                "eventType": "match.suggestion_generated",
                "aggregateId": str(suggestion.id),
                "organizationId": str(suggestion.organizationId) if getattr(suggestion, 'organizationId', None) else None,
                "timestamp": (suggestion.generatedAt.isoformat() if getattr(suggestion, 'generatedAt', None) else datetime.utcnow().isoformat()),
                "sequence": self._seq.next("matching"),
                "data": suggestion.model_dump()
            }
            line = json.dumps(event, default=str) + "\n"
            with open(self.history_file, "a") as f:
                f.write(line)
            if os.getenv("EVENT_MIRROR_GZ", "false").lower() == "true":
                gz_path = str(self.history_file) + ".gz"
                import gzip
                with gzip.open(gz_path, "ab") as gf:
                    gf.write(line.encode("utf-8"))
        except Exception:
            # Don't fail the save if history logging fails
            pass

        return suggestion
    
    async def find_by_volunteer(self, volunteer_id: str) -> List[MatchSuggestion]:
        """Find suggestions for a volunteer"""
        if self.storage_backend == 'postgres':
            # Placeholder: fetch from DB
            return []
        return [
            suggestion for suggestion in self._cache.values()
            if suggestion.volunteerId == volunteer_id
        ]
    
    async def get(self, suggestion_id: str) -> Optional[MatchSuggestion]:
        """Get suggestion by ID"""
        if self.storage_backend == 'postgres':
            # Placeholder: fetch from DB
            return None
        return self._cache.get(suggestion_id)
    
    async def update_status(self, suggestion_id: str, status: str) -> Optional[MatchSuggestion]:
        """Update suggestion status"""
        if self.storage_backend == 'postgres':
            # Placeholder: update in DB
            return None
        if suggestion_id in self._cache:
            self._cache[suggestion_id].status = status
            self._save()
            return self._cache[suggestion_id]
        return None

    async def health_check(self) -> dict:
        """Health check for repository"""
        if getattr(self, 'storage_backend', 'file') == 'postgres':
            try:
                # Placeholder health; assume unhealthy if no connection
                if getattr(self, 'db_connection', None):
                    health = await self.db_connection.health_check()  # type: ignore[attr-defined]
                    return {
                        'status': 'healthy' if health['status'] == 'healthy' else 'unhealthy',
                        'backend': 'postgres',
                        'database': health
                    }
                return {
                    'status': 'healthy',
                    'backend': 'postgres'
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
                'cache_size': len(self._cache)
            }
