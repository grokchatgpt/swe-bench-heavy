#!/usr/bin/env python3
"""
SWE-Bench Heavy: Enhanced Statistics Tracking System
Provides comprehensive stats tracking with per-issue details and overall aggregated statistics.
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import shutil

class StatsTracker:
    """Enhanced statistics tracker for SWE-Bench Heavy."""
    
    def __init__(self):
        self.state_file = 'state.json'
        self.progress_file = 'progress.md'
        self.backup_dir = 'backup_stats'
        
    def load_state(self) -> Dict[str, Any]:
        """Load current state with error handling."""
        if not os.path.exists(self.state_file):
            return self._create_initial_state()
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                # Ensure all required fields exist
                return self._validate_state(state)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ State file corrupted, creating fresh state: {e}")
            return self._create_initial_state()
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial state structure with per-issue and overall stats."""
        return {
            "test_config": {
                "mode": "RANGE",
                "total_issues": 300,
                "dataset_file": "swe_bench_lite.jsonl",
                "start_index": 0,
                "end_index": 299
            },
            "current_state": {
                "current_issue_index": 0,
                "issues_attempted": 0,
                "issues_passed": 0,
                "issues_failed": 0,
                "issues_skipped": 0,
                "last_activity": None,
                "session_start": None,
                "total_attempts": 0,
                "unique_issues_attempted": 0,
                "avg_attempts_per_issue": 0.0,
                "session_duration_minutes": 0.0
            },
            "issue_status": {},
            "failed_issues": [],
            "skipped_issues": [],
            "completed_issues": [],
            "retry_queue": [],
            "issue_attempts": {},  # PER-ISSUE detailed stats
            "overall_stats": {},   # OVERALL aggregated stats
            "current_issue_index": 0,
            "last_updated": None
        }
    
    def _validate_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix state structure."""
        initial = self._create_initial_state()
        
        # Ensure all top-level keys exist
        for key in initial:
            if key not in state:
                state[key] = initial[key]
        
        # Ensure all current_state fields exist
        for key in initial["current_state"]:
            if key not in state["current_state"]:
                state["current_state"][key] = initial["current_state"][key]
        
        return state
    
    def start_session(self) -> None:
        """Start a new testing session."""
        state = self.load_state()
        now = datetime.now().isoformat()
        
        if state["current_state"]["session_start"] is None:
            state["current_state"]["session_start"] = now
            print(f"🚀 Session started at: {now}")
        else:
            print(f"📊 Session already active since: {state['current_state']['session_start']}")
        
        state["current_state"]["last_activity"] = now
        self.save_state(state)
    
    def record_attempt(self, issue_id: str, status: str, notes: str = "") -> None:
        """Record an attempt with both per-issue and overall stats tracking."""
        state = self.load_state()
        now = datetime.now().isoformat()
        
        # Start session if not started
        if state["current_state"]["session_start"] is None:
            state["current_state"]["session_start"] = now
        
        # Initialize issue attempts tracking if needed
        if "issue_attempts" not in state:
            state["issue_attempts"] = {}
        
        # PER-ISSUE STATS: Track detailed stats for this specific issue
        if issue_id not in state["issue_attempts"]:
            state["issue_attempts"][issue_id] = {
                "attempt_count": 0,
                "attempts": [],
                "current_status": None,
                "first_attempt": now,
                "last_attempt": now,
                "total_time_minutes": 0.0,
                "time_to_success": None,
                "first_attempt_success": False,
                "final_status": None
            }
        
        # Record this specific attempt for this issue
        attempt_data = state["issue_attempts"][issue_id]
        attempt_data["attempt_count"] += 1
        attempt_data["last_attempt"] = now
        
        # Calculate time spent on this issue
        if attempt_data["attempt_count"] > 1:
            first_time = datetime.fromisoformat(attempt_data["first_attempt"])
            current_time = datetime.fromisoformat(now)
            attempt_data["total_time_minutes"] = round((current_time - first_time).total_seconds() / 60, 1)
        
        # Track success timing for this issue
        if status == "PASS" and attempt_data["time_to_success"] is None:
            attempt_data["time_to_success"] = attempt_data["total_time_minutes"]
            if attempt_data["attempt_count"] == 1:
                attempt_data["first_attempt_success"] = True
        
        # Record the individual attempt
        attempt_record = {
            "attempt": attempt_data["attempt_count"],
            "status": status,
            "timestamp": now,
            "notes": notes
        }
        attempt_data["attempts"].append(attempt_record)
        attempt_data["current_status"] = status
        attempt_data["final_status"] = status  # Always update final status
        
        # Update legacy counters (only for first attempt of each issue)
        if attempt_data["attempt_count"] == 1:
            state["current_state"]["issues_attempted"] += 1
            state["current_state"]["unique_issues_attempted"] += 1
        
        # Remove from previous status lists
        for status_list in ["completed_issues", "failed_issues", "skipped_issues"]:
            if issue_id in state[status_list]:
                state[status_list].remove(issue_id)
        
        # Update counters and lists based on current status
        if status == "PASS":
            state["current_state"]["issues_passed"] += 1
            if issue_id not in state["completed_issues"]:
                state["completed_issues"].append(issue_id)
        elif status == "FAIL":
            state["current_state"]["issues_failed"] += 1
            if issue_id not in state["failed_issues"]:
                state["failed_issues"].append(issue_id)
        elif status == "SKIP":
            state["current_state"]["issues_skipped"] += 1
            if issue_id not in state["skipped_issues"]:
                state["skipped_issues"].append(issue_id)
        
        # Update legacy issue_status
        state["issue_status"][issue_id] = {
            "status": status,
            "timestamp": now,
            "notes": notes
        }
        
        # Update both per-issue and overall statistics
        self._update_all_stats(state)
        
        # Update session duration
        self._update_session_duration(state)
        
        # Update activity timestamp
        state["current_state"]["last_activity"] = now
        
        # Save state
        self.save_state(state)
        
        # Update progress log
        self._update_progress_log(issue_id, status, notes, state)
        
        print(f"📊 Recorded attempt #{attempt_data['attempt_count']} for {issue_id}: {status}")
        if notes:
            print(f"📝 Notes: {notes}")
    
    def _update_all_stats(self, state: Dict[str, Any]) -> None:
        """Update both per-issue attempt stats and overall aggregated stats."""
        # Update basic attempt statistics
        total_attempts = 0
        unique_issues = 0
        
        for issue_id, attempts_data in state.get("issue_attempts", {}).items():
            total_attempts += attempts_data["attempt_count"]
            unique_issues += 1
        
        state["current_state"]["total_attempts"] = total_attempts
        state["current_state"]["unique_issues_attempted"] = unique_issues
        
        if unique_issues > 0:
            state["current_state"]["avg_attempts_per_issue"] = round(total_attempts / unique_issues, 2)
        else:
            state["current_state"]["avg_attempts_per_issue"] = 0.0
        
        # OVERALL STATS: Aggregate statistics across ALL issues
        overall = {
            "total_issues_processed": unique_issues,
            "total_attempts_across_all_issues": total_attempts,
            "total_passes": len(state["completed_issues"]),
            "total_fails": len(state["failed_issues"]),
            "total_skips": len(state["skipped_issues"]),
            "overall_success_rate": 0.0,
            "avg_attempts_per_issue": state["current_state"]["avg_attempts_per_issue"],
            "first_attempt_success_count": 0,
            "first_attempt_success_rate": 0.0,
            "retry_success_count": 0,
            "retry_success_rate": 0.0,
            "max_attempts_on_single_issue": 0,
            "min_attempts_on_single_issue": float('inf'),
            "fastest_solve_minutes": None,
            "slowest_solve_minutes": None,
            "avg_time_per_successful_issue": 0.0,
            "total_time_on_successful_issues": 0.0,
            "issues_solved_first_attempt": [],
            "issues_requiring_retries": [],
            "most_difficult_issues": []  # Issues with most attempts
        }
        
        # Calculate detailed overall statistics
        first_attempt_successes = 0
        retry_successes = 0
        successful_issue_times = []
        attempt_counts = []
        
        for issue_id, attempts_data in state.get("issue_attempts", {}).items():
            attempt_count = attempts_data["attempt_count"]
            attempt_counts.append(attempt_count)
            
            # Track max/min attempts
            overall["max_attempts_on_single_issue"] = max(overall["max_attempts_on_single_issue"], attempt_count)
            if overall["min_attempts_on_single_issue"] == float('inf'):
                overall["min_attempts_on_single_issue"] = attempt_count
            else:
                overall["min_attempts_on_single_issue"] = min(overall["min_attempts_on_single_issue"], attempt_count)
            
            # Track success patterns
            if attempts_data["final_status"] == "PASS":
                if attempts_data["first_attempt_success"]:
                    first_attempt_successes += 1
                    overall["issues_solved_first_attempt"].append(issue_id)
                else:
                    retry_successes += 1
                    overall["issues_requiring_retries"].append(issue_id)
                
                # Track timing for successful issues
                if attempts_data["time_to_success"] is not None:
                    time_taken = attempts_data["time_to_success"]
                    successful_issue_times.append(time_taken)
                    
                    if overall["fastest_solve_minutes"] is None or time_taken < overall["fastest_solve_minutes"]:
                        overall["fastest_solve_minutes"] = time_taken
                    if overall["slowest_solve_minutes"] is None or time_taken > overall["slowest_solve_minutes"]:
                        overall["slowest_solve_minutes"] = time_taken
        
        # Calculate rates and averages
        total_completed = overall["total_passes"]
        total_processed = overall["total_issues_processed"]
        
        if total_processed > 0:
            overall["overall_success_rate"] = round((total_completed / total_processed) * 100, 1)
            overall["first_attempt_success_rate"] = round((first_attempt_successes / total_processed) * 100, 1)
            
            if total_processed - first_attempt_successes > 0:
                overall["retry_success_rate"] = round((retry_successes / (total_processed - first_attempt_successes)) * 100, 1)
        
        overall["first_attempt_success_count"] = first_attempt_successes
        overall["retry_success_count"] = retry_successes
        
        if successful_issue_times:
            overall["avg_time_per_successful_issue"] = round(sum(successful_issue_times) / len(successful_issue_times), 1)
            overall["total_time_on_successful_issues"] = round(sum(successful_issue_times), 1)
        
        if overall["min_attempts_on_single_issue"] == float('inf'):
            overall["min_attempts_on_single_issue"] = 0
        
        # Find most difficult issues (most attempts)
        if state.get("issue_attempts"):
            sorted_by_attempts = sorted(
                state["issue_attempts"].items(),
                key=lambda x: x[1]["attempt_count"],
                reverse=True
            )
            overall["most_difficult_issues"] = [
                {"issue_id": issue_id, "attempts": data["attempt_count"], "status": data["final_status"]}
                for issue_id, data in sorted_by_attempts[:5]  # Top 5 most difficult
            ]
        
        state["overall_stats"] = overall
    
    def _update_session_duration(self, state: Dict[str, Any]) -> None:
        """Update session duration in minutes."""
        if state["current_state"]["session_start"]:
            start_time = datetime.fromisoformat(state["current_state"]["session_start"])
            current_time = datetime.now()
            duration = (current_time - start_time).total_seconds() / 60
            state["current_state"]["session_duration_minutes"] = round(duration, 1)
    
    def _update_progress_log(self, issue_id: str, status: str, notes: str, state: Dict[str, Any]) -> None:
        """Update the human-readable progress log with both per-issue and overall stats."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats = state["current_state"]
        overall = state.get("overall_stats", {})
        
        # Calculate success rate
        total_unique = stats["unique_issues_attempted"]
        success_rate = (stats["issues_passed"] / total_unique * 100) if total_unique > 0 else 0
        
        # Get session info
        session_start = stats.get("session_start")
        session_duration = stats.get("session_duration_minutes", 0)
        
        session_info = ""
        if session_start:
            start_time = datetime.fromisoformat(session_start).strftime("%Y-%m-%d %H:%M:%S")
            session_info = f"- **Session Started**: {start_time}\n- **Session Duration**: {session_duration} minutes\n"
        
        # FIXED: Clear index vs count display to avoid confusion
        start_idx = state["test_config"]["start_index"]
        end_idx = state["test_config"]["end_index"]
        total_issues = state["test_config"]["total_issues"]
        
        # Create updated progress content
        progress_content = f"""# SWE-bench Heavy Progress Log

## Test Configuration
- **Mode**: {state["test_config"]["mode"]}
- **Dataset**: {state["test_config"]["dataset_file"]}
- **Issue Range**: Index {start_idx} to {end_idx} (inclusive)
- **Total Issues in Range**: {total_issues}
{session_info}- **Status**: Active Testing

## Current Statistics (Per-Issue Tracking)
- **Unique Issues Attempted**: {stats["unique_issues_attempted"]}/{state["test_config"]["total_issues"]}
- **Total Attempts**: {stats["total_attempts"]}
- **Issues Passed**: {stats["issues_passed"]}
- **Issues Failed**: {stats["issues_failed"]}
- **Issues Skipped**: {stats["issues_skipped"]}
- **Success Rate**: {success_rate:.1f}%
- **Avg Attempts per Issue**: {stats["avg_attempts_per_issue"]}

## Overall Statistics (Aggregated Across All Issues)
- **Total Issues Processed**: {overall.get("total_issues_processed", 0)}
- **Overall Success Rate**: {overall.get("overall_success_rate", 0)}%
- **First Attempt Success Rate**: {overall.get("first_attempt_success_rate", 0)}%
- **Retry Success Rate**: {overall.get("retry_success_rate", 0)}%
- **Max Attempts on Single Issue**: {overall.get("max_attempts_on_single_issue", 0)}
- **Avg Time per Successful Issue**: {overall.get("avg_time_per_successful_issue", 0)} minutes
- **Fastest Solve**: {overall.get("fastest_solve_minutes", "N/A")} minutes
- **Slowest Solve**: {overall.get("slowest_solve_minutes", "N/A")} minutes

## Recent Activity
**{timestamp}**: {issue_id} - {status}""" + (f" ({notes})" if notes else "") + f"""

## Current Issue Details
### {issue_id} - {status}
- **Timestamp**: {timestamp}
- **Status**: {status}
- **Attempt**: #{state["issue_attempts"][issue_id]["attempt_count"]}
- **Time on Issue**: {state["issue_attempts"][issue_id].get("total_time_minutes", 0)} minutes
""" + (f"- **Notes**: {notes}\n" if notes else "") + """

## Notes
- Enhanced stats tracking with per-issue and overall statistics
- Individual attempt tracking per issue implemented
- Automatic progress updates and backup system active
- Session management and timing tracking active
"""
        
        # Write updated progress
        with open(self.progress_file, 'w') as f:
            f.write(progress_content)
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state with backup."""
        # Create backup
        self.create_backup()
        
        # Update timestamp
        state["last_updated"] = datetime.now().isoformat()
        
        # Save state
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def create_backup(self) -> None:
        """Create backup of current state files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Backup state.json
        if os.path.exists(self.state_file):
            backup_state = f"{self.backup_dir}/state_{timestamp}.json"
            shutil.copy2(self.state_file, backup_state)
        
        # Backup progress.md
        if os.path.exists(self.progress_file):
            backup_progress = f"{self.backup_dir}/progress_{timestamp}.md"
            shutil.copy2(self.progress_file, backup_progress)
    
    def get_completion_status(self) -> Dict[str, Any]:
        """Get completion status for the current test run."""
        state = self.load_state()
        config = state["test_config"]
        current = state["current_state"]
        
        total_issues = config["total_issues"]
        completed = len(state["completed_issues"])
        failed = len(state["failed_issues"])
        skipped = len(state["skipped_issues"])
        
        # FIXED: Calculate remaining based on unique issues attempted, not total
        # An issue can be in multiple states (failed then passed), so we count unique issues
        unique_issues_processed = len(set(
            state["completed_issues"] + state["failed_issues"] + state["skipped_issues"]
        ))
        remaining = total_issues - unique_issues_processed
        
        return {
            "total_issues": total_issues,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "remaining": remaining,
            "unique_issues_processed": unique_issues_processed,
            "is_complete": remaining == 0,
            "success_rate": (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0,
            "session_duration": current.get("session_duration_minutes", 0)
        }
    
    def print_stats(self) -> None:
        """Print current statistics with both per-issue and overall views."""
        state = self.load_state()
        stats = state["current_state"]
        overall = state.get("overall_stats", {})
        completion = self.get_completion_status()
        
        print("\n📊 CURRENT STATISTICS")
        print("=" * 50)
        print(f"Unique Issues Attempted: {stats['unique_issues_attempted']}/{completion['total_issues']}")
        print(f"Total Attempts: {stats['total_attempts']}")
        print(f"Passed: {stats['issues_passed']}")
        print(f"Failed: {stats['issues_failed']}")
        print(f"Skipped: {stats['issues_skipped']}")
        print(f"Remaining: {completion['remaining']}")
        print(f"Success Rate: {completion['success_rate']:.1f}%")
        print(f"Avg Attempts per Issue: {stats['avg_attempts_per_issue']}")
        
        if stats.get("session_start"):
            print(f"Session Duration: {completion['session_duration']} minutes")
        
        print("\n📈 OVERALL STATISTICS")
        print("=" * 50)
        print(f"Overall Success Rate: {overall.get('overall_success_rate', 0)}%")
        print(f"First Attempt Success Rate: {overall.get('first_attempt_success_rate', 0)}%")
        print(f"Retry Success Rate: {overall.get('retry_success_rate', 0)}%")
        print(f"Max Attempts on Single Issue: {overall.get('max_attempts_on_single_issue', 0)}")
        print(f"Avg Time per Successful Issue: {overall.get('avg_time_per_successful_issue', 0)} minutes")
        
        fastest = overall.get('fastest_solve_minutes')
        slowest = overall.get('slowest_solve_minutes')
        if fastest is not None:
            print(f"Fastest Solve: {fastest} minutes")
        if slowest is not None:
            print(f"Slowest Solve: {slowest} minutes")
        
        if completion["is_complete"]:
            print("\n🎉 ALL ISSUES COMPLETED!")

def main():
    """CLI interface for stats tracker."""
    if len(sys.argv) < 2:
        print("Usage: python stats_tracker.py <command> [args]")
        print("Commands:")
        print("  start_session - Start a new testing session")
        print("  record <issue_id> <status> [notes] - Record an attempt")
        print("  stats - Show current statistics")
        print("  backup - Create backup of current state")
        sys.exit(1)
    
    tracker = StatsTracker()
    command = sys.argv[1]
    
    if command == "start_session":
        tracker.start_session()
    elif command == "record":
        if len(sys.argv) < 4:
            print("Usage: python stats_tracker.py record <issue_id> <status> [notes]")
            sys.exit(1)
        issue_id = sys.argv[2]
        status = sys.argv[3].upper()
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        tracker.record_attempt(issue_id, status, notes)
    elif command == "stats":
        tracker.print_stats()
    elif command == "backup":
        tracker.create_backup()
        print("✅ Backup created")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
