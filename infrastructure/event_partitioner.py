"""
Event partitioning strategy utilities for file-based event stores.

This module provides a simple, service-aware partitioning strategy that can be
used by tooling or publishers that want to route events to different files or
streams depending on the originating service.

Architecture notes:
- We intentionally keep this module side-effect free and optional so it can be
  adopted incrementally by services without breaking existing publishers.
- The default strategy is "by_service" derived from the eventType prefix.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PartitionResult:
    key: str
    strategy: str


class EventPartitioner:
    def __init__(self, strategy: str = "by_service"):
        self.partition_strategy = strategy

    def get_partition_key(self, event: Dict[str, Any]) -> PartitionResult:
        """
        Compute a partition key for an event. Default: by service name derived
        from eventType prefix (e.g., "application.submitted" -> "events_application").
        """
        event_type = str(event.get("eventType") or event.get("type", "")).strip()
        service_name = event_type.split(".")[0] if "." in event_type else "unknown"
        key = f"events_{service_name}" if service_name else "events_unknown"
        return PartitionResult(key=key, strategy=self.partition_strategy)

    def should_replicate_to_service(self, event: Dict[str, Any], target_service: str) -> bool:
        """
        Determine if an event should be replicated to a given service. The default
        policy replicates only events which are scoped to an organization (i.e.,
        have a non-null organizationId).
        """
        return event.get("organizationId") is not None

