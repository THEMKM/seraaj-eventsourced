# Contracts Analysis - Shared Layer 1

## Contract Version Status
- **v1.1.0**: Current active version (BFF, Auth)
- **v1.0.0**: Legacy schemas (Application, MatchSuggestion, etc.)

## BFF Contract (v1.1.0)
- **Port**: 8000/api
- **Auth**: JWT Bearer tokens
- **Endpoints**: Auth proxy, Health, Volunteer operations
- **Key schemas**: User, AuthTokens, MatchSuggestion, Application

## Schema Consistency Issues Found

### 1. **MatchSuggestion Schema Mismatch**
**Contract vs Implementation**:
- Contract expects: `id` (UUID), `title`, `description`, `organizationName`, etc.
- Data has: `volunteerId`, `opportunityId`, `organizationId`, `status` 

**Status**: CRITICAL - Complete schema mismatch

### 2. **Application Status Enum Inconsistency**
**Contract**: [pending, approved, rejected, withdrawn]
**Data**: ["pending"] (invalid for MatchSuggestion status)

### 3. **UUID Format Enforcement**
**Contract**: Strict UUID format validation
**Legacy Data**: String IDs like "vol1", "opp1", "org1"

## Inter-Contract Dependencies
- BFF depends on Auth service contracts
- BFF proxies to individual service contracts
- Schema inheritance between v1.0.0 and v1.1.0

## Issues to Address
1. Migrate legacy data to UUID format
2. Align MatchSuggestion schema with contract
3. Reconcile Application status enums
4. Verify all services implement their contracts correctly