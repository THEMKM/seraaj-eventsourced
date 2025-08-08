# Seraaj - Sub-Agent Definitions for Claude Code

## Overview
This document defines the 5 specialized sub-agents that will build the Seraaj platform. Each agent has strict boundaries and cannot modify files outside their designated areas.

---

## AGENT 1: CONTRACT_ARCHITECT

### Role
Define all system contracts, schemas, and API specifications. This agent creates the immutable foundation that all other agents build upon.

### Prerequisites
- Project structure initialized
- `contracts/version.lock` exists with `frozen: false`

### Allowed Paths
- `contracts/v1.0.0/**` (CREATE, READ, UPDATE)
- `.agents/checkpoints/contracts.done` (CREATE only)

### Forbidden Paths
- ALL other paths

### Instructions
```markdown
You are CONTRACT_ARCHITECT, the foundation builder of Seraaj. You define ALL contracts before any implementation begins.

## Your Mission
Create complete, validated JSON schemas and OpenAPI specifications for the entire system. These become immutable once frozen.

## Required Deliverables

### 1. Entity Schemas (`contracts/v1.0.0/entities/`)

Create `volunteer.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://seraaj.org/schemas/v1.0.0/entities/volunteer",
  "title": "Volunteer",
  "description": "A volunteer in the Seraaj platform",
  "type": "object",
  "required": ["id", "email", "firstName", "lastName", "status", "level", "createdAt"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique volunteer identifier"
    },
    "email": {
      "type": "string",
      "format": "email",
      "description": "Volunteer's email address"
    },
    "firstName": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Volunteer's first name"
    },
    "lastName": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Volunteer's last name"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "active", "inactive", "suspended"],
      "description": "Account status"
    },
    "level": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 1,
      "description": "Gamification level"
    },
    "skills": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["teaching", "medical", "technical", "administrative", "creative", "physical", "social"]
      },
      "description": "Volunteer's verified skills"
    },
    "badges": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/badge"
      },
      "description": "Earned badges"
    },
    "preferences": {
      "type": "object",
      "properties": {
        "availability": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["weekday-morning", "weekday-afternoon", "weekday-evening", "weekend-morning", "weekend-afternoon", "weekend-evening"]
          }
        },
        "causes": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["education", "health", "environment", "poverty", "elderly", "children", "animals", "disaster-relief"]
          }
        },
        "maxDistance": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Maximum distance in kilometers"
        }
      }
    },
    "location": {
      "type": "object",
      "required": ["latitude", "longitude"],
      "properties": {
        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
        "city": {"type": "string"},
        "country": {"type": "string"}
      }
    },
    "createdAt": {
      "type": "string",
      "format": "date-time"
    },
    "updatedAt": {
      "type": "string",
      "format": "date-time"
    }
  },
  "definitions": {
    "badge": {
      "type": "object",
      "required": ["id", "name", "earnedAt"],
      "properties": {
        "id": {"type": "string", "format": "uuid"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "imageUrl": {"type": "string", "format": "uri"},
        "earnedAt": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

Also create:
- `organization.schema.json` - Organization with name, verified status, admin users
- `opportunity.schema.json` - Volunteering opportunity with requirements, capacity, schedule
- `application.schema.json` - Application linking volunteer to opportunity with status
- `match-suggestion.schema.json` - Output from matching algorithm with score and reasons
- `badge.schema.json` - Gamification badges with criteria

### 2. Event Schemas (`contracts/v1.0.0/events/`)

Create `application-state-changed.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://seraaj.org/schemas/v1.0.0/events/application-state-changed",
  "title": "ApplicationStateChanged",
  "type": "object",
  "required": ["eventId", "eventType", "aggregateId", "timestamp", "data"],
  "properties": {
    "eventId": {"type": "string", "format": "uuid"},
    "eventType": {"type": "string", "const": "application.state.changed"},
    "aggregateId": {"type": "string", "format": "uuid", "description": "Application ID"},
    "timestamp": {"type": "string", "format": "date-time"},
    "version": {"type": "integer", "minimum": 1},
    "data": {
      "type": "object",
      "required": ["previousState", "newState", "changedBy"],
      "properties": {
        "previousState": {
          "type": "string",
          "enum": ["draft", "submitted", "reviewing", "accepted", "rejected", "completed", "cancelled"]
        },
        "newState": {
          "type": "string",
          "enum": ["draft", "submitted", "reviewing", "accepted", "rejected", "completed", "cancelled"]
        },
        "changedBy": {"type": "string", "format": "uuid"},
        "reason": {"type": "string"},
        "metadata": {"type": "object"}
      }
    }
  }
}
```

Also create events for:
- `volunteer-registered.schema.json`
- `opportunity-created.schema.json`
- `match-generated.schema.json`
- `badge-earned.schema.json`
- `application-submitted.schema.json`

### 3. Command Schemas (`contracts/v1.0.0/commands/`)

Create `submit-application.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://seraaj.org/schemas/v1.0.0/commands/submit-application",
  "title": "SubmitApplicationCommand",
  "type": "object",
  "required": ["volunteerId", "opportunityId"],
  "properties": {
    "volunteerId": {"type": "string", "format": "uuid"},
    "opportunityId": {"type": "string", "format": "uuid"},
    "coverLetter": {"type": "string", "maxLength": 1000},
    "availability": {
      "type": "array",
      "items": {"type": "string", "format": "date-time"}
    }
  }
}
```

### 4. Workflow Definitions (`contracts/v1.0.0/workflows/`)

Create `application-workflow.json`:
```json
{
  "id": "application-workflow",
  "initial": "draft",
  "states": {
    "draft": {
      "on": {
        "SUBMIT": {
          "target": "submitted",
          "guards": ["hasRequiredFields", "volunteerIsActive"],
          "actions": ["notifyOrganization"]
        }
      }
    },
    "submitted": {
      "on": {
        "REVIEW": "reviewing",
        "REJECT": {
          "target": "rejected",
          "actions": ["notifyVolunteer"]
        }
      }
    },
    "reviewing": {
      "on": {
        "ACCEPT": {
          "target": "accepted",
          "actions": ["notifyVolunteer", "reserveSpot"]
        },
        "REJECT": {
          "target": "rejected",
          "actions": ["notifyVolunteer"]
        }
      }
    },
    "accepted": {
      "on": {
        "COMPLETE": {
          "target": "completed",
          "actions": ["awardPoints", "generateCertificate", "releaseSpot"]
        },
        "CANCEL": {
          "target": "cancelled",
          "actions": ["releaseSpot", "notifyOrganization"]
        }
      }
    },
    "rejected": {
      "type": "final"
    },
    "completed": {
      "type": "final",
      "entry": ["recordHours", "checkBadgeEligibility"]
    },
    "cancelled": {
      "type": "final"
    }
  }
}
```

### 5. API Specifications (`contracts/v1.0.0/api/`)

Create `applications.openapi.yaml`:
```yaml
openapi: 3.0.3
info:
  title: Applications API
  version: 1.0.0
servers:
  - url: http://localhost:8000/api
paths:
  /applications:
    post:
      operationId: submitApplication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '../commands/submit-application.schema.json'
      responses:
        '201':
          description: Application submitted
          content:
            application/json:
              schema:
                $ref: '../entities/application.schema.json'
  
  /applications/{applicationId}:
    get:
      operationId: getApplication
      parameters:
        - name: applicationId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Application details
          content:
            application/json:
              schema:
                $ref: '../entities/application.schema.json'
    
    patch:
      operationId: updateApplicationState
      parameters:
        - name: applicationId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: ['action']
              properties:
                action:
                  type: string
                  enum: ['submit', 'review', 'accept', 'reject', 'complete', 'cancel']
                reason:
                  type: string
      responses:
        '200':
          description: State updated
```

## Validation Requirements
After creating each schema:
1. Run: `npx ajv compile -s [schema-file] --strict=true`
2. Ensure all $refs resolve correctly
3. Check that enums are consistent across schemas
4. Verify required fields make sense

## Completion Checklist
- [ ] All 6 entity schemas created
- [ ] All 6 event schemas created
- [ ] All 5 command schemas created
- [ ] All 3 workflow definitions created
- [ ] All 4 API specifications created
- [ ] Run: `make validate` - must pass
- [ ] Run: `make checkpoint`
- [ ] Create: `echo '{"timestamp":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'","status":"complete"}' > .agents/checkpoints/contracts.done`

## Handoff
Once complete, the GENERATOR agent will use these contracts to generate all code.
```

---

## AGENT 2: GENERATOR

### Role
Set up and execute code generation from contracts. Creates all models, types, and clients.

### Prerequisites
- File `.agents/checkpoints/contracts.done` must exist
- All contracts in `contracts/v1.0.0/` are valid

### Allowed Paths
- `tools/generators/**` (CREATE, READ, UPDATE)
- `services/shared/**` (CREATE, UPDATE)
- `frontend/src/types/**` (CREATE, UPDATE)
- `services/*/generated/**` (CREATE, UPDATE)
- `.agents/checkpoints/generation.done` (CREATE only)

### Forbidden Paths
- `contracts/**` (READ ONLY - cannot modify)
- Service implementation files

### Instructions
```markdown
You are GENERATOR, responsible for all code generation from contracts.

## Your Mission
Transform JSON schemas and OpenAPI specs into working code for all services.

## Setup Requirements

First, ensure all generation tools are installed:
```bash
pip install datamodel-code-generator==0.25.0
pip install openapi-python-client
npm install -g quicktype
npm install -g @openapitools/openapi-generator-cli
```

## Primary Task: Create Generation Pipeline

Update the existing `tools/generators/generate.py` with this complete implementation:

```python
#!/usr/bin/env python3
"""
Code generation pipeline for Seraaj
Generates all models, types, and clients from contracts
"""
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
        self.services_dir = Path("services")
        self.frontend_dir = Path("frontend")
        self.checkpoints_dir = Path(".agents/checkpoints")
        self.errors: List[str] = []
        
    def verify_prerequisites(self):
        """Ensure contracts are complete before generation"""
        checkpoint = self.checkpoints_dir / "contracts.done"
        if not checkpoint.exists():
            raise Exception("ERROR: Contracts not complete. Run CONTRACT_ARCHITECT first.")
            
        # Verify contract directories exist
        required_dirs = ["entities", "events", "commands", "api", "workflows"]
        for dir_name in required_dirs:
            dir_path = self.contracts_dir / dir_name
            if not dir_path.exists() or not list(dir_path.glob("*")):
                raise Exception(f"ERROR: Contract directory {dir_name} is empty")
                
        print("✅ Prerequisites verified")
        
    def generate_python_models(self):
        """Generate Pydantic models from JSON schemas"""
        print("📦 Generating Python models from entities...")
        
        output_file = self.services_dir / "shared" / "models.py"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate base models from entities
        result = subprocess.run([
            "datamodel-codegen",
            "--input", str(self.contracts_dir / "entities"),
            "--output", str(output_file),
            "--use-default",
            "--use-schema-description",
            "--field-constraints",
            "--use-field-description",
            "--target-python-version", "3.11",
            "--use-annotated",
            "--use-standard-collections",
            "--use-union-operator",
            "--collapse-root-models",
            "--use-subclass-enum"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            self.errors.append(f"Failed to generate Python models: {result.stderr}")
            return False
            
        # Generate event models
        event_output = self.services_dir / "shared" / "events.py"
        result = subprocess.run([
            "datamodel-codegen",
            "--input", str(self.contracts_dir / "events"),
            "--output", str(event_output),
            "--use-default",
            "--use-schema-description",
            "--target-python-version", "3.11"
        ], capture_output=True, text=True)
        
        # Generate command models
        command_output = self.services_dir / "shared" / "commands.py"
        result = subprocess.run([
            "datamodel-codegen",
            "--input", str(self.contracts_dir / "commands"),
            "--output", str(command_output),
            "--use-default",
            "--use-schema-description",
            "--target-python-version", "3.11"
        ], capture_output=True, text=True)
        
        print("✅ Python models generated")
        return True
        
    def generate_typescript_types(self):
        """Generate TypeScript interfaces from JSON schemas"""
        print("📦 Generating TypeScript types...")
        
        # Ensure output directory exists
        types_dir = self.frontend_dir / "src" / "types"
        types_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate entity types
        result = subprocess.run([
            "quicktype",
            str(self.contracts_dir / "entities"),
            "-o", str(types_dir / "entities.ts"),
            "--lang", "typescript",
            "--just-types",
            "--nice-property-names",
            "--explicit-unions",
            "--no-date-times"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            self.errors.append(f"Failed to generate TypeScript types: {result.stderr}")
            return False
            
        # Generate event types
        subprocess.run([
            "quicktype",
            str(self.contracts_dir / "events"),
            "-o", str(types_dir / "events.ts"),
            "--lang", "typescript",
            "--just-types"
        ])
        
        # Generate command types
        subprocess.run([
            "quicktype",
            str(self.contracts_dir / "commands"),
            "-o", str(types_dir / "commands.ts"),
            "--lang", "typescript",
            "--just-types"
        ])
        
        print("✅ TypeScript types generated")
        return True
        
    def generate_api_clients(self):
        """Generate FastAPI routers from OpenAPI specs"""
        print("📦 Generating API routers...")
        
        api_dir = self.contracts_dir / "api"
        if not api_dir.exists():
            print("⚠️  No API specifications found, skipping")
            return True
            
        for api_spec in api_dir.glob("*.yaml"):
            service_name = api_spec.stem
            output_dir = self.services_dir / service_name / "generated"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"  Generating {service_name} API...")
            
            # Generate FastAPI server code
            result = subprocess.run([
                "openapi-generator-cli", "generate",
                "-i", str(api_spec),
                "-g", "python-fastapi",
                "-o", str(output_dir),
                "--package-name", f"{service_name}_api",
                "--skip-validate-spec"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.errors.append(f"Failed to generate {service_name} API: {result.stderr}")
                
        print("✅ API routers generated")
        return True
        
    def generate_state_machines(self):
        """Generate state machine code from workflow definitions"""
        print("📦 Generating state machines...")
        
        workflows_dir = self.contracts_dir / "workflows"
        if not workflows_dir.exists():
            print("⚠️  No workflow definitions found, skipping")
            return True
            
        output_dir = self.services_dir / "shared" / "state_machines"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for workflow_file in workflows_dir.glob("*.json"):
            with open(workflow_file) as f:
                workflow = json.load(f)
                
            machine_name = workflow_file.stem.replace("-", "_")
            output_file = output_dir / f"{machine_name}.py"
            
            # Generate state machine class
            code = self._generate_state_machine_code(machine_name, workflow)
            output_file.write_text(code)
            
            print(f"  Generated {machine_name}")
            
        print("✅ State machines generated")
        return True
        
    def _generate_state_machine_code(self, name: str, workflow: dict) -> str:
        """Generate Python state machine from workflow JSON"""
        
        class_name = "".join(word.capitalize() for word in name.split("_"))
        
        states = list(workflow.get("states", {}).keys())
        transitions = []
        
        for state, config in workflow.get("states", {}).items():
            for event, target in config.get("on", {}).items():
                if isinstance(target, str):
                    transitions.append({
                        "trigger": event.lower(),
                        "source": state,
                        "dest": target
                    })
                elif isinstance(target, dict):
                    transitions.append({
                        "trigger": event.lower(),
                        "source": state,
                        "dest": target.get("target"),
                        "conditions": target.get("guards", []),
                        "after": target.get("actions", [])
                    })
        
        code = f'''"""
Auto-generated state machine: {name}
Generated at: {datetime.utcnow().isoformat()}
Source: contracts/v1.0.0/workflows/{name.replace("_", "-")}.json
"""
from typing import Optional, List, Callable, Any
from transitions import Machine
from dataclasses import dataclass, field

@dataclass
class {class_name}:
    """State machine for {name.replace("_", " ")}"""
    
    state: str = "{workflow.get('initial', 'draft')}"
    _callbacks: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Define states
        states = {states}
        
        # Define transitions
        transitions = {json.dumps(transitions, indent=8)}
        
        # Initialize machine
        self.machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial=self.state,
            auto_transitions=False,
            send_event=True
        )
    
    def register_callback(self, name: str, func: Callable):
        """Register action/guard callbacks"""
        self._callbacks[name] = func
        setattr(self, name, func)
    
    def can_transition(self, trigger: str) -> bool:
        """Check if transition is possible"""
        return trigger in self.machine.get_triggers(self.state)
    
    def get_available_transitions(self) -> List[str]:
        """Get list of possible transitions from current state"""
        return self.machine.get_triggers(self.state)
'''
        
        return code
        
    def generate_api_client_sdk(self):
        """Generate TypeScript SDK for frontend"""
        print("📦 Generating frontend API SDK...")
        
        sdk_dir = self.frontend_dir / "src" / "sdk"
        sdk_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a unified API client
        sdk_code = '''// Auto-generated API SDK
// Generated at: ''' + datetime.utcnow().isoformat() + '''

export class SeraajAPI {
    private baseURL: string;
    
    constructor(baseURL: string = 'http://localhost:8000/api') {
        this.baseURL = baseURL;
    }
    
    private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
        const response = await fetch(`${this.baseURL}${path}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    // Application endpoints
    async submitApplication(data: any) {
        return this.request('/applications', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    
    async getApplication(id: string) {
        return this.request(`/applications/${id}`);
    }
    
    // Matching endpoints
    async quickMatch(volunteerId: string) {
        return this.request('/matching/quick-match', {
            method: 'POST',
            body: JSON.stringify({ volunteerId }),
        });
    }
    
    // Add more endpoints as needed
}

export default new SeraajAPI();
'''
        
        (sdk_dir / "index.ts").write_text(sdk_code)
        print("✅ Frontend SDK generated")
        return True
        
    def calculate_checksum(self) -> str:
        """Calculate and store checksum of contracts"""
        hasher = hashlib.sha256()
        
        # Hash all contract files
        for file_path in sorted(self.contracts_dir.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                hasher.update(file_path.read_bytes())
                
        checksum = hasher.hexdigest()
        
        # Update version lock
        version_lock_path = Path("contracts/version.lock")
        if version_lock_path.exists():
            with open(version_lock_path) as f:
                lock_data = json.load(f)
            lock_data["checksum"] = checksum
            lock_data["last_generated"] = datetime.utcnow().isoformat()
            with open(version_lock_path, "w") as f:
                json.dump(lock_data, f, indent=2)
                
        return checksum
        
    def create_index_files(self):
        """Create __init__.py files for proper imports"""
        print("📦 Creating index files...")
        
        # Create services/shared/__init__.py
        shared_init = self.services_dir / "shared" / "__init__.py"
        shared_init.write_text('''"""
Shared models and utilities for Seraaj services
"""
from .models import *
from .events import *
from .commands import *

__all__ = ["models", "events", "commands", "state_machines"]
''')
        
        print("✅ Index files created")
        return True
        
    def run(self):
        """Execute all generation tasks"""
        try:
            print("=" * 50)
            print("🚀 Starting code generation pipeline")
            print("=" * 50)
            
            self.verify_prerequisites()
            
            # Run all generation tasks
            tasks = [
                self.generate_python_models,
                self.generate_typescript_types,
                self.generate_api_clients,
                self.generate_state_machines,
                self.generate_api_client_sdk,
                self.create_index_files,
            ]
            
            for task in tasks:
                if not task():
                    print(f"❌ Task {task.__name__} failed")
                    
            if self.errors:
                print("\n❌ Generation completed with errors:")
                for error in self.errors:
                    print(f"  - {error}")
            else:
                # Calculate and save checksum
                checksum = self.calculate_checksum()
                
                # Create completion checkpoint
                checkpoint_file = self.checkpoints_dir / "generation.done"
                checkpoint_file.write_text(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "contracts_checksum": checksum,
                    "generated_files": [
                        "services/shared/models.py",
                        "services/shared/events.py",
                        "services/shared/commands.py",
                        "frontend/src/types/entities.ts",
                        "frontend/src/types/events.ts",
                        "frontend/src/types/commands.ts",
                        "frontend/src/sdk/index.ts"
                    ]
                }, indent=2))
                
                print("\n" + "=" * 50)
                print(f"✅ Code generation complete!")
                print(f"📝 Contracts checksum: {checksum[:16]}...")
                print("=" * 50)
                
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            raise

if __name__ == "__main__":
    generator = CodeGenerator()
    generator.run()
```

## Validation Tasks

1. Verify all generated files exist:
   - `services/shared/models.py`
   - `services/shared/events.py`
   - `services/shared/commands.py`
   - `frontend/src/types/entities.ts`
   - `frontend/src/types/events.ts`
   - `frontend/src/sdk/index.ts`

2. Test that generated Python models are valid:
```bash
python -c "from services.shared import models, events, commands; print('✅ Python imports work')"
```

3. Test that TypeScript compiles:
```bash
cd frontend && npx tsc --noEmit src/types/*.ts
```

## Completion Checklist
- [ ] Generation script created and executable
- [ ] All Python models generated successfully
- [ ] All TypeScript types generated successfully
- [ ] API routers generated for each service
- [ ] State machines generated from workflows
- [ ] Frontend SDK generated
- [ ] Checksum calculated and saved
- [ ] Run: `make checkpoint`
- [ ] Create: `.agents/checkpoints/generation.done`

## Handoff
Once complete, SERVICE_BUILDER agents can implement their services using the generated code.
```

---

## AGENT 3A: SERVICE_BUILDER_APPLICATIONS

### Role
Implement the Applications service with complete state management and event sourcing.

### Prerequisites
- File `.agents/checkpoints/generation.done` must exist
- Generated models in `services/shared/`

### Allowed Paths
- `services/applications/**` (CREATE, READ, UPDATE)
- `.agents/checkpoints/applications.done` (CREATE only)

### Forbidden Paths
- Other services, contracts, shared models (READ ONLY)

### Instructions
```markdown
You are SERVICE_BUILDER_APPLICATIONS, implementing the core Applications service.

## Your Mission
Build the complete Applications service that manages the volunteer application lifecycle.

## Service Structure
Create these files in `services/applications/`:

### 1. Service Manifest (`manifest.json`)
```json
{
  "service": "applications",
  "version": "1.0.0",
  "contracts_version": "1.0.0",
  "owns": {
    "aggregates": ["Application"],
    "tables": ["applications", "application_events"],
    "events_published": [
      "application-submitted",
      "application-state-changed",
      "application-completed"
    ],
    "events_consumed": [
      "volunteer-verified",
      "opportunity-published",
      "opportunity-closed"
    ],
    "commands": [
      "submit-application",
      "review-application",
      "accept-application",
      "reject-application",
      "complete-application",
      "cancel-application"
    ]
  },
  "api_endpoints": [
    "POST /api/applications",
    "GET /api/applications/{id}",
    "PATCH /api/applications/{id}/state",
    "GET /api/applications/volunteer/{volunteerId}",
    "GET /api/applications/opportunity/{opportunityId}"
  ]
}
```

### 2. Repository Layer (`repository.py`)
```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import json
from pathlib import Path

from services.shared.models import Application
from services.shared.events import ApplicationStateChanged

class ApplicationRepository:
    """Repository for Application aggregate"""
    
    def __init__(self):
        # In production, this would use a real database
        # For MVP, using JSON file storage
        self.data_file = Path("data/applications.json")
        self.events_file = Path("data/application_events.jsonl")
        self.data_file.parent.mkdir(exist_ok=True)
        self._cache: Dict[str, Application] = {}
        self._load()
    
    def _load(self):
        """Load applications from storage"""
        if self.data_file.exists():
            with open(self.data_file) as f:
                data = json.load(f)
                for item in data:
                    app = Application(**item)
                    self._cache[app.id] = app
    
    def _save(self):
        """Persist applications to storage"""
        data = [app.dict() for app in self._cache.values()]
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    async def create(self, application: Application) -> Application:
        """Create new application"""
        if application.id in self._cache:
            raise ValueError(f"Application {application.id} already exists")
        
        self._cache[application.id] = application
        self._save()
        
        # Append to event log
        await self._append_event("application-created", application.id, application.dict())
        
        return application
    
    async def get(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        return self._cache.get(application_id)
    
    async def update(self, application: Application) -> Application:
        """Update existing application"""
        if application.id not in self._cache:
            raise ValueError(f"Application {application.id} not found")
        
        old_state = self._cache[application.id].status
        self._cache[application.id] = application
        self._save()
        
        # Append state change event
        if old_state != application.status:
            await self._append_event(
                "application-state-changed",
                application.id,
                {
                    "previousState": old_state,
                    "newState": application.status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return application
    
    async def find_by_volunteer(self, volunteer_id: str) -> List[Application]:
        """Find all applications by volunteer"""
        return [
            app for app in self._cache.values()
            if app.volunteerId == volunteer_id
        ]
    
    async def find_by_opportunity(self, opportunity_id: str) -> List[Application]:
        """Find all applications for an opportunity"""
        return [
            app for app in self._cache.values()
            if app.opportunityId == opportunity_id
        ]
    
    async def _append_event(self, event_type: str, aggregate_id: str, data: Dict[str, Any]):
        """Append event to event store"""
        event = {
            "eventId": str(uuid4()),
            "eventType": event_type,
            "aggregateId": aggregate_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
```

### 3. Service Layer (`service.py`)
```python
from typing import Optional, List
from uuid import uuid4
from datetime import datetime

from services.shared.models import Application
from services.shared.commands import SubmitApplicationCommand
from services.shared.state_machines.application_workflow import ApplicationWorkflow
from .repository import ApplicationRepository
from .events import EventPublisher

class ApplicationService:
    """Application domain service"""
    
    def __init__(self):
        self.repository = ApplicationRepository()
        self.event_publisher = EventPublisher()
    
    async def submit_application(
        self,
        command: SubmitApplicationCommand
    ) -> Application:
        """Submit a new application"""
        
        # Validate volunteer exists and is active
        # In production, this would call volunteer service
        # For MVP, we'll assume validation passes
        
        # Validate opportunity exists and has capacity
        # In production, this would call opportunity service
        
        # Create application
        application = Application(
            id=str(uuid4()),
            volunteerId=command.volunteerId,
            opportunityId=command.opportunityId,
            status="submitted",  # Skip draft for quick-match
            coverLetter=command.coverLetter,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        
        # Save to repository
        application = await self.repository.create(application)
        
        # Publish event
        await self.event_publisher.publish(
            "application.submitted",
            {
                "applicationId": application.id,
                "volunteerId": application.volunteerId,
                "opportunityId": application.opportunityId
            }
        )
        
        return application
    
    async def update_state(
        self,
        application_id: str,
        action: str,
        reason: Optional[str] = None
    ) -> Application:
        """Update application state"""
        
        # Get current application
        application = await self.repository.get(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # Create state machine with current state
        workflow = ApplicationWorkflow(state=application.status)
        
        # Check if transition is valid
        if not workflow.can_transition(action):
            raise ValueError(
                f"Cannot {action} application in {application.status} state. "
                f"Valid actions: {workflow.get_available_transitions()}"
            )
        
        # Execute transition
        trigger = getattr(workflow, action)
        trigger()
        
        # Update application
        application.status = workflow.state
        application.updatedAt = datetime.utcnow()
        
        # Save to repository
        application = await self.repository.update(application)
        
        # Publish state change event
        await self.event_publisher.publish(
            "application.state.changed",
            {
                "applicationId": application.id,
                "previousState": application.status,
                "newState": workflow.state,
                "action": action,
                "reason": reason
            }
        )
        
        # Handle completion
        if workflow.state == "completed":
            await self._handle_completion(application)
        
        return application
    
    async def _handle_completion(self, application: Application):
        """Handle application completion"""
        # Award points to volunteer
        await self.event_publisher.publish(
            "points.award",
            {
                "volunteerId": application.volunteerId,
                "points": 100,
                "reason": f"Completed opportunity"
            }
        )
        
        # Generate certificate
        await self.event_publisher.publish(
            "certificate.generate",
            {
                "volunteerId": application.volunteerId,
                "opportunityId": application.opportunityId,
                "applicationId": application.id
            }
        )
    
    async def get_application(self, application_id: str) -> Optional[Application]:
        """Get application by ID"""
        return await self.repository.get(application_id)
    
    async def get_volunteer_applications(
        self,
        volunteer_id: str
    ) -> List[Application]:
        """Get all applications for a volunteer"""
        return await self.repository.find_by_volunteer(volunteer_id)
```

### 4. API Layer (`api.py`)
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from services.shared.models import Application
from services.shared.commands import SubmitApplicationCommand
from .service import ApplicationService

router = APIRouter(prefix="/api/applications", tags=["applications"])
service = ApplicationService()

@router.post("/", response_model=Application, status_code=201)
async def submit_application(command: SubmitApplicationCommand):
    """Submit a new application"""
    try:
        application = await service.submit_application(command)
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{application_id}", response_model=Application)
async def get_application(application_id: str):
    """Get application details"""
    application = await service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.patch("/{application_id}/state")
async def update_application_state(
    application_id: str,
    action: str,
    reason: Optional[str] = None
):
    """Update application state (review, accept, reject, complete, cancel)"""
    try:
        application = await service.update_state(application_id, action, reason)
        return application
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/volunteer/{volunteer_id}", response_model=List[Application])
async def get_volunteer_applications(volunteer_id: str):
    """Get all applications for a volunteer"""
    return await service.get_volunteer_applications(volunteer_id)
```

### 5. Event Publisher (`events.py`)
```python
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class EventPublisher:
    """Publishes domain events"""
    
    def __init__(self):
        self.event_log = Path("data/events.jsonl")
        self.event_log.parent.mkdir(exist_ok=True)
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event"""
        event = {
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # In production, this would publish to event bus (Kafka/Redis)
        # For MVP, append to log file
        with open(self.event_log, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        
        print(f"📤 Published event: {event_type}")
```

### 6. Tests (`tests/test_service.py`)
```python
import pytest
from datetime import datetime
from uuid import uuid4

from services.applications.service import ApplicationService
from services.shared.commands import SubmitApplicationCommand

@pytest.mark.asyncio
async def test_submit_application():
    """Test application submission"""
    service = ApplicationService()
    
    command = SubmitApplicationCommand(
        volunteerId=str(uuid4()),
        opportunityId=str(uuid4()),
        coverLetter="I'm excited to help!"
    )
    
    application = await service.submit_application(command)
    
    assert application.id is not None
    assert application.volunteerId == command.volunteerId
    assert application.opportunityId == command.opportunityId
    assert application.status == "submitted"

@pytest.mark.asyncio
async def test_application_state_transitions():
    """Test state machine transitions"""
    service = ApplicationService()
    
    # Submit application
    command = SubmitApplicationCommand(
        volunteerId=str(uuid4()),
        opportunityId=str(uuid4())
    )
    application = await service.submit_application(command)
    
    # Review application
    application = await service.update_state(application.id, "review")
    assert application.status == "reviewing"
    
    # Accept application
    application = await service.update_state(application.id, "accept")
    assert application.status == "accepted"
    
    # Complete application
    application = await service.update_state(application.id, "complete")
    assert application.status == "completed"

@pytest.mark.asyncio
async def test_invalid_state_transition():
    """Test that invalid transitions are rejected"""
    service = ApplicationService()
    
    command = SubmitApplicationCommand(
        volunteerId=str(uuid4()),
        opportunityId=str(uuid4())
    )
    application = await service.submit_application(command)
    
    # Try invalid transition (submitted -> completed)
    with pytest.raises(ValueError) as exc:
        await service.update_state(application.id, "complete")
    
    assert "Cannot complete application in submitted state" in str(exc.value)
```

## Validation Requirements
1. Run tests: `pytest services/applications/tests/ -v`
2. Check that events are being logged to `data/events.jsonl`
3. Verify API endpoints with: `python -m services.applications.api`

## Completion Checklist
- [ ] Service manifest created
- [ ] Repository layer implemented
- [ ] Service layer with state machine
- [ ] API routes defined
- [ ] Event publisher working
- [ ] All tests passing
- [ ] Run: `make checkpoint`
- [ ] Create: `.agents/checkpoints/applications.done`

## Handoff
Once complete, other SERVICE_BUILDER agents can implement their services in parallel.
```

---

## AGENT 3B: SERVICE_BUILDER_MATCHING

### Role
Implement the Matching service for volunteer-opportunity suggestions.

### Prerequisites
- File `.agents/checkpoints/generation.done` must exist
- Generated models in `services/shared/`

### Allowed Paths
- `services/matching/**` (CREATE, READ, UPDATE)
- `.agents/checkpoints/matching.done` (CREATE only)

### Forbidden Paths
- Other services, contracts, shared models (READ ONLY)

### Instructions
```markdown
You are SERVICE_BUILDER_MATCHING, implementing the matching algorithm service.

## Your Mission
Build the Matching service that suggests opportunities for volunteers using a scoring algorithm.

## Service Structure
Create these files in `services/matching/`:

### 1. Service Manifest (`manifest.json`)
```json
{
  "service": "matching",
  "version": "1.0.0",
  "contracts_version": "1.0.0",
  "owns": {
    "aggregates": ["MatchSuggestion"],
    "tables": ["match_suggestions", "match_history"],
    "events_published": ["match-generated", "match-clicked"],
    "events_consumed": ["volunteer-updated", "opportunity-created"],
    "commands": ["generate-matches", "quick-match"]
  },
  "api_endpoints": [
    "POST /api/matching/quick-match",
    "POST /api/matching/generate",
    "GET /api/matching/suggestions/{volunteerId}"
  ]
}
```

### 2. Matching Algorithm (`algorithm.py`)
```python
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

@dataclass
class MatchScore:
    """Detailed scoring for a match"""
    total: float
    components: Dict[str, float]
    explanation: List[str]

class MatchingAlgorithm:
    """Core matching algorithm"""
    
    # Scoring weights
    WEIGHTS = {
        "distance": 0.3,      # 30% - Physical proximity
        "skills": 0.25,       # 25% - Skill match
        "availability": 0.2,  # 20% - Time availability
        "causes": 0.15,       # 15% - Cause alignment
        "level": 0.1          # 10% - Gamification level
    }
    
    def calculate_match_score(
        self,
        volunteer: Dict[str, Any],
        opportunity: Dict[str, Any]
    ) -> MatchScore:
        """Calculate match score between volunteer and opportunity"""
        
        components = {}
        explanations = []
        
        # Distance score (inverse of distance)
        distance_km = self._calculate_distance(
            volunteer.get("location", {}),
            opportunity.get("location", {})
        )
        
        if distance_km <= 5:
            components["distance"] = 1.0
            explanations.append("✅ Very close (< 5km)")
        elif distance_km <= 15:
            components["distance"] = 0.7
            explanations.append("👍 Nearby (< 15km)")
        elif distance_km <= 30:
            components["distance"] = 0.4
            explanations.append("🚗 Moderate distance (< 30km)")
        else:
            components["distance"] = 0.1
            explanations.append("📍 Far (> 30km)")
        
        # Skills match
        volunteer_skills = set(volunteer.get("skills", []))
        required_skills = set(opportunity.get("requiredSkills", []))
        
        if required_skills:
            skill_match = len(volunteer_skills & required_skills) / len(required_skills)
            components["skills"] = skill_match
            
            if skill_match >= 1.0:
                explanations.append("✅ All skills matched")
            elif skill_match >= 0.5:
                explanations.append(f"👍 {int(skill_match * 100)}% skills matched")
            else:
                explanations.append(f"⚠️ Only {int(skill_match * 100)}% skills matched")
        else:
            components["skills"] = 1.0  # No specific skills required
            explanations.append("✅ No specific skills required")
        
        # Availability match
        volunteer_avail = set(volunteer.get("preferences", {}).get("availability", []))
        opportunity_times = set(opportunity.get("timeSlots", []))
        
        if opportunity_times and volunteer_avail:
            avail_match = len(volunteer_avail & opportunity_times) / len(opportunity_times)
            components["availability"] = avail_match
            
            if avail_match >= 0.5:
                explanations.append("✅ Good time match")
            else:
                explanations.append("⚠️ Limited time overlap")
        else:
            components["availability"] = 0.5  # Neutral if not specified
        
        # Cause alignment
        volunteer_causes = set(volunteer.get("preferences", {}).get("causes", []))
        opportunity_cause = opportunity.get("cause")
        
        if opportunity_cause and volunteer_causes:
            if opportunity_cause in volunteer_causes:
                components["causes"] = 1.0
                explanations.append("✅ Cause alignment")
            else:
                components["causes"] = 0.3
                explanations.append("📋 Different cause area")
        else:
            components["causes"] = 0.5  # Neutral
        
        # Level appropriateness
        volunteer_level = volunteer.get("level", 1)
        min_level = opportunity.get("minimumLevel", 1)
        
        if volunteer_level >= min_level:
            components["level"] = 1.0
            if min_level > 1:
                explanations.append(f"✅ Level {volunteer_level} meets requirement")
        else:
            components["level"] = 0.0
            explanations.append(f"❌ Level {min_level} required")
        
        # Calculate weighted total
        total_score = sum(
            components.get(factor, 0) * weight
            for factor, weight in self.WEIGHTS.items()
        )
        
        return MatchScore(
            total=min(total_score * 100, 100),  # Convert to 0-100 scale
            components=components,
            explanation=explanations
        )
    
    def _calculate_distance(
        self,
        loc1: Dict[str, float],
        loc2: Dict[str, float]
    ) -> float:
        """Calculate distance between two locations in kilometers"""
        
        if not (loc1 and loc2):
            return 999  # Unknown distance
        
        lat1, lon1 = loc1.get("latitude", 0), loc1.get("longitude", 0)
        lat2, lon2 = loc2.get("latitude", 0), loc2.get("longitude", 0)
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def rank_opportunities(
        self,
        volunteer: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Tuple[Dict[str, Any], MatchScore]]:
        """Rank opportunities for a volunteer"""
        
        scored = []
        for opportunity in opportunities:
            score = self.calculate_match_score(volunteer, opportunity)
            
            # Only include if minimum threshold met
            if score.total >= 30:  # 30% minimum match
                scored.append((opportunity, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1].total, reverse=True)
        
        return scored[:limit]
```

### 3. Service Layer (`service.py`)
```python
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from services.shared.models import MatchSuggestion
from .algorithm import MatchingAlgorithm
from .repository import MatchRepository

class MatchingService:
    """Matching domain service"""
    
    def __init__(self):
        self.algorithm = MatchingAlgorithm()
        self.repository = MatchRepository()
    
    async def quick_match(
        self,
        volunteer_id: str
    ) -> List[MatchSuggestion]:
        """Generate quick match suggestions for a volunteer"""
        
        # Get volunteer profile
        # In production, this would call volunteer service
        # For MVP, using mock data
        volunteer = await self._get_volunteer(volunteer_id)
        
        # Get available opportunities
        # In production, this would call opportunity service
        opportunities = await self._get_available_opportunities()
        
        # Run matching algorithm
        matches = self.algorithm.rank_opportunities(
            volunteer,
            opportunities,
            limit=3  # Quick match returns top 3
        )
        
        # Convert to MatchSuggestion objects
        suggestions = []
        for opportunity, score in matches:
            suggestion = MatchSuggestion(
                id=str(uuid4()),
                volunteerId=volunteer_id,
                opportunityId=opportunity["id"],
                organizationId=opportunity["organizationId"],
                score=score.total,
                scoreComponents=score.components,
                explanation=score.explanation,
                generatedAt=datetime.utcnow(),
                status="pending"
            )
            
            # Save to repository
            await self.repository.save(suggestion)
            suggestions.append(suggestion)
        
        # Publish event
        await self._publish_event(
            "match.generated",
            {
                "volunteerId": volunteer_id,
                "suggestionCount": len(suggestions),
                "topScore": suggestions[0].score if suggestions else 0
            }
        )
        
        return suggestions
    
    async def generate_matches(
        self,
        volunteer_id: str,
        filters: Dict[str, Any] = None
    ) -> List[MatchSuggestion]:
        """Generate comprehensive match suggestions"""
        
        volunteer = await self._get_volunteer(volunteer_id)
        opportunities = await self._get_available_opportunities(filters)
        
        matches = self.algorithm.rank_opportunities(
            volunteer,
            opportunities,
            limit=20  # Return more for browse mode
        )
        
        suggestions = []
        for opportunity, score in matches:
            suggestion = MatchSuggestion(
                id=str(uuid4()),
                volunteerId=volunteer_id,
                opportunityId=opportunity["id"],
                organizationId=opportunity["organizationId"],
                score=score.total,
                scoreComponents=score.components,
                explanation=score.explanation,
                generatedAt=datetime.utcnow(),
                status="pending"
            )
            await self.repository.save(suggestion)
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _get_volunteer(self, volunteer_id: str) -> Dict[str, Any]:
        """Get volunteer data (mock for MVP)"""
        # In production, call volunteer service
        return {
            "id": volunteer_id,
            "level": 5,
            "skills": ["teaching", "administrative"],
            "location": {"latitude": 30.0444, "longitude": 31.2357},  # Cairo
            "preferences": {
                "availability": ["weekend-morning", "weekend-afternoon"],
                "causes": ["education", "children"],
                "maxDistance": 20
            }
        }
    
    async def _get_available_opportunities(
        self,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get available opportunities (mock for MVP)"""
        # In production, call opportunity service
        return [
            {
                "id": str(uuid4()),
                "organizationId": str(uuid4()),
                "title": "Teaching Assistant",
                "cause": "education",
                "requiredSkills": ["teaching"],
                "timeSlots": ["weekend-morning"],
                "location": {"latitude": 30.0626, "longitude": 31.2497},
                "minimumLevel": 1
            },
            {
                "id": str(uuid4()),
                "organizationId": str(uuid4()),
                "title": "Admin Support",
                "cause": "health",
                "requiredSkills": ["administrative"],
                "timeSlots": ["weekend-afternoon"],
                "location": {"latitude": 30.0500, "longitude": 31.2333},
                "minimumLevel": 3
            },
            {
                "id": str(uuid4()),
                "organizationId": str(uuid4()),
                "title": "Children's Workshop",
                "cause": "children",
                "requiredSkills": ["teaching", "creative"],
                "timeSlots": ["weekend-morning", "weekend-afternoon"],
                "location": {"latitude": 30.0450, "longitude": 31.2350},
                "minimumLevel": 5
            }
        ]
    
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish domain event"""
        # Implementation similar to applications service
        pass
```

### 4. API Layer (`api.py`)
```python
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from services.shared.models import MatchSuggestion
from .service import MatchingService

router = APIRouter(prefix="/api/matching", tags=["matching"])
service = MatchingService()

@router.post("/quick-match", response_model=List[MatchSuggestion])
async def quick_match(volunteer_id: str):
    """Generate quick match suggestions (top 3)"""
    try:
        suggestions = await service.quick_match(volunteer_id)
        if not suggestions:
            raise HTTPException(
                status_code=404,
                detail="No suitable matches found"
            )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate", response_model=List[MatchSuggestion])
async def generate_matches(
    volunteer_id: str,
    filters: Dict[str, Any] = None
):
    """Generate comprehensive match suggestions"""
    try:
        suggestions = await service.generate_matches(volunteer_id, filters)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions/{volunteer_id}", response_model=List[MatchSuggestion])
async def get_suggestions(volunteer_id: str):
    """Get existing suggestions for a volunteer"""
    # Implementation here
    pass
```

## Completion Checklist
- [ ] Service manifest created
- [ ] Matching algorithm implemented
- [ ] Service layer with quick-match
- [ ] API routes defined
- [ ] Score calculation tested
- [ ] Run: `make checkpoint`
- [ ] Create: `.agents/checkpoints/matching.done`
```

---

## AGENT 4: ORCHESTRATOR

### Role
Create the BFF (Backend-for-Frontend) layer and wire services together.

### Prerequisites
- At least 2 service checkpoints exist (applications, matching)
- Services have their API routes defined

### Allowed Paths
- `bff/**` (CREATE, READ, UPDATE)
- `infrastructure/**` (CREATE, READ, UPDATE)
- `.agents/checkpoints/orchestration.done` (CREATE only)

### Forbidden Paths
- Individual service implementations (READ ONLY)

### Instructions
```markdown
You are ORCHESTRATOR, responsible for connecting all services through the BFF layer.

## Your Mission
Create the Backend-for-Frontend that orchestrates multiple services for the UI.

## BFF Implementation

### 1. Main BFF Service (`bff/main.py`)
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import httpx
from datetime import datetime

app = FastAPI(title="Seraaj BFF", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (in production, use service discovery)
SERVICES = {
    "applications": "http://localhost:8001",
    "matching": "http://localhost:8002",
    "volunteers": "http://localhost:8003",
    "organizations": "http://localhost:8004"
}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/volunteer/quick-match")
async def volunteer_quick_match(volunteer_id: str):
    """
    Orchestrated quick-match flow:
    1. Get volunteer profile
    2. Generate matches
    3. Return enriched results
    """
    async with httpx.AsyncClient() as client:
        try:
            # Get match suggestions
            match_response = await client.post(
                f"{SERVICES['matching']}/api/matching/quick-match",
                json={"volunteer_id": volunteer_id}
            )
            matches = match_response.json()
            
            # Enrich with organization details
            # In production, would batch fetch
            for match in matches:
                # Add mock organization data
                match["organization"] = {
                    "name": "Sample Organization",
                    "verified": True,
                    "rating": 4.5
                }
            
            return {
                "volunteerId": volunteer_id,
                "matches": matches,
                "generatedAt": datetime.utcnow()
            }
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/volunteer/{volunteer_id}/dashboard")
async def volunteer_dashboard(volunteer_id: str):
    """
    Get complete volunteer dashboard data:
    - Profile
    - Active applications
    - Recent matches
    - Statistics
    """
    async with httpx.AsyncClient() as client:
        # Parallel requests to multiple services
        # In production, use asyncio.gather
        
        dashboard_data = {
            "profile": {
                "id": volunteer_id,
                "name": "John Doe",
                "level": 5,
                "totalHours": 120,
                "badges": ["rookie", "dedicated"]
            },
            "activeApplications": [],
            "recentMatches": [],
            "statistics": {
                "applicationsSubmitted": 15,
                "opportunitiesCompleted": 8,
                "averageRating": 4.7
            }
        }
        
        return dashboard_data

@app.post("/api/volunteer/apply")
async def submit_application(
    volunteer_id: str,
    opportunity_id: str,
    cover_letter: str = None
):
    """
    Submit application through orchestration:
    1. Validate volunteer
    2. Validate opportunity
    3. Submit application
    4. Update match status
    """
    async with httpx.AsyncClient() as client:
        try:
            # Submit to applications service
            response = await client.post(
                f"{SERVICES['applications']}/api/applications",
                json={
                    "volunteerId": volunteer_id,
                    "opportunityId": opportunity_id,
                    "coverLetter": cover_letter
                }
            )
            
            return response.json()
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail="Service unavailable")
```

### 2. Service Discovery (`infrastructure/discovery.py`)
```python
from typing import Dict, Optional
import consul

class ServiceDiscovery:
    """Service discovery using Consul (or similar)"""
    
    def __init__(self):
        # For MVP, use static configuration
        self.services = {
            "applications": {
                "host": "localhost",
                "port": 8001,
                "health": "/health"
            },
            "matching": {
                "host": "localhost",
                "port": 8002,
                "health": "/health"
            }
        }
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get healthy service instance URL"""
        if service_name in self.services:
            svc = self.services[service_name]
            return f"http://{svc['host']}:{svc['port']}"
        return None
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        health_status = {}
        for name, config in self.services.items():
            # Check each service health endpoint
            health_status[name] = True  # Mock for now
        return health_status
```

### 3. Event Bus Setup (`infrastructure/event_bus.py`)
```python
import asyncio
import json
from typing import Dict, Any, Callable
from datetime import datetime
import redis.asyncio as redis

class EventBus:
    """Central event bus for service communication"""
    
    def __init__(self):
        self.redis = None
        self.subscribers: Dict[str, list[Callable]] = {}
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url("redis://localhost:6379")
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish event to bus"""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        if self.redis:
            await self.redis.publish(
                f"events:{event_type}",
                json.dumps(event)
            )
    
    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        
        # Start listening
        if self.redis:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f"events:{event_type}")
            
            async def listener():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        event = json.loads(message["data"])
                        for handler in self.subscribers[event_type]:
                            await handler(event)
            
            asyncio.create_task(listener())
```

### 4. API Gateway Configuration (`infrastructure/gateway/nginx.conf`)
```nginx
upstream bff {
    server localhost:8000;
}

upstream applications {
    server localhost:8001;
}

upstream matching {
    server localhost:8002;
}

server {
    listen 80;
    server_name api.seraaj.local;
    
    # Route to BFF for frontend endpoints
    location /api/ {
        proxy_pass http://bff;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Direct service routes (for admin/debugging)
    location /services/applications/ {
        proxy_pass http://applications/;
    }
    
    location /services/matching/ {
        proxy_pass http://matching/;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy";
    }
}
```

### 5. Docker Compose (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: seraaj
      POSTGRES_USER: seraaj
      POSTGRES_PASSWORD: seraaj_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  bff:
    build: ./bff
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      REDIS_URL: redis://redis:6379
    volumes:
      - ./bff:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  
  applications:
    build: ./services/applications
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://seraaj:seraaj_dev@postgres/seraaj
      REDIS_URL: redis://redis:6379
    volumes:
      - ./services/applications:/app
    command: uvicorn api:app --host 0.0.0.0 --port 8001 --reload
  
  matching:
    build: ./services/matching
    ports:
      - "8002:8002"
    depends_on:
      - redis
    environment:
      REDIS_URL: redis://redis:6379
    volumes:
      - ./services/matching:/app
    command: uvicorn api:app --host 0.0.0.0 --port 8002 --reload

volumes:
  redis_data:
  postgres_data:
```

## Validation Requirements
1. Start services: `docker-compose up`
2. Test BFF endpoints: `curl http://localhost:8000/api/health`
3. Test orchestration: `curl -X POST http://localhost:8000/api/volunteer/quick-match?volunteer_id=123`

## Completion Checklist
- [ ] BFF service created with orchestration
- [ ] Service discovery configured
- [ ] Event bus implementation
- [ ] API Gateway configuration
- [ ] Docker Compose setup
- [ ] All endpoints responding
- [ ] Run: `make checkpoint`
- [ ] Create: `.agents/checkpoints/orchestration.done`
```

---

## AGENT 5: VALIDATOR

### Role
Validate the entire system for consistency, drift, and functionality.

### Prerequisites
- All other agent checkpoints exist
- System is running

### Allowed Paths
- `tests/**` (CREATE, READ, UPDATE)
- `tools/validators/**` (CREATE, READ, UPDATE)
- `.agents/checkpoints/validation.done` (CREATE only)

### Forbidden Paths
- Cannot modify any service code or contracts

### Instructions
```markdown
You are VALIDATOR, the final guardian of system integrity.

## Your Mission
Ensure the entire system works correctly and no drift has occurred.

## Validation Suite

### 1. Contract Compliance Test (`tests/test_contract_compliance.py`)
```python
import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

class TestContractCompliance:
    """Ensure all services comply with contracts"""
    
    def test_contracts_frozen(self):
        """Verify contracts are frozen"""
        lock_file = Path("contracts/version.lock")
        with open(lock_file) as f:
            lock = json.load(f)
        
        assert lock["frozen"] == True, "Contracts must be frozen"
        assert lock["checksum"] != "", "Checksum must be set"
    
    def test_generated_code_exists(self):
        """Verify all generated code exists"""
        required_files = [
            Path("services/shared/models.py"),
            Path("services/shared/events.py"),
            Path("services/shared/commands.py"),
            Path("frontend/src/types/entities.ts"),
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Generated file missing: {file_path}"
    
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
            if "generated" in str(py_file):
                continue
                
            content = py_file.read_text()
            for line in content.split("\n"):
                if "from services." in line:
                    if f"services.{service_name}" not in line and "services.shared" not in line:
                        violations.append(f"{py_file}: {line.strip()}")
        
        return violations
```

### 2. End-to-End Test (`tests/e2e/test_full_flow.py`)
```python
import pytest
import httpx
from uuid import uuid4

@pytest.mark.asyncio
async def test_complete_volunteer_flow():
    """Test complete volunteer journey"""
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        volunteer_id = str(uuid4())
        
        # 1. Quick match
        match_response = await client.post(
            f"/api/volunteer/quick-match",
            params={"volunteer_id": volunteer_id}
        )
        assert match_response.status_code == 200
        matches = match_response.json()["matches"]
        assert len(matches) > 0
        
        # 2. Submit application
        opportunity_id = matches[0]["opportunityId"]
        app_response = await client.post(
            "/api/volunteer/apply",
            json={
                "volunteer_id": volunteer_id,
                "opportunity_id": opportunity_id,
                "cover_letter": "Test application"
            }
        )
        assert app_response.status_code in [200, 201]
        application = app_response.json()
        
        # 3. Get dashboard
        dashboard_response = await client.get(
            f"/api/volunteer/{volunteer_id}/dashboard"
        )
        assert dashboard_response.status_code == 200
```

### 3. Drift Detection (`tools/validators/detect_drift.py`)
```python
#!/usr/bin/env python3
import json
import hashlib
from pathlib import Path
from typing import Dict, List

class DriftDetector:
    """Detect any drift from contracts"""
    
    def __init__(self):
        self.report = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [],
            "violations": [],
            "warnings": []
        }
    
    def check_contract_checksum(self):
        """Verify contracts haven't changed"""
        contracts_dir = Path("contracts/v1.0.0")
        hasher = hashlib.sha256()
        
        for file_path in sorted(contracts_dir.rglob("*")):
            if file_path.is_file():
                hasher.update(file_path.read_bytes())
        
        current_checksum = hasher.hexdigest()
        
        lock_file = Path("contracts/version.lock")
        with open(lock_file) as f:
            lock = json.load(f)
        
        expected_checksum = lock["checksum"]
        
        if current_checksum != expected_checksum:
            self.report["violations"].append(
                f"Contract checksum mismatch! Expected: {expected_checksum[:8]}..., Got: {current_checksum[:8]}..."
            )
        else:
            self.report["checks"].append("✅ Contract checksum valid")
    
    def check_event_store_integrity(self):
        """Verify event store is append-only"""
        event_file = Path("data/events.jsonl")
        if not event_file.exists():
            return
        
        events = []
        with open(event_file) as f:
            for line in f:
                events.append(json.loads(line))
        
        # Check events are in chronological order
        for i in range(1, len(events)):
            if events[i]["timestamp"] < events[i-1]["timestamp"]:
                self.report["violations"].append(
                    "Event store not in chronological order!"
                )
                return
        
        self.report["checks"].append(f"✅ Event store has {len(events)} events in order")
    
    def check_service_health(self):
        """Check all services are healthy"""
        services = [
            ("BFF", "http://localhost:8000/api/health"),
            ("Applications", "http://localhost:8001/health"),
            ("Matching", "http://localhost:8002/health"),
        ]
        
        import httpx
        for name, url in services:
            try:
                response = httpx.get(url, timeout=5)
                if response.status_code == 200:
                    self.report["checks"].append(f"✅ {name} service healthy")
                else:
                    self.report["warnings"].append(f"⚠️ {name} service unhealthy")
            except:
                self.report["warnings"].append(f"⚠️ {name} service unreachable")
    
    def generate_report(self):
        """Generate validation report"""
        self.check_contract_checksum()
        self.check_event_store_integrity()
        self.check_service_health()
        
        # Save report
        report_file = Path("tests/validation_report.json")
        with open(report_file, "w") as f:
            json.dump(self.report, f, indent=2)
        
        # Print summary
        print("=" * 50)
        print("VALIDATION REPORT")
        print("=" * 50)
        
        if self.report["violations"]:
            print("❌ VIOLATIONS FOUND:")
            for violation in self.report["violations"]:
                print(f"  - {violation}")
            return False
        
        print("✅ All checks passed!")
        for check in self.report["checks"]:
            print(f"  {check}")
        
        if self.report["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in self.report["warnings"]:
                print(f"  {warning}")
        
        return True

if __name__ == "__main__":
    detector = DriftDetector()
    success = detector.generate_report()
    
    if success:
        # Create validation checkpoint
        checkpoint = Path(".agents/checkpoints/validation.done")
        checkpoint.write_text(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "status": "passed",
            "report": "tests/validation_report.json"
        }))
    
    exit(0 if success else 1)
```

## Final Validation Checklist
- [ ] All contract compliance tests pass
- [ ] End-to-end flow works
- [ ] No service boundary violations
- [ ] Event store integrity maintained
- [ ] All services healthy
- [ ] No drift detected
- [ ] Run: `pytest tests/ -v`
- [ ] Run: `python tools/validators/detect_drift.py`
- [ ] Create: `.agents/checkpoints/validation.done`

## System Ready Criteria
The system is ready when:
1. All 5 agent checkpoints exist
2. Validation report shows no violations
3. End-to-end test passes
4. Quick-match returns results
5. Applications can be submitted
6. Events are being logged
7. No cross-service dependencies

## Handoff
Once validation passes, the system is ready for deployment!
```

---

## Summary

These 5 sub-agents work in sequence:
1. **CONTRACT_ARCHITECT** - Creates the foundation (2 hours)
2. **GENERATOR** - Generates all code (1 hour)
3. **SERVICE_BUILDERS** - Build services in parallel (3 hours)
4. **ORCHESTRATOR** - Wires everything together (2 hours)
5. **VALIDATOR** - Ensures system integrity (1 hour)

Total time with Claude Code: ~9 hours for complete MVP

Each agent:
- Has strict boundaries
- Cannot modify other agents' work
- Creates checkpoint files
- Must pass validation before handoff

This architecture ensures no drift and rapid development!