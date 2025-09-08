#!/usr/bin/env python3
"""
Start all Seraaj services and the frontend for development (one-shot launcher)
"""
import os
import shutil
import subprocess
import sys
import time
import platform
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

def ensure_docker_desktop_running():
    """Ensure Docker Desktop is running on Windows"""
    if platform.system() != "Windows":
        print("[Docker] Non-Windows platform, skipping Docker Desktop auto-start")
        return True
    
    print("[Docker] Checking if Docker Desktop is running...")
    
    # Check if docker is available and responding
    try:
        result = subprocess.run(
            ["docker", "version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            print("[Docker] SUCCESS: Docker Desktop is already running")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("[Docker] >> Docker Desktop not responding, attempting to start...")
    
    # Common Docker Desktop paths on Windows
    docker_paths = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Docker" / "Docker" / "Docker Desktop.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Docker" / "Docker" / "Docker Desktop.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Docker" / "Docker" / "Docker Desktop.exe"
    ]
    
    docker_exe = None
    for path in docker_paths:
        if path.exists():
            docker_exe = str(path)
            break
    
    if not docker_exe:
        print("[Docker] ERROR: Docker Desktop executable not found in common locations")
        print("[Docker] Please start Docker Desktop manually and try again")
        return False
    
    try:
        # Start Docker Desktop with proper visibility
        print(f"[Docker] Starting Docker Desktop from: {docker_exe}")
        # Start Docker Desktop in the background but visible to user
        subprocess.Popen([docker_exe], shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
        
        # Wait for Docker to be ready (up to 90 seconds for slower machines)
        print("[Docker] Waiting for Docker Desktop to start (up to 90 seconds)...")
        for attempt in range(90):
            try:
                result = subprocess.run(
                    ["docker", "version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=3
                )
                if result.returncode == 0:
                    print(f"[Docker] SUCCESS: Docker Desktop is ready (took {attempt + 1} seconds)")
                    print("[Docker] >> You should see Docker Desktop running in your system tray")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            time.sleep(1)
            if attempt % 10 == 9:  # Print progress every 10 seconds
                print(f"[Docker] Still waiting... ({attempt + 1}/90 seconds)")
                print("[Docker] >> If Docker Desktop GUI appears, please wait for it to finish initializing")
        
        print("[Docker] ERROR: Docker Desktop failed to start within 90 seconds")
        print("[Docker] >> Please check if Docker Desktop is installed correctly")
        return False
        
    except Exception as e:
        print(f"[Docker] ERROR: Failed to start Docker Desktop: {e}")
        return False

def kill_processes_on_ports():
    """Kill any processes occupying our required ports"""
    ports = [8000, 8001, 8003, 8004, 8005, 8006, 8007, 3000, 5432, 6379]
    
    if platform.system() == "Windows":
        print("[Ports] Checking for processes on required ports...")
        for port in ports:
            try:
                # Find process using the port
                result = subprocess.run(
                    ["netstat", "-ano"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            try:
                                subprocess.run(["taskkill", "/F", "/PID", pid], 
                                             capture_output=True, check=True)
                                print(f"[Ports] Killed process {pid} on port {port}")
                            except subprocess.CalledProcessError:
                                pass
                                
            except (subprocess.CalledProcessError, IndexError):
                pass
    else:
        # Unix-like systems
        for port in ports:
            try:
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"], 
                    capture_output=True, 
                    text=True
                )
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            subprocess.run(["kill", "-9", pid], check=True)
                            print(f"[Ports] Killed process {pid} on port {port}")
                        except subprocess.CalledProcessError:
                            pass
            except FileNotFoundError:
                # lsof not available
                pass

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


def start_background_consumer(name: str, module: str) -> Optional[subprocess.Popen]:
    """Start a background consumer (no HTTP health)."""
    try:
        print(f"\033[90m[{name}]\033[0m Starting background consumer...")
        env = os.environ.copy()
        proc = subprocess.Popen(
            [sys.executable, "-m", module],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        attach_log_reader(name, proc)
        return proc
    except Exception as e:
        print(f"\033[90m[{name}]\033[0m Failed to start: {e}")
        return None
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

def bootstrap_node_workspace(root: Path) -> bool:
    """Install workspace dependencies and build internal packages needed by the web app.

    Uses pnpm when available; falls back to npm workspaces.
    """
    print("[Node] Bootstrapping workspace dependencies...")
    pnpm = _which("pnpm")
    npm = _which("npm")

    if not pnpm and not npm:
        print("[Node] ERROR: Neither pnpm nor npm found on PATH. Please install pnpm (recommended) or Node.js/npm.")
        return False

    try:
        if pnpm:
            # Install all workspace dependencies at root
            print("[Node] Installing packages with pnpm...")
            subprocess.run([pnpm, "install"], cwd=str(root), check=True)
            # Build UI package to ensure dist/ is present for both dev and prod consumers
            print("[Node] Building @seraaj/ui package...")
            subprocess.run([pnpm, "--filter", "@seraaj/ui", "build"], cwd=str(root), check=True)
            return True
        else:
            # npm fallback using workspaces
            print("[Node] Installing packages with npm workspaces...")
            subprocess.run([npm, "install"], cwd=str(root), check=True)
            print("[Node] Building @seraaj/ui package via npm workspaces...")
            subprocess.run([npm, "run", "--workspace", "@seraaj/ui", "build"], cwd=str(root), check=True)
            return True
    except subprocess.CalledProcessError as e:
        print(f"[Node] ERROR: Workspace bootstrap failed: {e}")
        return False

def main():
    print_banner()

    # Step 0: Ensure Node workspace is ready for the frontend
    root = Path(__file__).parent.resolve()
    if not bootstrap_node_workspace(root):
        print("[Node] ERROR: Failed to prepare Node workspace. Aborting startup.")
        return 1

    # Step 1: Kill any processes on required ports
    kill_processes_on_ports()
    
    # Step 2: Ensure Docker Desktop is running
    if not ensure_docker_desktop_running():
        print("ERROR: Cannot proceed without Docker. Please start Docker Desktop manually.")
        return 1
    
    processes: List[Tuple[Dict[str, str], subprocess.Popen]] = []

    # Step 3: Start Docker services (Redis, PostgreSQL)
    print("[Docker] Starting required services (Redis, PostgreSQL)...")
    try:
        docker = shutil.which('docker')
        if docker:
            # Start essential services
            compose_cmd = ['docker', 'compose', 'up', '-d', 'redis', 'postgres']
            try:
                result = subprocess.run(
                    compose_cmd, 
                    cwd=str(Path(__file__).parent), 
                    check=True, 
                    capture_output=True,
                    text=True
                )
                print('[Docker] SUCCESS: Redis and PostgreSQL started successfully')
                print("[Docker] >> Check Docker Desktop - you should see 'seraaj-eventsourced-redis-1' and 'seraaj-eventsourced-postgres-1' containers")
                
                # Wait a moment for services to stabilize
                time.sleep(3)
                
                # Show running containers
                try:
                    ps_result = subprocess.run(
                        ['docker', 'compose', 'ps'],
                        cwd=str(Path(__file__).parent),
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"[Docker] Running containers:\n{ps_result.stdout}")
                except subprocess.CalledProcessError:
                    pass
                
                # Verify services are healthy
                print("[Docker] Waiting for services to be healthy...")
                for attempt in range(30):
                    try:
                        health_check = subprocess.run(
                            ['docker', 'compose', 'ps'],
                            cwd=str(Path(__file__).parent),
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        healthy_services = health_check.stdout.count('(healthy)')
                        if healthy_services >= 2:  # Redis + PostgreSQL
                            print(f"[Docker] SUCCESS: Services are healthy ({healthy_services}/2)")
                            print("[Docker] >> You can now see healthy containers in Docker Desktop!")
                            break
                    except subprocess.CalledProcessError:
                        pass
                    
                    time.sleep(1)
                    if attempt % 5 == 4:  # Print progress every 5 seconds
                        print(f"[Docker] Still waiting for health checks... ({attempt + 1}/30 seconds)")
                        print("[Docker] >> Check Docker Desktop containers tab for status")
                
            except subprocess.CalledProcessError as e:
                print(f'[Docker] ❌ Failed to start services: {e}')
                print(f'[Docker] stderr: {e.stderr}')
                # Try fallback to legacy docker-compose
                legacy = shutil.which('docker-compose')
                if legacy:
                    try:
                        subprocess.run(
                            [legacy, 'up', '-d', 'redis', 'postgres'], 
                            cwd=str(Path(__file__).parent), 
                            check=True
                        )
                        print('[Docker] SUCCESS: Started via legacy docker-compose')
                    except subprocess.CalledProcessError:
                        print('[Docker] ERROR: Legacy docker-compose also failed')
                        return 1
        else:
            print('[Docker] ERROR: Docker not found; cannot continue')
            return 1
    except Exception as e:
        print(f"[Docker] ERROR: Unexpected error: {e}")
        return 1

    # Start all services
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service, process))
            time.sleep(1)  # Stagger startup
            attach_log_reader(service["name"], process)

    # Optionally start background recognition/points consumer when Redis is up
    background_processes: List[Tuple[Dict[str, object], subprocess.Popen]] = []
    if os.getenv("START_RECOGNITION_CONSUMER", "false").lower() == "true":
        consumer_proc = start_background_consumer(
            name="Recognition Consumer",
            module="infrastructure.consumers.recognition_consumer",
        )
        if consumer_proc:
            background_processes.append(({"name": "Recognition Consumer", "module": "infrastructure.consumers.recognition_consumer", "color": "\033[90m"}, consumer_proc))
    
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
  Background:    {', '.join([bp[0]['name'] for bp in background_processes]) if background_processes else 'None'}
================================================================
  Press Ctrl+C to stop all services                          
================================================================
""")
    
    # Keep running until interrupted
    try:
        print("\n>> All services are running! Press Ctrl+C to stop everything.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{RESET_COLOR}>> Shutting down all services...")
        
        # Stop Python services first
        for service, process in processes:
            if process.poll() is None:  # Still running
                print(f"  Stopping {service['name']}...")
                process.terminate()
        # Stop background consumers
        for svc, proc in background_processes:
            if proc.poll() is None:
                print(f"  Stopping {svc['name']}...")
                proc.terminate()
        
        # Wait a moment for graceful shutdown
        time.sleep(2)
        
        # Force kill any remaining processes
        for service, process in processes:
            if process.poll() is None:
                print(f"  Force stopping {service['name']}...")
                process.kill()
        for svc, proc in background_processes:
            if proc.poll() is None:
                print(f"  Force stopping {svc['name']}...")
                proc.kill()
        
        # Stop Docker services
        try:
            print("  Stopping Docker services...")
            subprocess.run(
                ['docker', 'compose', 'down'], 
                cwd=str(Path(__file__).parent),
                check=False,
                capture_output=True
            )
            print("  SUCCESS: Docker services stopped")
        except Exception:
            pass
        
        print(">> All services stopped successfully")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code or 0)
