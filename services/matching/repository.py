from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import json
from pathlib import Path

from services.shared.models import MatchSuggestion

class MatchRepository:
    """Repository for match suggestions"""
    
    def __init__(self):
        self.data_file = Path("data/match_suggestions.json")
        self.history_file = Path("data/match_history.jsonl")
        self.data_file.parent.mkdir(exist_ok=True)
        self._cache: Dict[str, MatchSuggestion] = {}
        self._load()
    
    def _load(self):
        """Load match suggestions from storage"""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    for item in data:
                        suggestion = MatchSuggestion(**item)
                        self._cache[suggestion.id] = suggestion
            except (json.JSONDecodeError, TypeError, KeyError):
                # Handle corrupted data gracefully
                pass
    
    def _save(self):
        """Persist suggestions to storage"""
        data = [suggestion.model_dump() for suggestion in self._cache.values()]
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    async def save(self, suggestion: MatchSuggestion) -> MatchSuggestion:
        """Save match suggestion"""
        self._cache[suggestion.id] = suggestion
        self._save()
        
        # Log to history
        try:
            with open(self.history_file, "a") as f:
                f.write(json.dumps(suggestion.model_dump(), default=str) + "\n")
        except Exception:
            # Don't fail the save if history logging fails
            pass
        
        return suggestion
    
    async def find_by_volunteer(self, volunteer_id: str) -> List[MatchSuggestion]:
        """Find suggestions for a volunteer"""
        return [
            suggestion for suggestion in self._cache.values()
            if suggestion.volunteerId == volunteer_id
        ]
    
    async def get(self, suggestion_id: str) -> Optional[MatchSuggestion]:
        """Get suggestion by ID"""
        return self._cache.get(suggestion_id)
    
    async def update_status(self, suggestion_id: str, status: str) -> Optional[MatchSuggestion]:
        """Update suggestion status"""
        if suggestion_id in self._cache:
            self._cache[suggestion_id].status = status
            self._save()
            return self._cache[suggestion_id]
        return None