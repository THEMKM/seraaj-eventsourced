"""
Run a smoke test by starting Auth, Applications, Matching, and BFF locally
on their designated ports, then exercising basic flows via HTTP.
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
from contextlib import suppress

import httpx
import uvicorn


def _run_uvicorn(app, host: str, port: int, log_level: str = "warning"):
    config = uvicorn.Config(app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())


async def _wait_health(url: str, timeout_s: float = 10.0) -> bool:
    t0 = time.time()
    async with httpx.AsyncClient(timeout=2.0) as client:
        while time.time() - t0 < timeout_s:
            with suppress(Exception):
                r = await client.get(url)
                if r.status_code == 200:
                    return True
            await asyncio.sleep(0.25)
    return False


async def main():
    # Keep it self-contained: avoid Redis during smoke
    os.environ.setdefault("USE_REDIS_EVENTS", "false")
    os.environ.setdefault("REQUIRE_SERVICE_AUTH", "false")

    # Import apps after env defaults
    from services.auth.api import app as auth_app
    from services.applications.api import app as applications_app
    from services.matching.api import app as matching_app
    from bff.main import app as bff_app

    # Designated hosts/ports
    auth_host, auth_port = "127.0.0.1", 8004
    applications_host, applications_port = "127.0.0.1", 8001
    matching_host, matching_port = "127.0.0.1", 8003
    bff_host, bff_port = "127.0.0.1", 8000

    # Start servers only if not already healthy
    threads = []
    if not await _wait_health(f"http://{auth_host}:{auth_port}/health", timeout_s=0.5):
        threads.append(threading.Thread(target=_run_uvicorn, args=(auth_app, auth_host, auth_port), daemon=True))
    if not await _wait_health(f"http://{applications_host}:{applications_port}/health", timeout_s=0.5):
        threads.append(threading.Thread(target=_run_uvicorn, args=(applications_app, applications_host, applications_port), daemon=True))
    if not await _wait_health(f"http://{matching_host}:{matching_port}/health", timeout_s=0.5):
        threads.append(threading.Thread(target=_run_uvicorn, args=(matching_app, matching_host, matching_port), daemon=True))
    if not await _wait_health(f"http://{bff_host}:{bff_port}/api/health", timeout_s=0.5):
        threads.append(threading.Thread(target=_run_uvicorn, args=(bff_app, bff_host, bff_port), daemon=True))
    for t in threads:
        t.start()

    # Wait for health endpoints
    ok = await _wait_health(f"http://{auth_host}:{auth_port}/health", timeout_s=15.0)
    ok &= await _wait_health(f"http://{applications_host}:{applications_port}/health", timeout_s=15.0)
    ok &= await _wait_health(f"http://{matching_host}:{matching_port}/health", timeout_s=15.0)
    ok &= await _wait_health(f"http://{bff_host}:{bff_port}/api/health", timeout_s=15.0)

    if not ok:
        print("[SMOKE] One or more services not healthy in time")
        return 1

    # Exercise a basic flow: submit application through BFF and fetch dashboard
    async with httpx.AsyncClient(timeout=5.0) as client:
        import uuid
        volunteer_id = str(uuid.uuid4())
        opportunity_id = str(uuid.uuid4())

        # Submit application via BFF
        r = await client.post(
            f"http://{bff_host}:{bff_port}/api/volunteer/apply",
            json={
                "volunteerId": volunteer_id,
                "opportunityId": opportunity_id,
                "coverLetter": "I would love to help!"
            }
        )
        print("[SMOKE] BFF apply status:", r.status_code)
        if r.status_code not in (200, 201):
            print("[SMOKE] Apply response:", r.text)
            return 2

        # Fetch dashboard via BFF
        r = await client.get(f"http://{bff_host}:{bff_port}/api/volunteer/{volunteer_id}/dashboard")
        print("[SMOKE] BFF dashboard status:", r.status_code)
        if r.status_code != 200:
            print("[SMOKE] Dashboard response:", r.text)
            return 3

    print("[SMOKE] Success: services started and basic flow works")
    return 0


if __name__ == "__main__":
    # Ensure repo root import path
    import sys
    sys.path.insert(0, os.getcwd())
    raise SystemExit(asyncio.run(main()))
