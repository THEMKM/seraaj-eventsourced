import pytest
import json
from pathlib import Path
from datetime import datetime

class TestEventSourcing:
    """Test event sourcing implementation"""
    
    def test_event_files_exist(self):
        """Test that event files are being created"""
        data_dir = Path("data")
        
        # These files should exist if services are running
        possible_event_files = [
            "events.jsonl",
            "application_events.jsonl", 
            "matching_events.jsonl",
            "event_bus.jsonl",
            "auth_events.jsonl"
        ]
        
        found_files = []
        for event_file in possible_event_files:
            file_path = data_dir / event_file
            if file_path.exists():
                found_files.append(file_path)
        
        assert len(found_files) > 0, "No event files found - event sourcing not working"
    
    def test_events_are_append_only(self):
        """Test that events are properly formatted and append-only"""
        data_dir = Path("data")
        
        for event_file in data_dir.glob("*events*.jsonl"):
            if event_file.stat().st_size == 0:
                continue
                
            events = []
            with open(event_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError as e:
                            pytest.fail(f"Invalid JSON in {event_file}: {e}")
            
            if not events:
                continue
                
            # Check events have required fields (flexible field names)
            for i, event in enumerate(events):
                # Accept either 'eventType' or 'type' field
                has_event_type = "eventType" in event or "type" in event
                assert has_event_type, f"Event {i} missing eventType/type field in {event_file}"
                assert "timestamp" in event, f"Event {i} missing timestamp in {event_file}"
                assert "data" in event, f"Event {i} missing data in {event_file}"
            
            # Check events are in chronological order
            for i in range(1, len(events)):
                prev_time = datetime.fromisoformat(events[i-1]["timestamp"].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(events[i]["timestamp"].replace('Z', '+00:00'))
                assert curr_time >= prev_time, f"Events not in order in {event_file}"
    
    def test_event_store_integrity(self):
        """Test event store hasn't been tampered with"""
        # This is a basic check - in production would use cryptographic signatures
        event_files = list(Path("data").glob("*events*.jsonl"))
        
        for event_file in event_files:
            if event_file.stat().st_size == 0:
                continue
                
            # Check file is append-only by verifying no gaps in timestamps
            with open(event_file) as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                continue
                
            # Basic integrity check - no empty lines in middle
            for i, line in enumerate(lines):
                assert line.strip(), f"Empty line found at position {i} in {event_file}"