# SDK & BFF Analysis - Shared Layer 2

## SDK Layer (packages/sdk-bff/index.ts)
### Design Pattern
- **TypeScript SDK**: Unified client for frontend consumption  
- **Class-based APIs**: AuthApi, VolunteerApi, SystemApi
- **BFFClient**: Composite client with all APIs
- **Configuration**: Base path + token management

### Schema Inconsistencies Found

#### 1. **UserRole Enum Mismatch**
**SDK**: `volunteer`, `org_admin`, `admin` (lowercase)
**Contract**: `VOLUNTEER`, `ORG_ADMIN`, `SUPERADMIN` (uppercase)

#### 2. **VolunteerDashboardResponse Schema Deviation**
**SDK Interface**: Complex nested structure with badges, hours, etc.
**BFF Implementation**: Different structure with profile/applications/matches

#### 3. **MatchSuggestion Schema Conflict**
**SDK**: `volunteerId`, `opportunityId`, `score`, `scoreComponents`
**Contract**: `id`, `title`, `description`, `organizationName`

#### 4. **Auth Token Structure**
**SDK**: Missing `tokenType` field
**Contract**: Requires `tokenType: "Bearer"`

## BFF Layer (bff/main.py)
### Architecture
- **FastAPI**: Python REST API
- **Service Adapters**: Applications, Matching, Auth
- **Schema Validation**: Contract compliance checking
- **Graceful Degradation**: Mock fallbacks when services down

### Issues Found

#### 1. **Mock Data Generation Inconsistency**
- `generate_mock_match_suggestion()` creates different schema than contract
- Uses old format with `volunteerId`/`opportunityId` instead of contract format

#### 2. **Service Adapter Dependencies**
- BFF depends on 3 services: Applications, Matching, Auth
- Each service failure triggers different fallback behavior
- No circuit breaker pattern implemented

#### 3. **Contract Validation Logic**
- Schema validation exists but doesn't enforce failures
- Just logs errors instead of rejecting invalid responses

## Inter-Layer Communication Issues

### 1. **Frontend → SDK → BFF Chain**
- Frontend uses SDK types
- SDK types don't match BFF responses  
- BFF responses don't match contracts

### 2. **Version Drift**
- SDK appears based on older iteration
- Contract is v1.1.0 but SDK has v1.0.0-style schemas
- BFF tries to bridge but creates more inconsistency

## Critical Problems to Address
1. **Align SDK types with v1.1.0 contracts**
2. **Fix UserRole enum case sensitivity**  
3. **Standardize MatchSuggestion schema across all layers**
4. **Implement proper error handling chain**
5. **Add circuit breaker for service failures**