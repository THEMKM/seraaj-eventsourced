#!/usr/bin/env python3
"""
Start all Seraaj services for development
"""
import os
import subprocess
import sys
import time
from pathlib import Path

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
{RESET_COLOR}╔══════════════════════════════════════════════════════════════╗
║                     🚀 SERAAJ SERVICES 🚀                    ║
║              Event-Sourced Volunteer Management              ║
╠══════════════════════════════════════════════════════════════╣
║  Phase 0-9 Complete: Auth, PostgreSQL, Redis, CI/CD, UI     ║
╚══════════════════════════════════════════════════════════════╝
""")

def start_service(service):
    """Start a single service"""
    print(f"{service['color']}[{service['name']}]{RESET_COLOR} Starting on port {service['port']}...")
    
    try:
        # Start service in background
        process = subprocess.Popen([
            sys.executable, "-m", service["module"]
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        return process
    except Exception as e:
        print(f"{service['color']}[{service['name']}]{RESET_COLOR} ❌ Failed to start: {e}")
        return None

def check_service_health(service):
    """Check if service is healthy"""
    import requests
    try:
        response = requests.get(f"http://localhost:{service['port']}/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def main():
    print_banner()
    
    processes = []
    
    # Start all services
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service, process))
            time.sleep(1)  # Stagger startup
    
    if not processes:
        print("❌ No services started successfully")
        return
    
    print(f"\n⏳ Waiting for services to become healthy...")
    time.sleep(5)
    
    # Check health
    healthy_services = []
    for service, process in processes:
        if check_service_health(service):
            healthy_services.append(service)
            print(f"{service['color']}[{service['name']}]{RESET_COLOR} ✅ Healthy")
        else:
            print(f"{service['color']}[{service['name']}]{RESET_COLOR} ⚠️  Not responding")
    
    # Print summary
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    📊 SERVICE SUMMARY                        ║
╠══════════════════════════════════════════════════════════════╣
║  Services Started: {len(processes)}/7                                      ║
║  Services Healthy: {len(healthy_services)}/7                                      ║ 
╠══════════════════════════════════════════════════════════════╣
║  🌐 BFF API:       http://localhost:8000/api/health         ║
║  🔐 Auth:          http://localhost:8004/health             ║
║  📝 Applications:  http://localhost:8001/health             ║
║  🎯 Matching:      http://localhost:8003/health             ║
║  👥 Volunteers:    http://localhost:8005/health (STUB)      ║
║  🎪 Opportunities: http://localhost:8006/health (STUB)      ║
║  🏢 Organizations: http://localhost:8007/health (STUB)      ║
╠══════════════════════════════════════════════════════════════╣
║  Press Ctrl+C to stop all services                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{RESET_COLOR}🛑 Shutting down all services...")
        for service, process in processes:
            if process.poll() is None:  # Still running
                print(f"  Stopping {service['name']}...")
                process.terminate()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()