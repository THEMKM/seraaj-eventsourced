# Inter-Service Communication Analysis

## Communication Patterns

### 1. **BFF → Services (HTTP)**
**Current Implementation:**
- BFF has service adapters: `ApplicationsAdapter`, `MatchingAdapter`, `AuthAdapter`
- Direct HTTP calls to hardcoded ports
- Graceful degradation with mock data on failure

**Issues Found:**
- No service discovery mechanism
- No circuit breaker pattern
- No retry logic for transient failures
- Hardcoded service URLs in adapters

### 2. **Service → Service (Event-Driven)**
**Current Implementation:**
- File-based event publishing to `.jsonl` files
- No Redis Streams integration yet
- No event consumers verified

**Issues Found:**
- Events are published but not consumed
- No cross-service event handlers
- Missing event-driven workflows

## Adapter Communication Analysis

### BFF Adapters
Found in: `bff/adapters/`

#### ApplicationsAdapter Issues
- **Endpoint Mismatch**: BFF expects `/api/applications` but Applications service might use different endpoints
- **Response Format**: Adapter expects specific JSON structure
- **Error Handling**: Different error formats between BFF and service

#### MatchingAdapter Issues
- **Critical Failure**: Service can't start due to data format issues
- **URL Mismatch**: Adapter expects endpoints that may not exist in current service
- **Schema Incompatibility**: Response models don't match expectations

#### AuthAdapter Issues  
- **Service Unavailable**: Auth service not running due to missing dependencies
- **Token Handling**: JWT format expectations may differ
- **Response Structure**: Error responses may not match BFF expectations

## Data Flow Issues

### 1. **UUID Inconsistency Cascade**
```
Frontend (SDK) → BFF → Services → Data Layer
     ↓           ↓       ↓          ↓
   UUIDs      UUIDs   UUIDs   "vol1","opp1"
```
**Problem**: Data layer has old string IDs, but entire stack expects UUIDs

### 2. **Field Naming Confusion**
```
TypeScript SDK: volunteerId (camelCase)
BFF Python: volunteer_id (snake_case) 
Services: volunteerId (camelCase in some, snake_case in others)
Contracts: volunteerId (camelCase)
```

### 3. **Status Enum Proliferation**
- Applications Service: SUBMITTED, REVIEWING, APPROVED, etc.
- BFF Contract: pending, approved, rejected, withdrawn
- Matching Data: "pending" (invalid for MatchSuggestion)
- SDK: Various status enums

## Event Sourcing Communication

### Event Publishing
**Current State:**
- Applications service publishes to `data/application_events.jsonl`
- Events include: application.created, application.submitted, points.award
- No Redis Streams or distributed event bus yet

### Event Consumption
**Missing:**
- No event consumers found
- No cross-service event handlers
- No event replay mechanisms
- No saga orchestration

## Service Discovery Issues

### Hardcoded Dependencies
```python
# BFF adapters hardcode service URLs
APPLICATIONS_SERVICE_URL = "http://localhost:8001"
MATCHING_SERVICE_URL = "http://localhost:8003"  
AUTH_SERVICE_URL = "http://localhost:8004"
```

### Health Check Chain
- BFF has `/api/health/services` endpoint
- Checks each service health independently
- No coordinated health status
- No dependency health propagation

## Communication Security

### Authentication Flow
1. **Frontend** → **BFF** (JWT Bearer token)
2. **BFF** → **Auth Service** (token validation)
3. **BFF** → **Other Services** (service-to-service auth missing)

**Security Gaps:**
- No service-to-service authentication
- No API gateway or rate limiting
- No request signing between services

## Performance Issues

### Synchronous Chains
- All BFF → Service calls are synchronous
- No parallel service calls for dashboard data
- No caching layer between BFF and services
- No timeout configuration for service calls

### Error Propagation
- Errors bubble up through entire stack
- No error transformation layers
- Inconsistent error response formats
- Limited error context preservation