import json
import pytest
from pathlib import Path
import hashlib

try:
    from jsonschema import validate, ValidationError
except ImportError:
    ValidationError = Exception  # Fallback for environments without jsonschema

class TestContractCompliance:
    """Ensure all services comply with contracts"""
    
    def test_contracts_frozen(self):
        """Verify contracts are frozen"""
        lock_file = Path("contracts/version.lock")
        with open(lock_file) as f:
            lock = json.load(f)
        
        assert lock["frozen"] == True, "Contracts must be frozen"
        assert lock["checksum"] != "", "Checksum must be set"
        assert lock["status"] == "stable", "Status must be stable"
    
    def test_generated_code_exists(self):
        """Verify all generated code exists"""
        required_files = [
            Path("services/shared/models.py"),
            Path("frontend/src/types/entities.ts"),
            Path("packages/sdk-bff/index.ts"),
        ]
        
        optional_files = [
            Path("services/shared/events.py"),
            Path("services/shared/commands.py"),
            Path("frontend/src/types/events.ts"),
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Generated file missing: {file_path}"
            assert file_path.stat().st_size > 0, f"Generated file is empty: {file_path}"
        
        # Check optional files but don't fail if missing
        for file_path in optional_files:
            if not file_path.exists():
                print(f"Optional file missing: {file_path}")
    
    def test_service_boundaries(self):
        """Verify no cross-service imports"""
        services_dir = Path("services")
        violations = []
        
        for service_path in services_dir.iterdir():
            if service_path.is_dir() and service_path.name != "shared":
                violations.extend(self._check_imports(service_path))
        
        assert not violations, f"Service boundary violations: {violations}"
    
    def _check_imports(self, service_path: Path):
        """Check for illegal imports"""
        violations = []
        service_name = service_path.name
        
        for py_file in service_path.rglob("*.py"):
            if "generated" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                for line_num, line in enumerate(content.split("\n"), 1):
                    if "from services." in line and not line.strip().startswith("#"):
                        if f"services.{service_name}" not in line and "services.shared" not in line:
                            violations.append(f"{py_file}:{line_num}: {line.strip()}")
            except Exception as e:
                print(f"Warning: Could not parse {py_file}: {e}")
        
        return violations
    
    def test_service_manifests_exist(self):
        """Verify all services have manifests"""
        services_dir = Path("services")
        required_services = ["applications", "matching", "auth"]
        
        for service_name in required_services:
            manifest_path = services_dir / service_name / "manifest.json"
            assert manifest_path.exists(), f"Manifest missing for {service_name}"
            
            with open(manifest_path) as f:
                manifest = json.load(f)
                
            assert manifest["service"] == service_name
            assert "owns" in manifest
            assert "api_endpoints" in manifest
    
    def test_checkpoint_files_exist(self):
        """Verify all agent checkpoints exist"""
        checkpoints_dir = Path(".agents/checkpoints")
        required_checkpoints = [
            "contracts.done",
            "generation.done",
            "applications.done",
            "matching.done",
            "orchestration.done",
            "auth.done",
            "hardening.done"
        ]
        
        for checkpoint in required_checkpoints:
            checkpoint_path = checkpoints_dir / checkpoint
            assert checkpoint_path.exists(), f"Missing checkpoint: {checkpoint}"

    def test_contract_versions_aligned(self):
        """Test that all services use compatible contract versions"""
        services_dir = Path("services")
        
        for service_path in services_dir.iterdir():
            if service_path.is_dir() and service_path.name != "shared":
                manifest_path = service_path / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    
                    contracts_version = manifest.get("contracts_version", "1.0.0")
                    assert contracts_version in ["1.0.0", "1.1.0"], \
                        f"Service {service_path.name} uses unsupported contract version: {contracts_version}"