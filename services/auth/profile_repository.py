"""
Simple JSON-backed repository for volunteer profiles managed by the Auth service.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4

from .profile_models import VolunteerProfile, UpdateVolunteerProfileRequest


class ProfileRepository:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.data_dir / "profiles.json"
        self._cache: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.store_file.exists():
            try:
                data = json.loads(self.store_file.read_text(encoding="utf-8"))
                # Keys are userId strings; values are profile dicts
                if isinstance(data, dict):
                    self._cache = data
            except Exception:
                # Corrupt file; start fresh but keep the file
                self._cache = {}

    def _persist(self):
        tmp = self.store_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cache, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
        tmp.replace(self.store_file)

    def get_by_user_id(self, user_id: UUID) -> Optional[VolunteerProfile]:
        raw = self._cache.get(str(user_id))
        if not raw:
            return None
        return VolunteerProfile(**raw)

    def upsert_for_user(self, user_id: UUID, base_name: str, base_email: str,
                        update: Optional[UpdateVolunteerProfileRequest] = None) -> VolunteerProfile:
        existing = self._cache.get(str(user_id))
        now = datetime.utcnow().isoformat()
        if existing is None:
            profile_id = str(uuid4())
            profile = {
                "id": profile_id,
                "userId": str(user_id),
                "name": base_name,
                "email": base_email,
                "phone": None,
                "location": None,
                "skills": [],
                "interests": [],
                "availability": None,
                "profileImageUrl": None,
                "createdAt": now,
                "updatedAt": None,
            }
        else:
            profile = dict(existing)

        if update:
            if update.name is not None:
                profile["name"] = update.name
            if update.email is not None:
                profile["email"] = update.email
            if update.phone is not None:
                profile["phone"] = update.phone
            if update.location is not None:
                profile["location"] = update.location
            if update.skills is not None:
                profile["skills"] = list(update.skills)
            if update.interests is not None:
                profile["interests"] = list(update.interests)
            if update.availability is not None:
                profile["availability"] = update.availability.model_dump()
            if update.profileImageUrl is not None:
                profile["profileImageUrl"] = str(update.profileImageUrl)
            profile["updatedAt"] = now

        self._cache[str(user_id)] = profile
        self._persist()
        return VolunteerProfile(**profile)

