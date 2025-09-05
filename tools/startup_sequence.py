"""
Service Startup Orchestrator

Prints recommended startup order and checks readiness of each service
before proceeding to the next. This does not start the processes for you;
use it to verify environment and sequencing.

Recommended order:
  1) auth
  2) applications
  3) matching
  4) bff

Usage:
  python tools/startup_sequence.py
"""
from __future__ import annotations

import asyncio
from typing import List

from services.shared.port_config import PortConfigManager
from infrastructure.service_registry import service_registry
from infrastructure.health_checker import check_http_endpoint


RECOMMENDED_ORDER: List[str] = [
    "auth",
    "applications",
    "matching",
    "bff",
]


async def check_service_ready(name: str) -> bool:
    url = PortConfigManager.get_service_url(name) + "/health"
    return await check_http_endpoint(url, timeout=2.5)


async def main() -> None:
    # Register default services for resolution
    service_registry.register_default_services()

    print("\n=== Recommended Startup Order ===")
    for idx, svc in enumerate(RECOMMENDED_ORDER, start=1):
        url = PortConfigManager.get_service_url(svc)
        print(f" {idx}. {svc:14} -> {url}")

    print("\n=== Readiness Checks ===")
    for svc in RECOMMENDED_ORDER:
        url = PortConfigManager.get_service_url(svc) + "/health"
        ready = await check_service_ready(svc)
        print(f" {svc:14} {'[READY] ' if ready else '[WAITING] '} {url}")


if __name__ == "__main__":
    asyncio.run(main())

