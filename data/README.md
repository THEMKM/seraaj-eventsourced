# Test Data UUID Mappings

This document contains the UUID mappings used to migrate invalid UUID formats in the test data files to comply with RFC 4122 UUID format requirements.

## Volunteers

| Original ID | Migrated UUID |
|-------------|---------------|
| vol1 | 550e8400-e29b-41d4-a716-446655440001 |
| vol2 | 550e8400-e29b-41d4-a716-446655440002 |
| vol3 | 550e8400-e29b-41d4-a716-446655440003 |
| test-volunteer-123 | 550e8400-e29b-41d4-a716-446655440099 |
| test-volunteer-456 | 550e8400-e29b-41d4-a716-446655440100 |
| test-volunteer-hero-2025 | 550e8400-e29b-41d4-a716-446655440101 |
| test-volunteer-1 | 550e8400-e29b-41d4-a716-446655440102 |
| test-volunteer-1755072956 | 550e8400-e29b-41d4-a716-446655440103 |
| unknown_vol | 550e8400-e29b-41d4-a716-446655440104 |
| invalid-id-format | 550e8400-e29b-41d4-a716-446655440105 |
| integration-test | 550e8400-e29b-41d4-a716-446655440106 |
| validation-test-user | 550e8400-e29b-41d4-a716-446655440107 |
| vol-test | 550e8400-e29b-41d4-a716-446655440108 |
| (empty string) | 550e8400-e29b-41d4-a716-446655440200 |

## Opportunities  

| Original ID | Migrated UUID |
|-------------|---------------|
| opp1 | 660e8400-e29b-41d4-a716-446655440001 |
| opp2 | 660e8400-e29b-41d4-a716-446655440002 |
| opp3 | 660e8400-e29b-41d4-a716-446655440003 |
| opp4 | 660e8400-e29b-41d4-a716-446655440004 |
| opp5 | 660e8400-e29b-41d4-a716-446655440005 |
| opp6 | 660e8400-e29b-41d4-a716-446655440006 |
| test-opportunity-1755072963 | 660e8400-e29b-41d4-a716-446655440007 |

## Organizations

| Original ID | Migrated UUID |
|-------------|---------------|
| org1 | 770e8400-e29b-41d4-a716-446655440001 |
| org2 | 770e8400-e29b-41d4-a716-446655440002 |
| org3 | 770e8400-e29b-41d4-a716-446655440003 |
| org4 | 770e8400-e29b-41d4-a716-446655440004 |

## Migration Details

- **Migration Date**: 2025-08-29
- **Issue**: [#4] Invalid UUIDs in test data causing service startup failures
- **Files Affected**:
  - `data/match_suggestions.json`
  - `data/applications.json`  
  - `data/match_history.jsonl`

## UUID Format

All migrated UUIDs follow the RFC 4122 format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

Pattern: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`

## Migration Script

The migration was performed using `uuid_migration.py` which:

1. Identified all invalid UUID formats in the data files
2. Mapped them to consistent, valid UUIDs 
3. Replaced all occurrences while preserving data structure
4. Handled both JSON and JSONL file formats
5. Properly handled edge cases like empty strings

## Validation

After migration, all UUID fields pass Pydantic UUID validation, allowing services to start successfully without UUID parsing errors.