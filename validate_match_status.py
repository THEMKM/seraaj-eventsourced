#!/usr/bin/env python3
"""
Validation script for MatchSuggestion status fix.
Validates that all match suggestion data conforms to the MatchSuggestion model.
"""

import json
import sys
from pathlib import Path

# Add services path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

from services.shared.models import MatchSuggestion, MatchSuggestionStatus

def validate_match_suggestions_json():
    """Validate data/match_suggestions.json"""
    print("VALIDATING: data/match_suggestions.json...")
    
    try:
        with open('data/match_suggestions.json', 'r') as f:
            data = json.load(f)
        
        print(f"FOUND: {len(data)} match suggestions to validate")
        
        errors = []
        for i, item in enumerate(data):
            try:
                # This should not raise validation error
                match = MatchSuggestion(**item)
                
                # Verify status is valid (status should be a MatchSuggestionStatus enum)
                if not isinstance(match.status, MatchSuggestionStatus):
                    errors.append(f"Item {i}: Status is not a MatchSuggestionStatus enum: '{match.status}'")
                    
            except Exception as e:
                errors.append(f"Item {i}: Validation failed: {e}")
        
        if errors:
            print(f"ERROR: Found {len(errors)} validation errors:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
            return False
        else:
            print("SUCCESS: All MatchSuggestion validations passed!")
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to load/validate data/match_suggestions.json: {e}")
        return False

def validate_match_history_jsonl():
    """Validate data/match_history.jsonl"""
    print("\nVALIDATING: data/match_history.jsonl...")
    
    try:
        errors = []
        line_count = 0
        
        with open('data/match_history.jsonl', 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                line_count += 1
                try:
                    data = json.loads(line)
                    # This should not raise validation error
                    match = MatchSuggestion(**data)
                    
                    # Verify status is valid (status should be a MatchSuggestionStatus enum)
                    if not isinstance(match.status, MatchSuggestionStatus):
                        errors.append(f"Line {line_num}: Status is not a MatchSuggestionStatus enum: '{match.status}'")
                        
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: JSON decode error: {e}")
                except Exception as e:
                    errors.append(f"Line {line_num}: Validation failed: {e}")
        
        print(f"FOUND: {line_count} match history entries to validate")
        
        if errors:
            print(f"ERROR: Found {len(errors)} validation errors:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
            return False
        else:
            print("SUCCESS: All match history validations passed!")
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to load/validate data/match_history.jsonl: {e}")
        return False

def validate_status_values():
    """Verify all status values are valid MatchSuggestionStatus values"""
    print(f"\nVALIDATING: status values against MatchSuggestionStatus enum...")
    
    valid_statuses = [status.value for status in MatchSuggestionStatus]
    print(f"VALID STATUS VALUES: {valid_statuses}")
    
    # Check match_suggestions.json
    try:
        with open('data/match_suggestions.json', 'r') as f:
            data = json.load(f)
        
        invalid_statuses = set()
        for item in data:
            status = item.get('status')
            if status and status not in valid_statuses:
                invalid_statuses.add(status)
        
        if invalid_statuses:
            print(f"ERROR: Found invalid statuses in match_suggestions.json: {invalid_statuses}")
            return False
            
    except Exception as e:
        print(f"ERROR: checking match_suggestions.json: {e}")
        return False
    
    # Check match_history.jsonl
    try:
        invalid_statuses = set()
        with open('data/match_history.jsonl', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                status = data.get('status')
                if status and status not in valid_statuses:
                    invalid_statuses.add(status)
        
        if invalid_statuses:
            print(f"ERROR: Found invalid statuses in match_history.jsonl: {invalid_statuses}")
            return False
            
    except Exception as e:
        print(f"ERROR: checking match_history.jsonl: {e}")
        return False
    
    print("SUCCESS: All status values are valid!")
    return True

def main():
    """Main validation function"""
    print("STARTING: MatchSuggestion validation after status fix...")
    print("=" * 60)
    
    all_passed = True
    
    # Validate status values first
    all_passed &= validate_status_values()
    
    # Validate match suggestions JSON
    all_passed &= validate_match_suggestions_json()
    
    # Validate match history JSONL
    all_passed &= validate_match_history_jsonl()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: ALL VALIDATIONS PASSED! MatchSuggestion status fix is successful.")
        sys.exit(0)
    else:
        print("FAILED: VALIDATION FAILED! There are still issues with the data.")
        sys.exit(1)

if __name__ == "__main__":
    main()