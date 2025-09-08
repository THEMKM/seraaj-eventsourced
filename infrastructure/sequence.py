"""
Monotonic sequence manager for file-based event stores.

Provides per-service sequence numbers persisted to data/event_sequences.json.
This is a lightweight mechanism to aid deterministic replay ordering when
using append-only JSONL files. It is intentionally simple and local-process
safe; for distributed setups, rely on broker sequence/stream IDs instead.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from threading import Lock


class SequenceStore:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "event_sequences.json"
        self._lock = Lock()
        self._cache: Dict[str, int] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                self._cache = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self._cache = {}

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass

    def next(self, service_name: str) -> int:
        with self._lock:
            current = int(self._cache.get(service_name, 0))
            nxt = current + 1
            self._cache[service_name] = nxt
            self._save()
            return nxt

