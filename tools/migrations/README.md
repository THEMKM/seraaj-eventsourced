# PostgreSQL Migration Tools

This directory contains tools for migrating from file-based storage to PostgreSQL event store.

## Quick Start

### 1. Setup PostgreSQL Database

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/seraaj"

# Or use individual components
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="seraaj"
export DB_USER="seraaj"
export DB_PASSWORD="seraaj"

# Setup database schema
python tools/migrations/setup_database.py --create-db --drop-existing
```

### 2. Import Existing Data

```bash
# Import JSONL files to PostgreSQL (dry run first)
python tools/migrations/import_jsonl_to_pg.py --dry-run

# Actual import with projection rebuilding
python tools/migrations/import_jsonl_to_pg.py --rebuild-projections

# Validate the import
python tools/migrations/import_jsonl_to_pg.py --validate-only
```

### 3. Switch Services to PostgreSQL

Services automatically detect PostgreSQL when environment variables are set:

```bash
# Start services - they will automatically use PostgreSQL
uvicorn services.applications.api:app --port 8001
uvicorn services.matching.api:app --port 8003
```

## Tools

### setup_database.py

Initialize PostgreSQL database and schema.

```bash
# Create database and schema
python tools/migrations/setup_database.py --create-db

# Drop existing tables and recreate
python tools/migrations/setup_database.py --drop-existing

# Verify schema only
python tools/migrations/setup_database.py --verify-only
```

### import_jsonl_to_pg.py

Import existing JSONL event files to PostgreSQL.

```bash
# Show what would be imported
python tools/migrations/import_jsonl_to_pg.py --dry-run

# Import and rebuild projections
python tools/migrations/import_jsonl_to_pg.py --rebuild-projections

# Validate existing import
python tools/migrations/import_jsonl_to_pg.py --validate-only
```

### replay_events.py

Rebuild projections from event store.

```bash
# Show event statistics
python tools/migrations/replay_events.py --stats-only

# Rebuild all projections
python tools/migrations/replay_events.py

# Incremental rebuild from timestamp
python tools/migrations/replay_events.py --from-timestamp "2025-08-11T10:00:00Z"

# Rebuild specific aggregate type
python tools/migrations/replay_events.py --aggregate-type Application

# Validate projections only
python tools/migrations/replay_events.py --validate-only
```

## Backend Selection

The repositories automatically detect which backend to use:

- **PostgreSQL**: When `DATABASE_URL` or `DB_HOST` environment variables are set
- **File**: Default fallback when PostgreSQL is not configured

You can also force a specific backend:

```python
# Force file backend
app_repo = ApplicationRepository(storage_backend="file")

# Force PostgreSQL backend  
app_repo = ApplicationRepository(storage_backend="postgres")
```

## Environment Variables

### Required for PostgreSQL

- `DATABASE_URL`: Full connection string (preferred)
  ```
  postgresql://user:password@host:port/database
  ```

### Alternative Configuration

- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432) 
- `DB_NAME`: Database name (default: seraaj)
- `DB_USER`: Database user (default: seraaj)
- `DB_PASSWORD`: Database password (default: seraaj)

### Optional Tuning

- `DB_POOL_SIZE`: Connection pool size (default: 10)
- `DB_POOL_OVERFLOW`: Pool overflow limit (default: 20)
- `DB_CONNECTION_TIMEOUT`: Connection timeout seconds (default: 30)
- `DB_ECHO`: Log SQL statements (default: false)

## Migration Strategy

### Zero-Downtime Migration

1. **Setup PostgreSQL** with schema
2. **Import existing data** from JSONL files
3. **Validate import** ensuring event counts match
4. **Set environment variables** to enable PostgreSQL
5. **Restart services** - they auto-detect PostgreSQL
6. **File storage becomes backup** (services ignore it when PostgreSQL is active)

### Rollback Strategy

1. **Remove/unset** `DATABASE_URL` and `DB_HOST` environment variables
2. **Restart services** - they fall back to file storage
3. **File storage continues** from where it left off

## Health Monitoring

All repositories include health check endpoints:

```python
health = await repository.health_check()
# Returns: 
# {
#   'status': 'healthy',
#   'backend': 'postgres',  # or 'file'
#   'database': {...}       # PostgreSQL health details
# }
```

## Testing

Run integration tests to verify dual backend functionality:

```bash
pytest tests/integration/test_dual_backend.py
```

Tests validate:
- File backend functionality
- PostgreSQL backend functionality  
- Backend auto-detection
- Compatibility between backends