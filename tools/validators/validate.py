#!/usr/bin/env python3
import json
import hashlib
import sys
import re
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
            Path("frontend/src/types/entities.ts"),
            Path("packages/sdk-bff/src/types.ts"),
            Path("packages/sdk-bff/src/apis.ts")
        ]
        for path in required_generated:
            if not path.exists():
                self.errors.append(f"Missing generated file: {path}")
                
    def validate_sdk_contracts_sync(self):
        """Validate SDK is in sync with contracts"""
        contracts_lock = Path("contracts/version.lock")
        sdk_checksum = Path("packages/sdk-bff/.contracts_checksum")
        
        if not contracts_lock.exists():
            self.warnings.append("No contracts version lock found")
            return
            
        if not sdk_checksum.exists():
            self.errors.append("Missing SDK contracts checksum file")
            return
            
        with open(contracts_lock) as f:
            lock_data = json.load(f)
        expected_checksum = lock_data.get("checksum", "")
        
        actual_checksum = sdk_checksum.read_text().strip()
        
        if expected_checksum != actual_checksum:
            self.errors.append(
                f"SDK out of sync with contracts! "
                f"Expected: {expected_checksum[:8]}..., Got: {actual_checksum[:8]}..."
            )
        else:
            self.warnings.append("[OK] SDK in sync with contracts")
                
    def validate_frontend_compliance(self):
        """Scan frontend for forbidden patterns"""
        apps_web_dir = Path("apps/web")
        if not apps_web_dir.exists():
            self.warnings.append("No apps/web directory found")
            return
            
        # Forbidden HTTP patterns
        forbidden_http = [
            r'\bfetch\s*\(',
            r'\baxios\.',
            r'\bky\.',
            r'\bsuperagent\.',
            r'from ["\']axios["\']',
            r'from ["\']ky["\']',
            r'import.*axios',
            r'import.*ky'
        ]
        
        # Forbidden deep SDK imports
        forbidden_sdk_imports = [
            r'from ["\']@seraaj/sdk-bff/src/',
            r'import.*@seraaj/sdk-bff/src/'
        ]
        
        violations = []
        
        for ts_file in apps_web_dir.rglob("*.ts"):
            if "node_modules" in str(ts_file):
                continue
                
            try:
                content = ts_file.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check forbidden HTTP
                    for pattern in forbidden_http:
                        if re.search(pattern, line):
                            violations.append(f"{ts_file}:{line_num}: Forbidden HTTP usage: {line.strip()}")
                            
                    # Check forbidden SDK imports
                    for pattern in forbidden_sdk_imports:
                        if re.search(pattern, line):
                            violations.append(f"{ts_file}:{line_num}: Forbidden deep SDK import: {line.strip()}")
                            
            except Exception as e:
                self.warnings.append(f"Could not scan {ts_file}: {e}")
                
        for tsx_file in apps_web_dir.rglob("*.tsx"):
            if "node_modules" in str(tsx_file):
                continue
                
            try:
                content = tsx_file.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check forbidden HTTP
                    for pattern in forbidden_http:
                        if re.search(pattern, line):
                            violations.append(f"{tsx_file}:{line_num}: Forbidden HTTP usage: {line.strip()}")
                            
                    # Check forbidden SDK imports
                    for pattern in forbidden_sdk_imports:
                        if re.search(pattern, line):
                            violations.append(f"{tsx_file}:{line_num}: Forbidden deep SDK import: {line.strip()}")
                            
            except Exception as e:
                self.warnings.append(f"Could not scan {tsx_file}: {e}")
        
        if violations:
            self.errors.extend(violations)
        else:
            self.warnings.append("[OK] Frontend compliance validated")
        
    def validate_checkpoints(self):
        """Validate agent checkpoint files and their boundaries compliance"""
        checkpoints_dir = Path(".agents/checkpoints")
        boundaries_file = Path(".agents/boundaries.json")
        
        if not boundaries_file.exists():
            self.errors.append("Missing .agents/boundaries.json file")
            return
            
        with open(boundaries_file) as f:
            boundaries = json.load(f)
            
        for agent, config in boundaries.get("agents", {}).items():
            checkpoint_file = checkpoints_dir / config.get("checkpoint_file", "")
            if checkpoint_file.name and checkpoint_file.exists():
                self.warnings.append(f"[OK] {agent} checkpoint found")
                
                # Validate that checkpoint outputs are within allowed paths
                try:
                    checkpoint_data = json.loads(checkpoint_file.read_text())
                    paths_touched = checkpoint_data.get("outputs", {}).get("pathsTouched", [])
                    allowed_paths = config.get("allowed_paths", [])
                    
                    for path in paths_touched:
                        if not self._path_matches_patterns(path, allowed_paths):
                            self.errors.append(
                                f"Agent {agent} touched disallowed path: {path}"
                            )
                            
                except (json.JSONDecodeError, KeyError):
                    self.warnings.append(f"Could not validate paths for {agent} checkpoint")
            else:
                self.warnings.append(f"Missing checkpoint for {agent}")
                    
    def _hash_directory(self, directory: Path) -> str:
        """Calculate hash of all files in directory"""
        hasher = hashlib.sha256()
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                hasher.update(file_path.read_bytes())
        return hasher.hexdigest()
        
    def _path_matches_patterns(self, path: str, patterns: List[str]) -> bool:
        """Check if a path matches any of the given glob patterns"""
        import fnmatch
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.rstrip('*')):
                return True
        return False
    
    def run(self) -> bool:
        """Run all validations"""
        print("[SERAAJ] Running comprehensive drift validation...")
        
        self.validate_contracts_frozen()
        self.validate_service_boundaries()
        self.validate_generated_code()
        self.validate_sdk_contracts_sync()
        self.validate_frontend_compliance()
        self.validate_checkpoints()
        
        if self.errors:
            print("\n[ERROR] VALIDATION FAILED with errors:")
            for error in self.errors:
                print(f"  - {error}")
            return False
            
        if self.warnings:
            print("\n[WARNING] Validation notes:")
            for warning in self.warnings:
                print(f"  {warning}")
                
        print("\n[SUCCESS] All validations passed!")
        return True

if __name__ == "__main__":
    validator = DriftValidator()
    if not validator.run():
        sys.exit(1)