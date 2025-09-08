# Vertical Services Analysis - Individual Slices

## Applications Service (Port 8001)
### Architecture
- **API**: FastAPI with structured logging
- **Domain**: Event-sourced with state machine
- **Repository**: File-based storage with event publishing
- **State Machine**: DRAFT → SUBMITTED → REVIEWING → APPROVED/REJECTED → COMPLETED/CANCELLED

### Issues Found
#### 1. **Field Name Inconsistency**
**Service Model**: `volunteerId`, `opportunityId` (camelCase)
**BFF Contract**: Expects same field names
**But this creates confusion with Python naming conventions**

#### 2. **State Machine vs Contract Status**
**State Machine**: SUBMITTED, REVIEWING, APPROVED, REJECTED, COMPLETED, CANCELLED
**BFF Contract**: pending, approved, rejected, withdrawn
**Issue**: Mismatch between internal states and external API

#### 3. **Event Publishing Without Event Bus**
- Uses file-based event publishing to `data/application_events.jsonl`
- No Redis Streams integration yet
- Events published but no consumers verified

## Auth Service (Port 8004)
### Architecture
- **API**: FastAPI with v1.1.0 contract compliance
- **Models**: Uses shared auth models from `services.shared.auth_models`
- **JWT**: Token generation and validation
- **Role Management**: VOLUNTEER, ORG_ADMIN, SUPERADMIN

### Issues Found
#### 1. **Missing Service Startup**
- Service exists but fails to start (bcrypt, PyJWT dependencies)
- Not currently running despite BFF trying to proxy to it

#### 2. **Error Response Format**
**Auth Service**: Returns `{"error": "CODE", "message": "desc"}`
**BFF Contract**: Expects `ErrorResponse` schema
**Potential mismatch in error handling**

## Matching Service (Port 8003)
### Architecture  
- **API**: Simple FastAPI with basic endpoints
- **Algorithm**: File-based suggestions
- **Repository**: Loads from `data/match_suggestions.json`

### Critical Issues Found
#### 1. **Complete Schema Mismatch**
**Service Model**: Uses `MatchSuggestion` from shared models
**Contract Schema**: Completely different structure
**Data Format**: Old test data with invalid UUIDs

#### 2. **Service Cannot Start**
- UUID validation errors prevent startup
- Data uses "vol1", "opp1" instead of proper UUIDs
- Status enum mismatch ("pending" vs expected values)

#### 3. **Endpoint URL Mismatch**
**Service Endpoints**: `/quick-match`, `/generate`, `/suggestions/{id}`
**BFF Adapter**: Expects different endpoint structure

## Shared Models Issues
### 1. **Multiple Model Definitions**
- `services.shared.models.py` has one set of models
- `services.shared.auth_models.py` has another set
- SDK has its own TypeScript definitions
- Contracts have their own schemas

### 2. **Inconsistent Field Naming**
- Python uses snake_case: `volunteer_id`, `opportunity_id`
- JavaScript/JSON uses camelCase: `volunteerId`, `opportunityId`
- Contracts sometimes use different names entirely

## Inter-Service Dependencies
### 1. **BFF → Services Communication**
- BFF has adapters for each service
- Adapters expect services to be running
- Graceful degradation with mock data when services fail

### 2. **Service Discovery**
- Hardcoded ports: 8001, 8003, 8004
- No service registry or health checking between services
- BFF doesn't verify service availability before calling

## Architectural Drift Issues
### 1. **Contract vs Implementation Drift**
- Services were built at different times
- Contracts evolved but services didn't update
- No automated contract compliance testing

### 2. **Shared Layer Confusion**
- Multiple shared model definitions
- No single source of truth for data structures
- Version mismatches between layers