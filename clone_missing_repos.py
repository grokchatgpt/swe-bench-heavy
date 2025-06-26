#!/usr/bin/env python3
"""
Clone Missing Repositories
Recovers missing repositories by cloning them from their original sources.
Essential recovery utility for SWE-bench Heavy.
"""
import json
import os
import subprocess
import sys
import shutil
from pathlib import Path

def load_dataset():
    """Load the SWE-bench dataset to get repository information."""
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            issues = []
            for line in f:
                issues.append(json.loads(line.strip()))
        return issues
    except FileNotFoundError:
        print("❌ ERROR: swe_bench_lite.jsonl not found!")
        print("This file is required to determine which repositories to clone.")
        sys.exit(1)

def get_repo_info(issues):
    """Extract unique repository information from issues."""
    repos = {}
    for issue in issues:
        repo_path = issue['repo']
        base_commit = issue['base_commit']
        
        # Convert repo path to full GitHub URL
        if repo_path.startswith('https://'):
            # Already a full URL
            repo_url = repo_path
            if not repo_url.endswith('.git'):
                repo_url += '.git'
        else:
            # Convert path like 'django/django' to full GitHub URL
            repo_url = f"https://github.com/{repo_path}.git"
        
        # Extract repo name for directory naming
        if '/' in repo_path:
            repo_name = repo_path.replace('/', '__')
        else:
            repo_name = repo_path
        
        # Store repo info
        repos[issue['instance_id']] = {
            'url': repo_url,
            'base_commit': base_commit,
            'repo_name': repo_name,
            'repo_path': repo_path
        }
    
    return repos

def clone_repository(issue_id, repo_info, target_dir):
    """Clone a single repository to the target directory."""
    repo_url = repo_info['url']
    base_commit = repo_info['base_commit']
    
    print(f"Cloning {issue_id}: {repo_url}")
    
    # Create target directory
    issue_dir = os.path.join(target_dir, issue_id)
    repo_dir = os.path.join(issue_dir, 'repo')
    
    # Skip if already exists
    if os.path.exists(repo_dir):
        print(f"  ✅ Already exists: {issue_id}")
        return True
    
    try:
        # Create directory structure
        os.makedirs(issue_dir, exist_ok=True)
        
        # Clone repository
        result = subprocess.run([
            'git', 'clone', repo_url, repo_dir
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"  ❌ Clone failed: {result.stderr}")
            return False
        
        # Checkout specific commit
        result = subprocess.run([
            'git', 'checkout', base_commit
        ], cwd=repo_dir, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"  ⚠️  Checkout warning: {result.stderr}")
            # Don't fail here - some repos might not have the exact commit
        
        print(f"  ✅ Cloned: {issue_id}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout cloning {issue_id}")
        return False
    except Exception as e:
        print(f"  ❌ Error cloning {issue_id}: {e}")
        return False

def check_missing_repos(target_dir):
    """Check which repositories are missing."""
    if not os.path.exists(target_dir):
        print(f"Target directory {target_dir} does not exist. All repos are missing.")
        return set()
    
    existing_repos = set()
    for item in os.listdir(target_dir):
        repo_path = os.path.join(target_dir, item, 'repo')
        if os.path.exists(repo_path) and os.path.isdir(repo_path):
            existing_repos.add(item)
    
    return existing_repos

def check_working_tree_complete(repo_dir):
    """Check if working tree has essential files (simplified check)."""
    try:
        # Simple check - if we can run git status without errors, repo is functional
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=repo_dir, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except:
        return False

def is_repo_complete(repo_dir, expected_commit):
    """Check if repository is complete and at correct commit."""
    # Check if .git directory exists
    if not os.path.exists(os.path.join(repo_dir, '.git')):
        return False
    
    try:
        # Check if git can read the HEAD
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              cwd=repo_dir, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False
            
        # Check if we're at expected commit
        current_commit = result.stdout.strip()
        if not current_commit.startswith(expected_commit[:8]):
            return False
            
        # Check if working tree is complete
        if not check_working_tree_complete(repo_dir):
            return False
            
        return True
    except:
        return False

def fix_incomplete_repo(issue_id, repo_info, target_dir):
    """Fix an incomplete repository."""
    repo_dir = os.path.join(target_dir, issue_id, 'repo')
    
    print(f"  🔧 Fixing: {issue_id}")
    
    # Try git checkout first (faster for missing files)
    try:
        result = subprocess.run(['git', 'checkout', '--', '.'], 
                              cwd=repo_dir, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            # Verify it's now complete
            if is_repo_complete(repo_dir, repo_info['base_commit']):
                print(f"  ✅ Restored files: {issue_id}")
                return True
    except:
        pass
    
    # If that fails, delete and re-clone completely
    print(f"  🔄 Re-cloning: {issue_id}")
    issue_dir = os.path.join(target_dir, issue_id)
    if os.path.exists(issue_dir):
        shutil.rmtree(issue_dir)
    return clone_repository(issue_id, repo_info, target_dir)

def verify_all_repositories(target_dir, repos):
    """Verify all repositories are complete and fix any issues."""
    print("\n" + "=" * 50)
    print("VERIFYING REPOSITORY COMPLETENESS")
    print("=" * 50)
    
    all_repo_ids = list(repos.keys())
    incomplete_repos = []
    
    print(f"Checking {len(all_repo_ids)} repositories...")
    
    # Check each repository
    for i, issue_id in enumerate(sorted(all_repo_ids), 1):
        repo_dir = os.path.join(target_dir, issue_id, 'repo')
        
        if not os.path.exists(repo_dir):
            continue  # Skip missing repos (already handled in cloning phase)
            
        print(f"[{i}/{len(all_repo_ids)}] Checking {issue_id}...", end=" ")
        
        if is_repo_complete(repo_dir, repos[issue_id]['base_commit']):
            print("✅")
        else:
            print("❌")
            incomplete_repos.append(issue_id)
    
    # Fix incomplete repositories
    if incomplete_repos:
        print(f"\nFound {len(incomplete_repos)} incomplete repositories")
        print("Fixing incomplete repositories...")
        
        fixed_count = 0
        still_broken = []
        
        for i, issue_id in enumerate(incomplete_repos, 1):
            print(f"[{i}/{len(incomplete_repos)}] ", end="")
            
            if fix_incomplete_repo(issue_id, repos[issue_id], target_dir):
                fixed_count += 1
            else:
                still_broken.append(issue_id)
        
        print(f"\n✅ Fixed: {fixed_count}")
        if still_broken:
            print(f"❌ Still broken: {len(still_broken)}")
            for repo in still_broken:
                print(f"  - {repo}")
        
        return len(still_broken) == 0
    else:
        print("✅ All repositories are complete!")
        return True

def main():
    """Main recovery process."""
    print("SWE-bench Heavy: Clone Missing Repositories")
    print("=" * 50)
    
    # Determine target directory
    target_dir = 'repos'
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    
    print(f"Target directory: {target_dir}")
    
    # Load dataset
    print("Loading SWE-bench dataset...")
    issues = load_dataset()
    repos = get_repo_info(issues)
    
    print(f"Found {len(repos)} repositories in dataset")
    
    # Check existing repositories
    print("Checking existing repositories...")
    existing_repos = check_missing_repos(target_dir)
    missing_repos = set(repos.keys()) - existing_repos
    
    print(f"Found {len(existing_repos)} existing repositories")
    print(f"Missing {len(missing_repos)} repositories")
    
    success_count = 0
    failed_repos = []
    
    # Clone missing repositories if any
    if missing_repos:
        # Confirm with user
        if len(missing_repos) > 10:
            response = input(f"Clone {len(missing_repos)} missing repositories? This may take a while. (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        
        # Create target directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Clone missing repositories
        print("Cloning missing repositories...")
        
        for i, issue_id in enumerate(sorted(missing_repos), 1):
            print(f"[{i}/{len(missing_repos)}] ", end="")
            
            if clone_repository(issue_id, repos[issue_id], target_dir):
                success_count += 1
            else:
                failed_repos.append(issue_id)
        
        # Summary
        print("\n" + "=" * 50)
        print("CLONING SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully cloned: {success_count}")
        print(f"❌ Failed to clone: {len(failed_repos)}")
        print(f"📁 Total repositories in {target_dir}: {len(existing_repos) + success_count}")
        
        if failed_repos:
            print(f"\nFailed repositories:")
            for repo in failed_repos:
                print(f"  - {repo}")
            print("\nYou can retry failed repositories by running this script again.")
    else:
        print("✅ All repositories are already present!")
        # Create target directory just in case
        os.makedirs(target_dir, exist_ok=True)
    
    # Verify all repositories (both existing and newly cloned)
    all_complete = verify_all_repositories(target_dir, repos)
    
    # Final summary
    print("\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    
    final_existing = check_missing_repos(target_dir)
    print(f"📁 Total repositories: {len(final_existing)}")
    print(f"📋 Dataset repositories: {len(repos)}")
    
    if all_complete and len(final_existing) == len(repos):
        print("🎉 SUCCESS: All repositories are present and complete!")
    else:
        missing_count = len(repos) - len(final_existing)
        if missing_count > 0:
            print(f"⚠️  WARNING: {missing_count} repositories are still missing")
        if not all_complete:
            print("⚠️  WARNING: Some repositories may be incomplete")
    
    print(f"\nRepositories are available in: {target_dir}/")

if __name__ == "__main__":
    main()
