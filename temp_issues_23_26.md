## P2 Issue #23: Event Store Transaction Consistency

**Problem:** Dual publishing to file + Redis without transaction consistency
**Location:** infrastructure/event_publisher.py line 25-30
**Fix:** Add transaction support for atomic dual publishing
**Commands:** `touch infrastructure/transaction_manager.py`

---

## P2 Issue #24: Service Port Configuration  

**Problem:** Hardcoded ports in service startup
**Location:** services/applications/api.py line 60, services/auth/api.py line 45
**Current:** `uvicorn.run(app, host="0.0.0.0", port=8001)`
**Fix:** `port=int(os.getenv("SERVICE_PORT", 8001))`
**Commands:** `rg "port=[0-9]+" services/ -n`

---

## P2 Issue #25: Event Store Partitioning Strategy

**Problem:** No service-aware event partitioning
**Location:** Event infrastructure files
**Fix:** Design partitioning strategy for cross-service event replay
**Commands:** `touch infrastructure/event_partitioner.py`

---

## P2 Issue #26: BFF Mock Data Schema Compliance

**Problem:** Mock data doesn't match real service schemas
**Location:** bff/main.py line 193-212 (mock generation)
**Current:** 70% schema mismatch with contract
**Fix:** Generate schema-compliant mock data
**Commands:** `rg "mock.*data" bff/ -A5`