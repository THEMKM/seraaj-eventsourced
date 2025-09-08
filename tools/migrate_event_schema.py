"""
Migration script to unify event store schema across files.

Applies the following transformations:
- Ensure each event has `eventId` (UUID) and `timestamp` in ISO 8601 with 'T'
- Ensure `organizationId` is present (nullable)
- Convert match_history.jsonl state snapshots into event envelopes
- Add `eventType` alias for events that only have `type`

Usage: python tools/migrate_event_schema.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4
from datetime import datetime

DATA_DIR = Path("data")


def iso(dt: str | datetime) -> str:
    if isinstance(dt, datetime):
        return dt.isoformat()
    # normalize to use 'T'
    return dt.replace(" ", "T")


def migrate_line_event(event: dict) -> dict:
    # Ensure eventId
    if 'eventId' not in event:
        if 'id' in event:
            event['eventId'] = str(event.pop('id'))
        else:
            event['eventId'] = str(uuid4())
    # Normalize timestamp
    if 'timestamp' in event:
        event['timestamp'] = iso(event['timestamp'])
    else:
        event['timestamp'] = datetime.utcnow().isoformat()
    # Add organizationId if missing
    if 'organizationId' not in event:
        # try to infer from data payload
        org = None
        data = event.get('data') or event.get('payload') or {}
        if isinstance(data, dict):
            org = data.get('organizationId')
        event['organizationId'] = org
    # Add eventType alias if only 'type' exists
    if 'eventType' not in event and 'type' in event:
        event['eventType'] = event['type']
    # Ensure data key exists
    if 'data' not in event:
        if 'payload' in event:
            event['data'] = event['payload']
        else:
            event['data'] = {}
    return event


def migrate_file_line_events(path: Path):
    if not path.exists():
        return
    backup = path.with_suffix(path.suffix + ".backup")
    shutil.copy(path, backup)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(path, 'r', encoding='utf-8') as src, open(tmp, 'w', encoding='utf-8') as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            migrated = migrate_line_event(obj)
            # Normalize nested datetime fields if present
            data = migrated.get('data')
            if isinstance(data, dict):
                for key in ('generatedAt', 'expiresAt'):
                    if isinstance(data.get(key), str) and ' ' in data[key]:
                        data[key] = data[key].replace(' ', 'T')
            dst.write(json.dumps(migrated, ensure_ascii=False) + "\n")
    tmp.replace(path)


def migrate_match_history(path: Path):
    if not path.exists():
        return
    backup = path.with_suffix(path.suffix + ".backup")
    shutil.copy(path, backup)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(path, 'r', encoding='utf-8') as src, open(tmp, 'w', encoding='utf-8') as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            # If already an event, migrate as a line event
            if 'eventId' in item or 'eventType' in item or 'type' in item:
                migrated = migrate_line_event(item)
                dst.write(json.dumps(migrated, ensure_ascii=False) + "\n")
                continue
            # Convert snapshot into event
            # Normalize inner snapshot datetime fields
            if isinstance(item.get('generatedAt'), str) and ' ' in item['generatedAt']:
                item['generatedAt'] = item['generatedAt'].replace(' ', 'T')
            if isinstance(item.get('expiresAt'), str) and ' ' in item['expiresAt']:
                item['expiresAt'] = item['expiresAt'].replace(' ', 'T')

            event = {
                'eventId': str(uuid4()),
                'eventType': 'match.suggestion_generated',
                'aggregateId': str(item.get('id')) if item.get('id') else None,
                'organizationId': item.get('organizationId'),
                'timestamp': iso(item.get('generatedAt') or datetime.utcnow().isoformat()),
                'data': item
            }
            dst.write(json.dumps(event, ensure_ascii=False) + "\n")
    tmp.replace(path)


def fix_space_separated_datetimes_in_match_suggestions(path: Path):
    """Ensure generatedAt/expiresAt use ISO 8601 with 'T' separator"""
    if not path.exists():
        return
    backup = path.with_suffix(path.suffix + ".backup")
    shutil.copy(path, backup)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    changed = False
    for item in data:
        for key in ("generatedAt", "expiresAt"):
            if isinstance(item.get(key), str) and ' ' in item[key]:
                item[key] = item[key].replace(' ', 'T')
                changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')


def main():
    migrate_file_line_events(DATA_DIR / 'auth_events.jsonl')
    migrate_file_line_events(DATA_DIR / 'auth_domain_events.jsonl')
    migrate_file_line_events(DATA_DIR / 'application_events.jsonl')
    migrate_match_history(DATA_DIR / 'match_history.jsonl')
    # In case match_history already contains events, normalize nested datetimes
    migrate_file_line_events(DATA_DIR / 'match_history.jsonl')
    fix_space_separated_datetimes_in_match_suggestions(DATA_DIR / 'match_suggestions.json')
    print("Migration complete.")


if __name__ == '__main__':
    main()
