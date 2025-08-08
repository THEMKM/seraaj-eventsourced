#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path
from datetime import datetime

def freeze_contracts():
    """Freeze contracts at current state"""
    contracts_dir = Path("contracts/v1.0.0")
    lock_file = Path("contracts/version.lock")
    
    # Calculate checksum
    hasher = hashlib.sha256()
    for file_path in sorted(contracts_dir.rglob("*")):
        if file_path.is_file():
            hasher.update(file_path.read_bytes())
    
    checksum = hasher.hexdigest()
    
    # Update lock file
    with open(lock_file) as f:
        lock_data = json.load(f)
        
    lock_data["frozen"] = True
    lock_data["frozen_at"] = datetime.utcnow().isoformat()
    lock_data["checksum"] = checksum
    lock_data["status"] = "frozen"
    
    with open(lock_file, "w") as f:
        json.dump(lock_data, f, indent=2)
        
    print(f"🔒 Contracts frozen with checksum: {checksum}")
    return checksum

if __name__ == "__main__":
    freeze_contracts()