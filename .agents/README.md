# Seraaj Claude Code Sub-Agents

This directory contains specialized sub-agents for building the Seraaj event-sourced volunteer management platform. Each agent has strict boundaries and specific responsibilities.

## Agent Execution Sequence

### Phase 1: Foundation Services (Complete ✅)
**1. contract-architect** - Define OpenAPI contracts and JSON schemas
**2. generator** - Generate TypeScript SDK and Python models from contracts  
**3. service-builder-applications** - Event-sourced application management service
**4. service-builder-matching** - ML-like matching algorithm service
**5. orchestrator** - BFF integration with service orchestration
**6. frontend-composer** - Next.js 14 frontend with 8-Bit Optimism design
**7. validator** - E2E tests and boundary enforcement

### Phase 2: Full MVP Services (Current)
**8. service-builder-auth** - JWT authentication service with user management
- **Scope**: `services/auth/**`
- **Deliverables**: User registration, login, JWT tokens, password hashing
- **Checkpoint**: `auth.done`

**9. service-builder-volunteers** - Volunteer profile management
- **Scope**: `services/volunteers/**`  
- **Deliverables**: Volunteer profiles, skills, availability, preferences
- **Checkpoint**: `volunteers.done`

**10. service-builder-opportunities** - Volunteer opportunity management
- **Scope**: `services/opportunities/**`
- **Deliverables**: Opportunity creation, discovery, status management
- **Checkpoint**: `opportunities.done`

**11. service-builder-organizations** - Organization profile management
- **Scope**: `services/organizations/**`
- **Deliverables**: Nonprofit/charity profiles, verification, management
- **Checkpoint**: `organizations.done`

### Phase 3: Infrastructure & Operations
**12. data-layer-migrator** - Database migration and event store upgrade
- **Scope**: `infrastructure/db/**`, `tools/migrations/**`, specific repository files
- **Deliverables**: PostgreSQL event store, projections, migration tools
- **Checkpoint**: `persistence.done`

**13. infra-eventbus** - Redis Streams event bus implementation
- **Scope**: `infrastructure/event_bus.py`, specific event publisher files
- **Deliverables**: Redis event streaming, pub/sub patterns, event aggregation
- **Checkpoint**: `eventbus.done`

**14. observability-baseline** - Structured logging and telemetry
- **Scope**: Service-specific logging files across all services
- **Deliverables**: JSON logging, OTEL instrumentation, health checks
- **Checkpoint**: `observability.done`

**15. ci-enforcer** - GitHub Actions CI/CD pipeline
- **Scope**: `.github/workflows/**`, `tools/validators/**`
- **Deliverables**: Automated testing, validation, deployment pipelines
- **Checkpoint**: `ci.done`

## Agent Boundaries

Each agent operates within strict path boundaries defined in `boundaries.json`:
- **Restrictive Patterns**: Only specific files/directories allowed per agent
- **Checkpoint Files**: Each agent creates a completion checkpoint
- **Pre-commit Validation**: Boundary violations are blocked automatically
- **Run Manifests**: Every execution logged in `.agents/runs/<AGENT>/`

## Usage Examples

```bash
# Use specific agent for targeted work
> Use the service-builder-auth subagent to implement JWT authentication

# Sequential execution for full system
> Use the contract-architect subagent  
> Use the generator subagent
> Use the service-builder-auth subagent
> Use the orchestrator subagent
> Use the validator subagent
```

## Critical Rules

1. **Boundary Enforcement**: Agents cannot modify files outside their allowed paths
2. **Sequential Dependencies**: Some agents depend on others completing first
3. **Checkpoint Validation**: Completion checkpoints must be created and validated
4. **No Contract Drift**: v1.0.0 contracts are immutable, new features go in v1.1.0+
5. **Run Manifests**: Every agent execution must create a timestamped run manifest

## Status Tracking

- ✅ **Foundation Complete**: Applications + Matching services operational
- 🔄 **MVP Expansion**: Auth, Volunteers, Opportunities, Organizations
- ⏳ **Infrastructure**: Database migration, event bus, observability
- ⏳ **Operations**: CI/CD pipeline, deployment automation