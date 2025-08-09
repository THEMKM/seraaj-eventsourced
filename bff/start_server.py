#!/usr/bin/env python3
"""
Simple script to start the BFF server for testing
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from main import app
    
    port = int(os.getenv('BFF_PORT', '8000'))
    
    print(f"[INFO] Starting Seraaj BFF server on port {port}")
    print(f"[INFO] Health endpoint: http://localhost:{port}/api/health")
    print(f"[INFO] API docs: http://localhost:{port}/docs")
    
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=port,
            log_level="info",
            reload=True
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Server failed to start: {e}")
        sys.exit(1)