# Seraaj Claude Code Sub-Agents

This directory contains 7 specialized sub-agents for building the Seraaj event-sourced volunteer management platform. Each agent has strict boundaries and specific responsibilities.

## Agent Execution Sequence

### Phase 1: Foundation (2 hours)
**1. contract-architect** - Define all contracts, schemas, and API specifications
- Creates immutable JSON schemas for entities, events, commands
- Defines OpenAPI specifications for each service
- Establishes workflow state machines
- Must complete before any other agent can run

### Phase 2: Code Generation (1 hour)
**2. generator** - Generate all code from contracts
- Creates Python Pydantic models from JSON schemas
- Generates TypeScript types for frontend
- Builds API clients from OpenAPI specs
- Creates state machine classes from workflows

### Phase 3: Service Implementation (3-4 hours parallel)
**3. service-builder-applications** - Build Applications service
- Implements application lifecycle management
- Event sourcing with state machine integration
- Repository, service, and API layers

**4. service-builder-matching** - Build Matching service
- Implements sophisticated matching algorithm
- Considers distance, skills, availability, causes
- Generates ranked opportunity suggestions

### Phase 4: System Integration (2 hours)
**5. orchestrator** - Create BFF and wire services together
- Backend-for-Frontend layer
- Service discovery and communication
- Event bus setup
- Docker configuration

### Phase 5: Frontend Development (2 hours)
**6. frontend-composer** - Create Next.js 14 frontend with 8-Bit Optimism design system
- Complete Next.js app with App Router
- 8-Bit Optimism design system (@seraaj/ui)
- Monorepo structure with pnpm workspaces
- BFF SDK integration with HTTP boundaries
- ESLint enforcement preventing direct API calls

### Phase 6: Validation (1 hour)  
**7. validator** - Validate entire system integrity
- Contract compliance verification
- Service boundary enforcement
- Event sourcing integrity
- End-to-end testing

## Usage Examples

### Invoke Specific Agent
```bash
> Use the contract-architect subagent to define all contracts
> Use the generator subagent to generate code from contracts  
> Use the service-builder-applications subagent to implement the applications service
> Use the frontend-composer subagent to create the Next.js frontend
```

### Sequential Execution
```bash
# Start with contracts
> Use the contract-architect subagent

# Then generate code
> Use the generator subagent

# Then build services (can be parallel)
> Use the service-builder-applications subagent
> Use the service-builder-matching subagent

# Then orchestrate
> Use the orchestrator subagent

# Then build frontend
> Use the frontend-composer subagent

# Finally validate
> Use the validator subagent
```

## Agent Boundaries

### contract-architect
- **Allowed**: `contracts/v1.0.0/**`
- **Forbidden**: All other paths
- **Creates**: All JSON schemas, OpenAPI specs, workflows

### generator
- **Allowed**: `tools/generators/**`, `services/shared/**`, `frontend/src/types/**`
- **Forbidden**: Contracts (read-only), service implementations
- **Creates**: Generated models, types, API clients

### service-builder-applications
- **Allowed**: `services/applications/**`
- **Forbidden**: Other services, contracts, generated code (read-only)
- **Creates**: Complete Applications service implementation

### service-builder-matching
- **Allowed**: `services/matching/**`
- **Forbidden**: Other services, contracts, generated code (read-only)
- **Creates**: Complete Matching service with algorithm

### orchestrator
- **Allowed**: `bff/**`, `infrastructure/**`, `docker-compose.yml`
- **Forbidden**: Service implementations, contracts (read-only)
- **Creates**: BFF, service discovery, event bus, Docker config

### validator
- **Allowed**: `tests/**`, `tools/validators/**`
- **Forbidden**: Cannot modify any implementation code
- **Creates**: Test suites, validation tools, system reports

## Prerequisites Chain

```
contract-architect → generator → service-builders → orchestrator → validator
     (no deps)         ↑            ↑                ↑           ↑
                   contracts.done  generation.done  services.done orchestration.done
```

## Checkpoint Files

Each agent creates a checkpoint file when complete:
- `.agents/checkpoints/contracts.done`
- `.agents/checkpoints/generation.done`
- `.agents/checkpoints/applications.done`
- `.agents/checkpoints/matching.done`
- `.agents/checkpoints/orchestration.done`
- `.agents/checkpoints/validation.done`

## Quality Gates

### After contract-architect
- [ ] All required schemas created
- [ ] Schemas validate with JSON Schema
- [ ] OpenAPI specs are valid
- [ ] Workflow definitions are complete

### After generator
- [ ] Python models generated successfully
- [ ] TypeScript types created
- [ ] API clients built
- [ ] State machines generated
- [ ] All imports work

### After service-builders
- [ ] Service APIs respond to requests
- [ ] Event sourcing is working
- [ ] State machines integrate properly
- [ ] Tests pass

### After orchestrator
- [ ] BFF orchestrates service calls
- [ ] Docker services start successfully
- [ ] Health checks pass
- [ ] Event bus is operational

### After validator
- [ ] No contract drift detected
- [ ] Service boundaries enforced
- [ ] Event store integrity verified
- [ ] End-to-end flows work

## Recovery Procedures

### If Agent Fails
1. Check prerequisite checkpoints exist
2. Verify allowed paths are accessible
3. Check for boundary violations
4. Review error messages for guidance
5. Rollback to previous checkpoint if needed

### Rollback Commands
```bash
# Rollback contracts
git checkout HEAD -- contracts/

# Rollback generated code
rm -rf services/shared/models.py services/shared/events.py
rm -rf frontend/src/types/

# Rollback specific service
git checkout HEAD -- services/applications/

# Rollback orchestration
git checkout HEAD -- bff/ infrastructure/ docker-compose.yml
```

## Validation Commands

```bash
# Check system health
make validate

# Run drift detection
python tools/validators/detect_drift.py

# Run full test suite
pytest tests/ -v

# Check service boundaries
python tools/validators/validate.py
```

## Expected Timeline

- **Total Time**: ~9 hours for complete MVP
- **Parallel Execution**: Service builders can run simultaneously
- **Critical Path**: contract-architect → generator → orchestrator → validator
- **Recovery Time**: < 30 minutes per agent rollback

## Architecture Benefits

1. **Drift-Proof**: Immutable contracts prevent LLM-induced decay
2. **Agent-Safe**: Strict boundaries prevent cascading failures  
3. **Event-Sourced**: Complete audit trail and reproducible state
4. **Contract-First**: All code generated from schemas
5. **Service-Isolated**: No cross-service dependencies
6. **Quality-Assured**: Validation gates at every step

## Success Criteria

The system is complete when:
- All 6 checkpoint files exist
- Validation passes with no violations
- Quick-match returns results
- Applications can be submitted
- Events are being logged
- Services are isolated
- Docker environment works