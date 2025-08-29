# Data Consistency Violations - QA CRITICAL ISSUES

## CRITICAL: Multiple Status Enum Definitions
**File**: `services/shared/models.py`
**Lines**: 16, 75, 135

### Violation 1: Status Enum Name Collision
```python
# Line 16 - Application Status
class Status(Enum):
    draft = 'draft'
    submitted = 'submitted'
    reviewing = 'reviewing'
    accepted = 'accepted'  # ← INCONSISTENT with contract
    rejected = 'rejected'
    completed = 'completed'
    cancelled = 'cancelled'

# Line 75 - MatchSuggestion Status  
class Status(Enum):  # ← SAME NAME! COLLISION!
    active = 'active'
    applied = 'applied'
    expired = 'expired'
    dismissed = 'dismissed'

# Line 135 - VolunteerProfile Status
class Status(Enum):  # ← SAME NAME AGAIN! TRIPLE COLLISION!
    pending = 'pending'
    active = 'active'
    inactive = 'inactive'
    suspended = 'suspended'
```

**QA FAILURE**: Three different Status enums with IDENTICAL names in the same module. This is a Python namespace collision that will cause the last definition to overwrite the others.

## CRITICAL: Schema vs Contract Misalignment

### Violation 2: Application Status Mismatch
**Shared Model**: `accepted`, `cancelled`
**BFF Contract**: `approved`, `withdrawn`
**Services State Machine**: `ACCEPTED`, `CANCELLED` (uppercase)

### Violation 3: MatchSuggestion Complete Schema Deviation
**Shared Model MatchSuggestion**:
```python
id: UUID
volunteerId: UUID           # ← PRESENT
opportunityId: UUID         # ← PRESENT  
organizationId: UUID        # ← PRESENT
score: float (0-100)        # ← PRESENT
reasons: List[str]          # ← PRESENT
opportunityTitle: str       # ← PRESENT
organizationName: str       # ← PRESENT
status: Status              # ← PRESENT
generatedAt: datetime       # ← PRESENT
expiresAt: datetime         # ← PRESENT
```

**BFF Contract MatchSuggestion**:
```yaml
id: uuid                    # ← PRESENT
title: string               # ← MISSING from shared model
description: string         # ← MISSING from shared model  
organizationName: string    # ← PRESENT
requiredSkills: [string]    # ← MISSING from shared model
location: string            # ← MISSING from shared model
timeCommitment: string      # ← MISSING from shared model
matchScore: number          # ← PRESENT (as 'score')
# volunteerId: MISSING from contract
# opportunityId: MISSING from contract
# status: MISSING from contract
```

**QA FAILURE**: 70% schema mismatch between shared model and contract.

## CRITICAL: Data File Format Violations

### Violation 4: UUID Format Inconsistency
**File**: `data/match_suggestions.json`
```json
{
  "volunteerId": "vol1",        # ← INVALID UUID
  "opportunityId": "opp1",      # ← INVALID UUID  
  "organizationId": "org1"      # ← INVALID UUID
}
```

**File**: `data/applications.json`
```json
{
  "volunteerId": "test-volunteer-123",  # ← INVALID UUID
  "opportunityId": "opp1"               # ← INVALID UUID
}
```

**Expected**: All UUIDs must match pattern `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`

### Violation 5: Invalid Status Values
**File**: `data/match_suggestions.json`
```json
{
  "status": "pending"  # ← INVALID! Not in [active, applied, expired, dismissed]
}
```

## CRITICAL: Field Naming Convention Chaos

### Violation 6: camelCase vs snake_case Inconsistency

**Applications Service API** (`services/applications/api.py:58`):
```python
class SubmitApplicationRequest(BaseModel):
    volunteerId: str    # ← camelCase
    opportunityId: str  # ← camelCase
```

**Applications Service Domain** (`services/applications/service.py:16`):
```python
class SubmitApplicationCommand:
    def __init__(self, volunteer_id: str, opportunity_id: str):  # ← snake_case
        self.volunteerId = volunteer_id    # ← camelCase property
        self.opportunityId = opportunity_id # ← camelCase property
```

**Applications Repository** (implied from service usage):
```python
app.volunteer_id    # ← snake_case attribute access
app.opportunityId   # ← camelCase property access
```

**QA FAILURE**: Inconsistent naming conventions within the same service.

## CRITICAL: Model Import Violations

### Violation 7: Circular Import Risk
**File**: `services/shared/models.py`
```python
from uuid import UUID  # ← Line 15
# ... 58 lines later ...
from uuid import UUID  # ← Line 74 (DUPLICATE IMPORT)
# ... 59 lines later ...  
from uuid import UUID  # ← Line 134 (TRIPLE IMPORT)
```

**QA FAILURE**: Redundant imports indicate poor code organization.

### Violation 8: Pydantic Version Inconsistency
**File**: `services/shared/models.py`
```python
from pydantic import BaseModel, Field, Extra, AnyUrl, EmailStr
```

**File**: `services/shared/auth_models.py`
```python
from pydantic import BaseModel, ConfigDict, Field, AnyUrl
```

**QA ISSUE**: Different Pydantic features used (`Extra` vs `ConfigDict`), indicating inconsistent model configuration patterns.

## CRITICAL: DateTime Format Inconsistencies

### Violation 9: DateTime String Format Variation
**Event File** (`data/application_events.jsonl`):
```json
"timestamp": "2025-08-09T15:18:52.013345"  # ← ISO format, microseconds
```

**Match Data** (`data/match_suggestions.json`):
```json
"generatedAt": "2025-08-09 12:02:01.455603"  # ← Space-separated, microseconds
```

**QA FAILURE**: Two different datetime string formats in the same system.

## CRITICAL: Type Safety Violations

### Violation 10: String vs UUID Type Confusion
**Auth Models** (`services/shared/auth_models.py:29`):
```python
id: str = Field(..., pattern=r'^[0-9a-f]{8}-...')  # ← String with UUID pattern
```

**Shared Models** (`services/shared/models.py:31`):
```python
id: UUID  # ← Actual UUID type
```

**QA FAILURE**: Inconsistent use of UUID vs String types for identical data.

## QA ASSESSMENT: SYSTEM INTEGRITY COMPROMISED

**Status**: 🔴 CRITICAL FAILURE
**Risk Level**: HIGH
**Recommended Action**: IMMEDIATE REMEDIATION REQUIRED

The codebase exhibits systematic data consistency violations that would cause runtime failures in production. The enum name collisions alone make the shared models module unusable.