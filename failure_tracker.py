#!/usr/bin/env python3
"""
SWE-bench Heavy: Failure Tracker
Tracks failure attempts to prevent infinite loops and provide circuit breaker functionality.
"""
import json
import os
from typing import Dict, Any

FAILURE_TRACKER_FILE = 'failure_tracker.json'

def load_failure_data() -> Dict[str, Any]:
    """Load failure tracking data."""
    if not os.path.exists(FAILURE_TRACKER_FILE):
        return {}
    
    try:
        with open(FAILURE_TRACKER_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_failure_data(data: Dict[str, Any]) -> None:
    """Save failure tracking data."""
    with open(FAILURE_TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def increment_failure_count(issue_id: str) -> int:
    """Increment failure count for an issue and return current count."""
    data = load_failure_data()
    
    if issue_id not in data:
        data[issue_id] = {'attempts': 0}
    
    data[issue_id]['attempts'] += 1
    save_failure_data(data)
    
    return data[issue_id]['attempts']

def get_failure_count(issue_id: str) -> int:
    """Get current failure count for an issue."""
    data = load_failure_data()
    return data.get(issue_id, {}).get('attempts', 0)

def reset_failure_count(issue_id: str) -> None:
    """Reset failure count for an issue (on success)."""
    data = load_failure_data()
    if issue_id in data:
        data[issue_id]['attempts'] = 0
        save_failure_data(data)

def clear_all_failures() -> None:
    """Clear all failure tracking data."""
    if os.path.exists(FAILURE_TRACKER_FILE):
        os.remove(FAILURE_TRACKER_FILE)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            clear_all_failures()
            print("All failure tracking data cleared.")
        elif sys.argv[1] == "status":
            data = load_failure_data()
            if data:
                print("Current failure counts:")
                for issue_id, info in data.items():
                    print(f"  {issue_id}: {info['attempts']} attempts")
            else:
                print("No failure data tracked.")
        elif sys.argv[1] == "reset" and len(sys.argv) > 2:
            issue_id = sys.argv[2]
            old_count = get_failure_count(issue_id)
            reset_failure_count(issue_id)
            print(f"Reset failure count for {issue_id} (was {old_count} attempts, now 0)")
        else:
            issue_id = sys.argv[1]
            count = get_failure_count(issue_id)
            print(f"{issue_id}: {count} attempts")
    else:
        print("Usage: python failure_tracker.py <issue_id|clear|status|reset <issue_id>>")
