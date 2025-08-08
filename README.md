# Seraaj - Event-Sourced Volunteer Management Platform

## Overview
Seraaj is a volunteer management platform built with event-sourced architecture and strict contract-first development. The system is designed to be resilient to LLM-induced drift through immutable contracts, generated code, and append-only event logs.

## Architecture Principles
1. **Contract-First**: All schemas defined before implementation
2. **Code Generation**: Models/types generated from JSON Schema  
3. **Event Sourcing**: Every state change creates an immutable event
4. **Service Isolation**: No service can import from another
5. **Audit Everything**: Complete trace of all operations

## Quick Start

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Validate contracts (once contracts are defined)
make validate

# Generate code from contracts
make generate

# Run tests
make test

# Start development environment
docker-compose up
```

## Multi-Agent Workflow

This project uses a 5-agent workflow:

1. **CONTRACT_ARCHITECT** - Defines all contracts and schemas
2. **GENERATOR** - Sets up and runs code generation
3. **SERVICE_BUILDERS** - Implement individual services
4. **ORCHESTRATOR** - Creates BFF and wires services
5. **VALIDATOR** - Ensures system consistency

## Directory Structure

```
seraaj-eventsourced/
├── contracts/v1.0.0/          # Immutable contracts
├── services/                  # Isolated microservices
├── infrastructure/            # Event bus, gateway
├── bff/                      # Backend for Frontend
├── frontend/                 # Web application
├── tools/                    # Generation and validation
├── .agents/                  # Agent coordination
└── tests/                    # Contract and e2e tests
```

## Critical Rules

1. **Contracts are Immutable**: Once frozen, contracts cannot change
2. **Services are Islands**: No cross-service imports allowed
3. **Events are Append-Only**: Never delete or modify events
4. **Generate Don't Write**: Always generate from schemas
5. **Validate Continuously**: Run validation after changes

## Development Commands

- `make generate` - Generate code from contracts
- `make validate` - Validate contracts and boundaries  
- `make checkpoint` - Create development checkpoint
- `make freeze` - Freeze contracts at current version
- `make test` - Run all tests
- `make clean` - Clean generated files

## Recovery Procedures

If validation fails, use:
- `git checkout HEAD -- contracts/` to rollback contracts
- `make clean && make generate` to regenerate code
- `python tools/validators/validate.py` to check drift

## Status

- ✅ Project structure initialized
- ✅ Agent boundaries configured
- ✅ Generation pipeline ready
- ✅ Validation system active
- ⏳ Contracts pending (CONTRACT_ARCHITECT phase)
- ⏳ Services pending (SERVICE_BUILDERS phase)
- ⏳ Integration pending (ORCHESTRATOR phase)