#!/usr/bin/env python3
"""
Aggressive cleanup for SWE-bench Heavy - keep ONLY production files
"""
import os
import shutil
import json

def main():
    print("AGGRESSIVE CLEANUP - Keeping only production files")
    
    # Files to KEEP (production toolchain)
    keep_files = {
        'setup.py',
        'get_next_issue.py', 
        'grading_fast.py',
        'record_progress.py',
        'cleanup.py',
        'reset_pristine.py',
        'instructions.md',
        'heavy.md', 
        'install.md',
        'README.md',
        'state.json',
        'progress.md',
        'swe_bench_lite.jsonl',
        '.gitignore',
        'aggressive_cleanup.py'  # Keep this script too
    }
    
    # Directories to KEEP
    keep_dirs = {
        'repos',
        'runs', 
        '.git',
        'swe_venv'  # Keep the virtual environment
    }
    
    # Get all files and directories
    all_items = set(os.listdir('.'))
    
    # Remove everything not in keep lists
    for item in all_items:
        if item.startswith('.') and item not in {'.gitignore', '.git'}:
            # Remove hidden files except .gitignore and .git
            if os.path.isdir(item):
                print(f"Removing hidden directory: {item}")
                shutil.rmtree(item)
            else:
                print(f"Removing hidden file: {item}")
                os.remove(item)
        elif item not in keep_files and item not in keep_dirs:
            if os.path.isdir(item):
                print(f"Removing directory: {item}")
                shutil.rmtree(item)
            else:
                print(f"Removing file: {item}")
                os.remove(item)
    
    print("\n✅ Aggressive cleanup complete!")
    print("Remaining files:")
    for item in sorted(os.listdir('.')):
        if not item.startswith('.') or item in {'.gitignore'}:
            print(f"  {item}")

if __name__ == "__main__":
    response = input("This will DELETE everything except core production files. Continue? (y/N): ")
    if response.lower() == 'y':
        main()
    else:
        print("Aborted.")
