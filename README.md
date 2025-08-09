# Seraaj - Event-Sourced Volunteer Management Platform

## Overview
Seraaj is a complete volunteer management platform built with event-sourced architecture, sophisticated matching algorithms, and strict contract-first development. The system features a Next.js 14 frontend with 8-Bit Optimism design, TypeScript SDK generation, and runtime schema validation.

## Architecture Principles
1. **Contract-First**: All schemas defined before implementation with OpenAPI 3.0.3
2. **Code Generation**: TypeScript SDK auto-generated from contracts with provenance stamps
3. **Event Sourcing**: Every state change creates immutable events in JSONL logs
4. **Service Isolation**: Microservices communicate only via HTTP APIs
5. **Schema Validation**: Runtime validation ensures contract compliance
6. **Boundary Enforcement**: Pre-commit hooks prevent architectural violations

## Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.8+ with pip
- Git with hooks enabled

### Installation & Setup
```bash
# Install all dependencies
pnpm install
pip install -r bff/requirements.txt

# Validate system integrity
python tools/validators/validate.py

# Run all tests
pytest services/applications -q
pytest services/matching -q  
pytest tests/e2e -q
pnpm -w type-check && pnpm -w lint && pnpm -w build
```

### Development Servers
```bash
# Terminal 1: Applications Service
uvicorn services.applications.api:app --host 127.0.0.1 --port 8001

# Terminal 2: Matching Service  
uvicorn services.matching.api:app --host 127.0.0.1 --port 8002

# Terminal 3: BFF (Backend-for-Frontend)
uvicorn bff.main:app --host 127.0.0.1 --port 8000

# Terminal 4: Frontend (Next.js 14)
$env:NEXT_PUBLIC_BFF_URL = "http://127.0.0.1:8000/api"  # PowerShell
export NEXT_PUBLIC_BFF_URL="http://127.0.0.1:8000/api"  # Unix
pnpm dev:web
```

### URLs
- **Frontend**: http://localhost:3000 (8-Bit Optimism design system)
- **BFF API**: http://127.0.0.1:8000/api (OpenAPI docs at /docs)
- **Applications**: http://127.0.0.1:8001 (Event-sourced application management)
- **Matching**: http://127.0.0.1:8002 (ML-like scoring algorithm)

## System Architecture

### Services Overview
- **Applications Service** (Port 8001): Event-sourced application management with state machine lifecycle
- **Matching Service** (Port 8002): Sophisticated scoring algorithm with distance/skills/availability weighting
- **BFF Service** (Port 8000): Backend-for-Frontend with runtime schema validation and service orchestration
- **Frontend** (Port 3000): Next.js 14 with 8-Bit Optimism design system and strict SDK-only HTTP boundaries

### API Endpoints

#### BFF API (http://127.0.0.1:8000/api)
- `GET /health` - Service health check
- `POST /volunteer/quick-match` - Get top match suggestions for volunteer
- `POST /volunteer/apply` - Submit application to opportunity  
- `GET /volunteer/{id}/dashboard` - Get volunteer dashboard with profile, applications, and matches

#### Applications API (http://127.0.0.1:8001/api) 
- `POST /applications` - Submit new application
- `GET /applications/{id}` - Get application details
- `PATCH /applications/{id}/state` - Update application state
- `GET /applications/volunteer/{volunteerId}` - Get volunteer's applications

#### Matching API (http://127.0.0.1:8002)
- `POST /quick-match` - Generate top 3 matches for volunteer
- `POST /generate` - Generate comprehensive matches with filtering
- `GET /suggestions/{volunteer_id}` - Get existing match suggestions

### Multi-Agent Development Workflow

This project uses a 7-agent workflow with strict boundaries:

1. **CONTRACT_ARCHITECT** - OpenAPI contracts and JSON schemas
2. **GENERATOR** - TypeScript SDK generation with provenance stamps  
3. **SERVICE_BUILDER_APPLICATIONS** - Event-sourced application service
4. **SERVICE_BUILDER_MATCHING** - ML-like matching algorithm service
5. **ORCHESTRATOR** - BFF integration and service wiring
6. **FRONTEND_COMPOSER** - Next.js frontend with 8-Bit Optimism design
7. **VALIDATOR** - E2E tests, boundary enforcement, pre-commit hooks

### Directory Structure

```
seraaj-eventsourced/
├── contracts/v1.0.0/          # OpenAPI specs and JSON schemas
│   ├── api/bff.openapi.yaml   # BFF API specification  
│   ├── entities/              # Domain entity schemas
│   ├── commands/              # Command schemas
│   └── events/                # Event schemas
├── services/
│   ├── applications/          # Event-sourced application service
│   ├── matching/              # Matching algorithm service
│   └── shared/                # Shared models and utilities
├── bff/
│   ├── adapters/              # HTTP clients for services
│   └── main.py                # FastAPI BFF with schema validation
├── apps/web/                  # Next.js 14 frontend
├── packages/
│   ├── sdk-bff/               # Generated TypeScript SDK
│   ├── ui/                    # 8-Bit Optimism design system
│   └── config/                # Shared configuration
├── tools/
│   ├── generators/            # Code generation scripts
│   └── validators/            # Validation and boundary enforcement
├── tests/e2e/                 # End-to-end integration tests
├── data/                      # File-based storage (JSON + JSONL)
└── .agents/                   # Agent coordination and checkpoints
```

## Key Features

### Event Sourcing
- **Immutable Event Logs**: All state changes recorded in JSONL format
- **Event Replay**: Complete system state can be reconstructed from events
- **Audit Trail**: Full traceability of all operations and state transitions
- **Time Travel**: View system state at any point in history

### Matching Algorithm  
- **Multi-factor Scoring**: Distance (40%), skills (35%), availability (25%)
- **Haversine Distance**: Accurate geographic distance calculation
- **Skills Matching**: Percentage-based matching against required skills
- **Availability Overlap**: Time slot intersection analysis with 30% minimum threshold

### Architecture Safeguards
- **SDK-Only HTTP**: ESLint rules prevent direct fetch/axios usage in frontend
- **Runtime Schema Validation**: All API responses validated against OpenAPI contracts
- **Boundary Enforcement**: Pre-commit hooks block cross-agent file modifications  
- **SDK Drift Detection**: Automatic detection when SDK diverges from contracts
- **Provenance Stamps**: Generated code includes tool versions and timestamps

## Development Commands

### Core Operations
```bash
# Validate entire system
python tools/validators/validate.py

# Generate TypeScript SDK from contracts
python tools/generators/generate.py

# Run all tests
pytest services/applications -q && pytest services/matching -q && pytest tests/e2e -q
pnpm -w type-check && pnpm -w lint && pnpm -w build

# Watch for boundary violations (development helper)
bash tools/validators/watch.sh
```

### Service Management
```bash
# Start all services (4 terminals)
uvicorn services.applications.api:app --host 127.0.0.1 --port 8001
uvicorn services.matching.api:app --host 127.0.0.1 --port 8002  
uvicorn bff.main:app --host 127.0.0.1 --port 8000
pnpm dev:web

# Check service health
curl http://127.0.0.1:8001/health  # Applications
curl http://127.0.0.1:8002/health  # Matching
curl http://127.0.0.1:8000/api/health  # BFF
```

## Critical Rules

1. **Contracts are Immutable**: OpenAPI specs define service boundaries - never modify manually
2. **Services are Islands**: Microservices communicate only via HTTP APIs, no imports
3. **Events are Append-Only**: Never delete or modify events in JSONL logs
4. **SDK-Only Frontend**: All HTTP calls must use generated `@seraaj/sdk-bff` package
5. **Schema Validation**: Runtime validation ensures responses match contracts
6. **Agent Boundaries**: Pre-commit hooks prevent unauthorized file modifications
7. **Generate Don't Write**: Always regenerate SDK when contracts change

## Recovery Procedures

### SDK Drift
```bash
# If SDK is out of sync with contracts
python tools/generators/generate.py
git add packages/sdk-bff/ && git commit -m "fix: regenerate SDK"
```

### Validation Failures  
```bash
# Check system integrity
python tools/validators/validate.py

# Reset to known good state
git checkout HEAD -- contracts/
python tools/generators/generate.py
```

### Service Issues
```bash
# Reset event store data
rm -rf data/ test_data/
# Services will recreate empty stores on startup
```

## Status

- ✅ **Complete System Operational**
- ✅ OpenAPI contracts defined with 4 BFF endpoints
- ✅ TypeScript SDK generated with provenance stamps
- ✅ Applications service with event sourcing (10 tests passing)
- ✅ Matching service with ML-like scoring (21 tests passing)  
- ✅ BFF integration with real service calls and schema validation
- ✅ Next.js 14 frontend with 8-Bit Optimism design system
- ✅ E2E tests validating complete volunteer flow (5 tests passing)
- ✅ Pre-commit hooks enforcing architectural boundaries
- ✅ 36 total tests passing across all layers

**System Ready**: Full volunteer management platform with event sourcing, sophisticated matching, and strict architectural boundaries.