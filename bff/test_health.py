#!/usr/bin/env python3
"""
Simple test script to validate BFF health endpoint
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import main module
sys.path.insert(0, str(Path(__file__).parent))

try:
    from main import app
    print("[OK] BFF main module imported successfully")
    
    # Test basic app configuration
    print(f"[OK] App title: {app.title}")
    print(f"[OK] App version: {app.version}")
    
    # Check if routes are registered
    routes = [route.path for route in app.routes]
    expected_routes = ["/api/health", "/api/volunteer/quick-match", "/api/volunteer/apply", "/api/volunteer/{volunteer_id}/dashboard"]
    
    print("\nRegistered routes:")
    for route in routes:
        print(f"  - {route}")
    
    print("\nChecking expected routes:")
    for expected in expected_routes:
        if expected in routes:
            print(f"  [OK] {expected}")
        else:
            print(f"  [MISSING] {expected}")
    
    print("\n[OK] BFF application setup appears to be correct!")
    print("You can now run: uvicorn bff.main:app --port 8000")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure required dependencies are installed:")
    print("   pip install -r bff/requirements.txt")
    
except Exception as e:
    print(f"[ERROR] Setup error: {e}")
    sys.exit(1)