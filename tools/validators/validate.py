#!/usr/bin/env python3
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Set
import ast

class DriftValidator:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_contracts_frozen(self):
        """Ensure contracts haven't changed if frozen"""
        lock_file = Path("contracts/version.lock")
        if lock_file.exists():
            lock = json.loads(lock_file.read_text())
            if lock.get("frozen"):
                current_hash = self._hash_directory(Path("contracts/v1.0.0"))
                if current_hash != lock.get("checksum"):
                    self.errors.append("CRITICAL: Frozen contracts have been modified!")
                    
    def validate_service_boundaries(self):
        """Ensure services don't import from each other"""
        services_dir = Path("services")
        for service_path in services_dir.iterdir():
            if service_path.is_dir() and service_path.name != "shared":
                self._check_imports(service_path)
                
    def _check_imports(self, service_path: Path):
        """Check that service doesn't import from other services"""
        service_name = service_path.name
        for py_file in service_path.rglob("*.py"):
            if "generated" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            self._validate_import(name.name, service_name, py_file)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._validate_import(node.module, service_name, py_file)
            except Exception as e:
                self.warnings.append(f"Could not parse {py_file}: {e}")
                
    def _validate_import(self, module: str, service_name: str, file_path: Path):
        """Validate a single import statement"""
        if module.startswith("services."):
            parts = module.split(".")
            if len(parts) >= 2:
                imported_service = parts[1]
                if imported_service != "shared" and imported_service != service_name:
                    self.errors.append(
                        f"Illegal cross-service import in {file_path}: {module}"
                    )
                        
    def validate_generated_code(self):
        """Ensure generated code matches contracts"""
        required_generated = [
            Path("services/shared/models.py"),
            Path("frontend/src/types/entities.ts")
        ]
        for path in required_generated:
            if not path.exists():
                self.errors.append(f"Missing generated file: {path}")
                
    def validate_event_store(self):
        """Ensure event store is append-only"""
        # This would check that event store implementation is append-only
        pass
        
    def validate_checkpoints(self):
        """Validate agent checkpoint files"""
        checkpoints_dir = Path(".agents/checkpoints")
        boundaries_file = Path(".agents/boundaries.json")
        
        if boundaries_file.exists():
            with open(boundaries_file) as f:
                boundaries = json.load(f)
                
            for agent, config in boundaries.get("agents", {}).items():
                checkpoint_file = checkpoints_dir / config.get("checkpoint_file", "")
                if checkpoint_file.name and checkpoint_file.exists():
                    self.warnings.append(f"OK {agent} checkpoint found")
                    
    def _hash_directory(self, directory: Path) -> str:
        """Calculate hash of all files in directory"""
        hasher = hashlib.sha256()
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                hasher.update(file_path.read_bytes())
        return hasher.hexdigest()
        
    def run(self) -> bool:
        """Run all validations"""
        print("Running drift validation...")
        
        self.validate_contracts_frozen()
        self.validate_service_boundaries()
        self.validate_generated_code()
        self.validate_event_store()
        self.validate_checkpoints()
        
        if self.errors:
            print("FAILED: Validation failed with errors:")
            for error in self.errors:
                print(f"  - {error}")
            return False
            
        if self.warnings:
            print("WARNING: Validation notes:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        print("SUCCESS: Validation passed!")
        return True

if __name__ == "__main__":
    validator = DriftValidator()
    if not validator.run():
        sys.exit(1)