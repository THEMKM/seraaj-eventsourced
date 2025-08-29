# Event Sourcing Violations - QA CRITICAL ISSUES

## CRITICAL: Event Store Consistency Failures

### Violation 1: Multiple Event Storage Systems
**File Structure Analysis**:
```
data/
├── application_events.jsonl     (46 events)
├── auth_domain_events.jsonl     (3 events) 
├── auth_events.jsonl            (30 events)
└── match_history.jsonl          (474 events)
```

**QA FAILURE**: Four different event storage files with inconsistent naming conventions and purposes.

### Violation 2: Event Storage Naming Inconsistency
**Applications**: `application_events.jsonl` (snake_case)
**Auth Domain**: `auth_domain_events.jsonl` (snake_case with domain suffix)
**Auth General**: `auth_events.jsonl` (snake_case)
**Matching**: `match_history.jsonl` (NOT events, history!)

**QA VIOLATION**: Inconsistent naming patterns indicate no unified event store strategy.

## CRITICAL: Event Schema Violations

### Violation 3: Event Structure Inconsistency
**Application Events** (`application_events.jsonl:1`):
```json
{
  "eventId": "540e09d3-4ba7-46c2-b599-58db32c9c423",
  "eventType": "application.created",
  "timestamp": "2025-08-09T15:18:52.013345",
  "data": {...}
}
```

**Auth Events** (`auth_domain_events.jsonl:1`):
```json
{
  "eventType": "user.login",
  "timestamp": "2025-08-11T18:40:09.158365", 
  "data": {...}
}
```

**QA FAILURE**: Missing `eventId` field in auth events breaks event store consistency.

### Violation 4: Match History is NOT Event Sourcing
**File**: `match_history.jsonl`
**Content**: Direct state snapshots, not events
```json
{
  "id": "8790758d-...",
  "volunteerId": "vol1",
  "status": "pending"
}
```

**QA VIOLATION**: This is state storage masquerading as event sourcing. Should be events like:
- `match.suggestion.generated`
- `match.suggestion.status.changed`

## CRITICAL: Event Type Violations

### Violation 5: Event Type Definition vs Usage Mismatch
**Defined in EventTypes** (`infrastructure/event_types.py:9`):
```python
APPLICATION_CREATED = "application.created"
APPLICATION_SUBMITTED = "application.submitted"
APPLICATION_STATE_CHANGED = "application.state.changed"
```

**Actually Published** (`data/application_events.jsonl`):
```json
{"eventType": "application.created"}     # ✓ MATCHES
{"eventType": "application.submitted"}   # ✓ MATCHES
{"eventType": "points.award"}           # ✗ NOT DEFINED!
```

**QA FAILURE**: Undefined event type `points.award` being published.

### Violation 6: Event Schema Validation Missing
**EventSchemas Definition** (`infrastructure/event_types.py:96`):
```python
APPLICATION_SUBMITTED = {
    "required": ["applicationId", "volunteerId", "organizationId"]
}
```

**Actual Event Data** (`data/application_events.jsonl:2`):
```json
{
  "data": {
    "applicationId": "3104e2fb-...",
    "volunteerId": "test-volunteer-123",
    "opportunityId": "opp1",
    "submittedAt": "2025-08-09T15:18:52.009045"
  }
}
```

**QA FAILURE**: Missing required `organizationId` field in actual events.

## CRITICAL: Event Publisher Violations

### Violation 7: Dual Publishing Without Coordination
**File**: `services/applications/events.py:42`
```python
async def publish(self, event_type: str, data: Dict[str, Any]):
    # 1. File-based publishing (existing functionality)
    with open(self.event_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
    
    # 2. Redis publishing (new functionality) 
    if self.redis_bus:
        stream_id = await self.redis_bus.publish(...)
```

**QA ISSUES**:
1. No transactional consistency between file and Redis
2. No rollback mechanism if Redis fails after file succeeds
3. No deduplication across storage systems
4. Different event IDs for same logical event

### Violation 8: Event Consumer Infrastructure Missing
**Expected**: Event consumers in `infrastructure/consumers/`
**Found**: 
- `application_consumer.py` - EXISTS
- `matching_consumer.py` - EXISTS

**QA VERIFICATION NEEDED**: Need to check if consumers actually process events or are stubs.

## CRITICAL: Event Ordering Violations

### Violation 9: Timestamp Format Inconsistency in Event Store
**Application Events**: `"2025-08-09T15:18:52.013345"` (ISO 8601 with microseconds)
**Auth Events**: `"2025-08-11T18:40:09.158365"` (ISO 8601 with microseconds)
**Match Data**: `"2025-08-09 12:02:01.455603"` (Space-separated format)

**QA FAILURE**: Different timestamp formats prevent chronological event ordering across stores.

### Violation 10: Event Sequence Missing
**Current Events**: No sequence numbers or ordering guarantees
**Required**: Events need sequence IDs for proper replay and ordering

## CRITICAL: Event Store Partitioning Issues

### Violation 11: No Service Boundary Enforcement
**Current**: Each service writes to separate files
**Problem**: No way to replay events across service boundaries
**Missing**: Unified event stream with service source tracking

### Violation 12: Event Retention Policy Missing
**Files Keep Growing**: No rotation or archival strategy
- `match_history.jsonl`: 474 lines (largest)
- `application_events.jsonl`: 46 lines
- No size limits, rotation, or cleanup

## CRITICAL: Infrastructure Import Failures

### Violation 13: Optional Redis Import Pattern
**File**: `services/applications/events.py:12-17`
```python
try:
    from infrastructure.event_bus import RedisEventBus
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
```

**QA CONCERN**: This pattern suggests Redis infrastructure is not reliably available, indicating incomplete event sourcing setup.

## QA ASSESSMENT: EVENT SOURCING INTEGRITY COMPROMISED

**Status**: 🔴 CRITICAL FAILURE
**Risk Level**: HIGH - Data Consistency at Risk
**Event Store State**: FRAGMENTED AND INCONSISTENT

**Critical Issues Count**: 13 violations
**Recommended Action**: COMPLETE EVENT STORE REDESIGN REQUIRED

The event sourcing implementation violates fundamental principles:
1. **No unified event store**
2. **Inconsistent event schemas**
3. **Missing event ordering**
4. **No transactional consistency**
5. **Fragmented storage systems**