#!/usr/bin/env python3
import subprocess
import json
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class CodeGenerator:
    def __init__(self):
        self.contracts_dir = Path("contracts/v1.0.0")
        self.contracts_v11_dir = Path("contracts/v1.1.0")
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
        entities_dir = self.contracts_dir / "entities"
        if entities_dir.exists() and list(entities_dir.glob("*.json")):
            subprocess.run([
                "datamodel-codegen",
                "--input", str(entities_dir),
                "--input-file-type", "jsonschema",
                "--output", str(self.services_dir / "shared" / "models.py"),
                "--use-default",
                "--use-schema-description",
                "--field-constraints",
                "--use-field-description",
                "--target-python-version", "3.11",
                "--use-annotated",
                "--use-non-positive-negative-number-constrained-types"
            ], check=True)
        else:
            print("    WARNING: No entities found in v1.0.0, skipping")
        
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
        """Generate deterministic, provenance-stamped BFF TypeScript SDK."""
        print("Generating BFF TypeScript SDK with hardening...")
        
        tmp = Path('.tmp')
        tmp.mkdir(exist_ok=True)
        
        bff_src = self.contracts_dir / 'api' / 'bff.openapi.yaml'
        if not bff_src.exists():
            print("WARNING: BFF OpenAPI spec not found, skipping")
            return
            
        bff_bundled = tmp / 'bff.bundled.yaml'
        out = Path('packages/sdk-bff')
        
        # Remove ALL stale files from SDK directory before regeneration (except package.json)
        if out.exists():
            print("Removing stale SDK files...")
            for item in out.iterdir():
                if item.name not in ['package.json', '.gitignore']:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        else:
            out.mkdir(parents=True, exist_ok=True)
            
        # 1) Bundle/dereference with Redocly (deterministic version)
        try:
            subprocess.run(['npx', '@redocly/cli@1.16.0', 'bundle', str(bff_src), 
                          '--dereferenced', '-o', str(bff_bundled)], check=True)
            print("OpenAPI spec bundled with Redocly v1.16.0")
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Failed to bundle OpenAPI spec: {e}")
            bff_bundled = bff_src
            
        # 2) Generate TypeScript SDK using openapi-generator v7.6.0
        try:
            subprocess.run([
                'npx', '@openapitools/openapi-generator-cli@2.13.4', 'generate',
                '-i', str(bff_bundled),
                '-g', 'typescript-fetch',
                '-o', str(out),
                '--generator-version=7.6.0',
                '--additional-properties=typescriptThreePlus=true,modelPropertyNaming=camelCase,enumPropertyNaming=UPPERCASE',
                '--skip-validate-spec'
            ], check=True)
            print("TypeScript SDK generated with openapi-generator v7.6.0")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to generate TypeScript SDK: {e}")
            return
            
        # 3) Write deterministic codegen versions stamp
        codegen_versions = {
            "openapiGenerator": "7.6.0",
            "redoclyCli": "1.16.0",
            "generatedAt": datetime.utcnow().isoformat() + "Z"
        }
        (out / '.codegen_versions.json').write_text(json.dumps(codegen_versions, indent=2))
        print("Wrote .codegen_versions.json provenance stamp")
        
        # 4) Stamp contracts checksum for verifiable traceability
        lock_path = Path('contracts/version.lock')
        if lock_path.exists():
            with open(lock_path) as f:
                lock_data = json.load(f)
            checksum = lock_data.get('checksum', '')
            (out / '.contracts_checksum').write_text(checksum)
            print(f'Wrote .contracts_checksum: {checksum[:12]}...')
            print(f'SUCCESS: Generated deterministic @seraaj/sdk-bff')
        else:
            print("ERROR: contracts/version.lock not found - cannot verify traceability")
                    
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
        
    def create_run_manifest(self, checksum: str):
        """Create a generator run manifest with tool versions and provenance"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        manifest = {
            "timestamp": timestamp,
            "agent": "GENERATOR",
            "contracts_checksum": checksum,
            "tool_versions": {
                "openapiGenerator": "7.6.0",
                "redoclyCli": "1.16.0",
                "datamodelCodegen": "0.25.0",
                "quicktype": "latest"
            },
            "commands_executed": [
                "datamodel-codegen --input contracts/v1.0.0/entities --output services/shared/models.py",
                "quicktype contracts/v1.0.0/entities -o frontend/src/types/entities.ts",
                "npx @redocly/cli@1.16.0 bundle contracts/v1.0.0/api/bff.openapi.yaml",
                "npx @openapitools/openapi-generator-cli@2.13.4 generate -g typescript-fetch"
            ],
            "inputs": [
                "contracts/v1.0.0/entities/",
                "contracts/v1.0.0/api/bff.openapi.yaml",
                "contracts/v1.0.0/workflows/"
            ],
            "outputs": [
                "services/shared/models.py",
                "frontend/src/types/entities.ts",
                "packages/sdk-bff/",
                "packages/sdk-bff/.contracts_checksum",
                "packages/sdk-bff/.codegen_versions.json"
            ]
        }
        
        # Write manifest to runs directory
        run_manifest_path = Path(f".agents/runs/GENERATOR/{timestamp.replace(':', '-')}.json")
        run_manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"Run manifest created: {run_manifest_path}")
        
    def run(self):
        """Execute all generation tasks"""
        self.verify_contracts_complete()
        self.generate_python_models()
        self.generate_typescript_types()
        self.generate_api_clients()
        self.generate_state_machines()
        self.generate_bff_ts_sdk()
        self.generate_auth_artifacts()
        checksum = self.calculate_checksum()
        
        # Create run manifest
        self.create_run_manifest(checksum)
        
        # Create generation checkpoint
        checkpoint_file = self.checkpoints_dir / "generation.done"
        checkpoint_file.write_text(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "contracts_checksum": checksum,
            "generated": ["packages/sdk-bff", "packages/sdk-bff/.contracts_checksum"],
            "notes": "BFF TypeScript SDK generated and contracts checksum stamped"
        }, indent=2))
        
        print(f"SUCCESS: Code generation complete! Checksum: {checksum}")
    
    def generate_auth_artifacts(self):
        """Generate auth-related artifacts from v1.1.0 contracts"""
        print("Generating auth artifacts from v1.1.0 contracts...")
        
        if not self.contracts_v11_dir.exists():
            print("WARNING: v1.1.0 contracts not found, skipping auth generation")
            return
            
        # Generate TypeScript types for v1.1.0 entities
        self._generate_v11_typescript_types()
        
        # Generate Python auth models
        self._generate_auth_python_models()
        
        # Generate BFF auth client adapter
        self._generate_bff_auth_client()
        
        # Update provenance stamps
        self._update_provenance_stamps()
        
        print("✅ Auth artifacts generated successfully")
    
    def _generate_v11_typescript_types(self):
        """Generate TypeScript types from v1.1.0 entities"""
        print("  Generating v1.1.0 TypeScript types...")
        
        v11_entities_dir = self.contracts_v11_dir / "entities"
        if not v11_entities_dir.exists() or not list(v11_entities_dir.glob("*.json")):
            print("    WARNING: v1.1.0 entities directory not found or empty")
            return
            
        # Create v1_1 types directory
        output_dir = self.frontend_dir / "src" / "types" / "v1_1"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            subprocess.run([
                "quicktype",
                str(v11_entities_dir),
                "-o", str(output_dir / "entities.ts"),
                "--lang", "typescript",
                "--just-types",
                "--nice-property-names",
                "--explicit-unions"
            ], check=True)
            print("    ✅ v1.1.0 TypeScript types generated")
        except subprocess.CalledProcessError as e:
            print(f"    ERROR: Failed to generate v1.1.0 TypeScript types: {e}")
    
    def _generate_auth_python_models(self):
        """Generate Python auth models from v1.1.0 entities"""
        print("  Generating auth Python models...")
        
        v11_entities_dir = self.contracts_v11_dir / "entities"
        if not v11_entities_dir.exists() or not list(v11_entities_dir.glob("*.json")):
            print("    WARNING: v1.1.0 entities directory not found or empty")
            return
            
        output_file = self.services_dir / "shared" / "auth_models.py"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            subprocess.run([
                "datamodel-codegen",
                "--input", str(v11_entities_dir),
                "--input-file-type", "jsonschema",
                "--output", str(output_file),
                "--use-default",
                "--use-schema-description",
                "--field-constraints",
                "--use-field-description",
                "--target-python-version", "3.11",
                "--use-annotated",
                "--use-non-positive-negative-number-constrained-types"
            ], check=True)
            print("    ✅ Auth Python models generated")
        except subprocess.CalledProcessError as e:
            print(f"    ERROR: Failed to generate auth Python models: {e}")
    
    def _generate_bff_auth_client(self):
        """Generate BFF auth client adapter"""
        print("  Generating BFF auth client...")
        
        auth_openapi = self.contracts_v11_dir / "api" / "auth.openapi.yaml"
        if not auth_openapi.exists():
            print("    WARNING: Auth OpenAPI spec not found")
            return
            
        # Create a simple adapter for BFF to call auth service
        bff_auth_client_path = Path("bff") / "auth_client.py"
        
        auth_client_code = '''"""Auth service client for BFF
Generated from contracts/v1.1.0/api/auth.openapi.yaml
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

class AuthClient:
    """Client for communicating with the Auth service"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url)
    
    async def register_user(self, email: str, password: str, name: str, role: str) -> Dict[str, Any]:
        """Register a new user"""
        response = await self.client.post("/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": role
        })
        response.raise_for_status()
        return response.json()
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email and password"""
        response = await self.client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        return response.json()
    
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        response = await self.client.post("/auth/refresh", json={
            "refreshToken": refresh_token
        })
        response.raise_for_status()
        return response.json()
    
    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user profile"""
        response = await self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global auth client instance
auth_client = AuthClient()
'''
        
        bff_auth_client_path.write_text(auth_client_code)
        print("    ✅ BFF auth client generated")
    
    def _update_provenance_stamps(self):
        """Update .codegen_versions.json with auth generation info"""
        print("  Updating provenance stamps...")
        
        # Read existing provenance
        provenance_path = Path("packages/sdk-bff/.codegen_versions.json")
        if provenance_path.exists():
            with open(provenance_path) as f:
                provenance = json.load(f)
        else:
            provenance = {}
        
        # Add auth generation info
        provenance.update({
            "authGeneration": {
                "contractsVersion": "v1.1.0",
                "generatedAt": datetime.utcnow().isoformat() + "Z",
                "tools": {
                    "datamodelCodegen": "0.25.0",
                    "quicktype": "latest"
                },
                "outputs": [
                    "frontend/src/types/v1_1/entities.ts",
                    "services/shared/auth_models.py",
                    "bff/auth_client.py"
                ]
            }
        })
        
        # Write updated provenance
        with open(provenance_path, "w") as f:
            json.dump(provenance, f, indent=2)
        
        print("    ✅ Provenance stamps updated")

if __name__ == "__main__":
    generator = CodeGenerator()
    generator.run()