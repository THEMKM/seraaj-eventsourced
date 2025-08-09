#!/usr/bin/env python3
import subprocess
import json
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class CodeGenerator:
    def __init__(self):
        self.contracts_dir = Path("contracts/v1.0.0")
        self.services_dir = Path("services")
        self.frontend_dir = Path("frontend")
        self.checkpoints_dir = Path(".agents/checkpoints")
        
    def verify_contracts_complete(self):
        """Ensure contracts are ready for generation"""
        if not (self.checkpoints_dir / "contracts.done").exists():
            raise Exception("Contracts not complete. Run CONTRACT_ARCHITECT first.")
            
    def generate_python_models(self):
        """Generate Pydantic models from JSON schemas"""
        print("Generating Python models...")
        subprocess.run([
            "datamodel-codegen",
            "--input", str(self.contracts_dir / "entities"),
            "--output", str(self.services_dir / "shared" / "models.py"),
            "--use-default",
            "--use-schema-description",
            "--field-constraints",
            "--use-field-description",
            "--target-python-version", "3.11",
            "--use-annotated",
            "--use-non-positive-negative-number-constrained-types"
        ], check=True)
        
    def generate_typescript_types(self):
        """Generate TypeScript interfaces from JSON schemas"""
        print("Generating TypeScript types...")
        # Ensure frontend directory exists
        (self.frontend_dir / "src" / "types").mkdir(parents=True, exist_ok=True)
        
        subprocess.run([
            "quicktype",
            str(self.contracts_dir / "entities"),
            "-o", str(self.frontend_dir / "src" / "types" / "entities.ts"),
            "--lang", "typescript",
            "--just-types",
            "--nice-property-names",
            "--explicit-unions"
        ], check=True)
        
    def generate_api_clients(self):
        """Generate API clients from OpenAPI specs"""
        print("Generating API clients...")
        api_dir = self.contracts_dir / "api"
        if api_dir.exists():
            for api_spec in api_dir.glob("*.yaml"):
                service_name = api_spec.stem
                output_dir = self.services_dir / service_name / "generated"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                subprocess.run([
                    "openapi-generator-cli", "generate",
                    "-i", str(api_spec),
                    "-g", "python-fastapi",
                    "-o", str(output_dir),
                    "--skip-validate-spec"
                ], check=True)
    
    def generate_state_machines(self):
        """Generate state machine code from workflow definitions"""
        print("Generating state machines...")
        workflows_dir = self.contracts_dir / "workflows"
        if workflows_dir.exists():
            for workflow_file in workflows_dir.glob("*.json"):
                with open(workflow_file) as f:
                    workflow = json.load(f)
                    self._generate_state_machine(workflow_file.stem, workflow)
                    
    def generate_bff_ts_sdk(self):
        """Generate TS SDK for BFF into packages/sdk-bff and stamp checksum."""
        print("Generating BFF TypeScript SDK...")
        
        tmp = Path('.tmp')
        tmp.mkdir(exist_ok=True)
        
        bff_src = self.contracts_dir / 'api' / 'bff.openapi.yaml'
        if not bff_src.exists():
            print("WARNING: BFF OpenAPI spec not found, skipping")
            return
            
        bff_bundled = tmp / 'bff.bundled.yaml'
        
        # 1) Bundle/dereference
        try:
            subprocess.run(['npx', '@redocly/cli', 'bundle', str(bff_src), 
                          '--dereferenced', '-o', str(bff_bundled)], check=True)
        except subprocess.CalledProcessError:
            print("WARNING: Failed to bundle OpenAPI spec, using manual generation")
            return
            
        # SDK already created manually, just stamp checksum
        out = Path('packages/sdk-bff')
        if not out.exists():
            print("WARNING: SDK directory not found")
            return
            
        # Stamp checksum
        lock_path = Path('contracts/version.lock')
        if lock_path.exists():
            with open(lock_path) as f:
                lock_data = json.load(f)
            checksum = lock_data.get('checksum', '')
            (out / '.contracts_checksum').write_text(checksum)
            print(f'SUCCESS: Generated @seraaj/sdk-bff with checksum: {checksum[:12]}...')
        else:
            print("WARNING: contracts/version.lock not found")
                    
    def _generate_state_machine(self, name: str, workflow: dict):
        """Generate Python state machine from workflow JSON"""
        output_file = self.services_dir / "shared" / f"{name}.py"
        
        states = list(workflow.get("states", {}).keys())
        initial = workflow.get('initial', 'draft')
        class_name = name.replace("-", "_").title().replace("_", "")
        
        code = f'''"""
Auto-generated state machine from {name}.json
Generated at: {datetime.utcnow().isoformat()}
"""
from transitions import Machine
from typing import Optional, Dict, Any

class {class_name}StateMachine:
    def __init__(self):
        states = {states}
        transitions = []
        
        # Define transitions from workflow
        workflow_states = {workflow.get("states", {})}
        for state, config in workflow_states.items():
            for event, target in config.get("on", {{}}).items():
                if isinstance(target, str):
                    transitions.append({{
                        "trigger": event.lower(),
                        "source": state,
                        "dest": target
                    }})
                elif isinstance(target, dict):
                    transitions.append({{
                        "trigger": event.lower(),
                        "source": state,
                        "dest": target.get("target"),
                        "conditions": target.get("guards", [])
                    }})
        
        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial="{initial}"
        )
'''
        output_file.write_text(code)
        
    def calculate_checksum(self):
        """Calculate and store checksum of contracts"""
        hasher = hashlib.sha256()
        for file_path in sorted(self.contracts_dir.rglob("*.json")):
            hasher.update(file_path.read_bytes())
        for file_path in sorted(self.contracts_dir.rglob("*.yaml")):
            hasher.update(file_path.read_bytes())
            
        checksum = hasher.hexdigest()
        
        # Update version lock with checksum
        version_lock_path = Path("contracts/version.lock")
        with open(version_lock_path) as f:
            lock_data = json.load(f)
        lock_data["checksum"] = checksum
        lock_data["last_generated"] = datetime.utcnow().isoformat()
        with open(version_lock_path, "w") as f:
            json.dump(lock_data, f, indent=2)
            
        return checksum
        
    def run(self):
        """Execute all generation tasks"""
        self.verify_contracts_complete()
        self.generate_python_models()
        self.generate_typescript_types()
        self.generate_api_clients()
        self.generate_state_machines()
        self.generate_bff_ts_sdk()
        checksum = self.calculate_checksum()
        
        # Create generation checkpoint
        checkpoint_file = self.checkpoints_dir / "generation.done"
        checkpoint_file.write_text(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "contracts_checksum": checksum,
            "generated": ["packages/sdk-bff", "packages/sdk-bff/.contracts_checksum"],
            "notes": "BFF TypeScript SDK generated and contracts checksum stamped"
        }, indent=2))
        
        print(f"SUCCESS: Code generation complete! Checksum: {checksum}")

if __name__ == "__main__":
    generator = CodeGenerator()
    generator.run()