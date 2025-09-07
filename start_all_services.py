#!/usr/bin/env python3
"""
Start all Seraaj services and the frontend for development (one-shot launcher)
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Tuple, Dict

SERVICES = [
    {
        "name": "Applications",
        "port": 8001,
        "module": "services.applications.api",
        "color": "\033[94m"  # Blue
    },
    {
        "name": "Matching", 
        "port": 8003,
        "module": "services.matching.api",
        "color": "\033[92m"  # Green
    },
    {
        "name": "Auth",
        "port": 8004,
        "module": "services.auth.api", 
        "color": "\033[93m"  # Yellow
    },
    {
        "name": "Volunteers (STUB)",
        "port": 8005,
        "module": "services.volunteers.api",
        "color": "\033[95m"  # Magenta
    },
    {
        "name": "Opportunities (STUB)",
        "port": 8006,
        "module": "services.opportunities.api",
        "color": "\033[96m"  # Cyan
    },
    {
        "name": "Organizations (STUB)", 
        "port": 8007,
        "module": "services.organizations.api",
        "color": "\033[91m"  # Red
    },
    {
        "name": "BFF",
        "port": 8000,
        "module": "bff.main",
        "color": "\033[97m"  # White
    }
]

RESET_COLOR = "\033[0m"

def print_banner():
    """Print startup banner"""
    print(f"""
{RESET_COLOR}================================================================
                       SERAAJ SERVICES
              Event-Sourced Volunteer Management
================================================================
  Phase 0-9 Complete: Auth, PostgreSQL, Redis, CI/CD, UI
================================================================
""")

def start_service(service):
    """Start a single service"""
    print(f"{service['color']}[{service['name']}]{RESET_COLOR} Starting on port {service['port']}...")
    
    try:
        # Start service in background
        # Provide targeted env overrides where needed
        env = os.environ.copy()
        if service["module"].startswith("services.matching."):
            # Ensure matching knows where Auth and Opportunities live
            env.setdefault("AUTH_SERVICE_URL", "http://localhost:8004")
            env.setdefault("OPPORTUNITIES_SERVICE_URL", "http://localhost:8006")

        process = subprocess.Popen(
            [sys.executable, "-m", service["module"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        
        return process
    except Exception as e:
        print(f"{service['color']}[{service['name']}]{RESET_COLOR} ❌ Failed to start: {e}")
        return None

def check_service_health(service):
    """Check if service is healthy"""
    import requests
    try:
        # Prefer liveness endpoints for quick checks
        if service["name"].lower() == "bff":
            url = f"http://localhost:{service['port']}/api/health/live"
        else:
            url = f"http://localhost:{service['port']}/health/live"

        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return True
    except:
        pass
    return False


def _which(cmd: str) -> Optional[str]:
    """Locate an executable on PATH (handles Windows .cmd/.exe)."""
    candidates = [cmd]
    if os.name == "nt":
        for ext in (".cmd", ".exe", ".bat"):
            candidates.append(cmd + ext)
    for c in candidates:
        path = shutil.which(c)
        if path:
            return path
    return None


def start_frontend(root: Path) -> Optional[subprocess.Popen]:
    """Start the Next.js frontend dev server and return the process."""
    web_dir = root / "apps" / "web"
    if not web_dir.exists():
        print("\033[90m[Web]\033[0m apps/web not found; skipping web start")
        return None

    env = os.environ.copy()
    env.setdefault("NEXT_PUBLIC_BFF_URL", "http://localhost:8000/api")

    pnpm = _which("pnpm")
    npm = _which("npm")

    try:
        if pnpm:
            print("\033[90m[Web]\033[0m Starting via pnpm workspace (port 3000)...")
            return subprocess.Popen(
                [pnpm, "--filter", "@seraaj/web", "dev"],
                cwd=str(root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        elif npm:
            print("\033[90m[Web]\033[0m Starting via npm in apps/web (port 3000)...")
            return subprocess.Popen(
                [npm, "run", "dev"],
                cwd=str(web_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        else:
            print("\033[90m[Web]\033[0m ?O Neither pnpm nor npm found on PATH; cannot start frontend")
            return None
    except Exception as e:
        print(f"\033[90m[Web]\033[0m ?O Failed to start: {e}")
        return None


def attach_log_reader(name: str, proc: subprocess.Popen) -> None:
    """Stream a few boot logs per process to the console."""
    def _reader():
        try:
            shown = 0
            while proc.poll() is None and shown < 6:
                line = proc.stdout.readline()
                if not line:
                    break
                print(f"[{name}] " + line.rstrip())
                shown += 1
        except Exception:
            pass

    import threading
    t = threading.Thread(target=_reader, daemon=True)
    t.start()

def main():
    print_banner()

    processes: List[Tuple[Dict[str, str], subprocess.Popen]] = []

    # Try to ensure Redis is available (best option: docker compose)
    try:
        docker = shutil.which('docker')
        if docker:
            # Prefer new syntax if available
            compose_cmd = ['docker', 'compose', 'up', '-d', 'redis']
            try:
                subprocess.run(compose_cmd, cwd=str(Path(__file__).parent), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print('[redis] Ensured via docker compose (detached)')
            except Exception:
                # Fallback to legacy docker-compose
                legacy = shutil.which('docker-compose')
                if legacy:
                    subprocess.run([legacy, 'up', '-d', 'redis'], cwd=str(Path(__file__).parent), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print('[redis] Ensured via docker-compose (detached)')
                else:
                    print('[redis] Docker found but compose command failed; continuing without redis')
        else:
            print('[redis] Docker not found; continuing without redis')
    except Exception as e:
        print(f"[redis] Skipping auto-start: {e}")

    # Start all services
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service, process))
            time.sleep(1)  # Stagger startup
            attach_log_reader(service["name"], process)
    
    if not processes:
        print("No services started successfully")
        return
    
    # Start Next.js frontend
    root = Path(__file__).parent.resolve()
    web_proc = start_frontend(root)
    if web_proc:
        processes.append(({"name": "Web", "port": 3000, "module": "apps.web", "color": "\033[90m"}, web_proc))
        attach_log_reader("Web", web_proc)

    print(f"\nWaiting for services to become healthy...")
    time.sleep(5)
    
    # Check health
    healthy_services = []
    for service, process in processes:
        if service["name"].lower() == "web":
            # Probe home page instead of /health
            try:
                import requests
                r = requests.get("http://localhost:3000", timeout=3)
                if r.status_code < 500:
                    healthy_services.append(service)
                    print(f"{service['color']}[{service['name']}]{RESET_COLOR} Healthy")
                else:
                    print(f"{service['color']}[{service['name']}]{RESET_COLOR} Not responding")
            except Exception:
                print(f"{service['color']}[{service['name']}]{RESET_COLOR} Not responding")
            continue

        if check_service_health(service):
            healthy_services.append(service)
            print(f"{service['color']}[{service['name']}]{RESET_COLOR} Healthy")
        else:
            print(f"{service['color']}[{service['name']}]{RESET_COLOR} Not responding")
    
    # Print summary
    print(f"""
================================================================
                      SERVICE SUMMARY                        
================================================================
  Services Started: {len(processes)}/8                                      
  Services Healthy: {len(healthy_services)}/8                                       
================================================================
  BFF API:       http://localhost:8000/api/health         
  Auth:          http://localhost:8004/health             
  Applications:  http://localhost:8001/health             
  Matching:      http://localhost:8003/health             
  Volunteers:    http://localhost:8005/health (STUB)      
  Opportunities: http://localhost:8006/health (STUB)      
  Organizations: http://localhost:8007/health (STUB)      
  Web (Next):    http://localhost:3000                    
================================================================
  Press Ctrl+C to stop all services                          
================================================================
""")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{RESET_COLOR}Shutting down all services...")
        for service, process in processes:
            if process.poll() is None:  # Still running
                print(f"  Stopping {service['name']}...")
                process.terminate()
        
        print("All services stopped")

if __name__ == "__main__":
    main()
