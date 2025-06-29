#!/usr/bin/env python3
"""
SWE-Bench Heavy: Smart File Helper
Auto-creates directory structure when writing files to runs/ directory.
"""
import os
from pathlib import Path

def smart_write_file(file_path: str, content: str) -> bool:
    """
    Write file with automatic directory creation.
    
    Args:
        file_path: Path to file (e.g., "runs/issue_id/astropy/modeling/separable.py")
        content: File content to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert to Path object for easier manipulation
        path = Path(file_path)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Created: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to write {file_path}: {e}")
        return False

def smart_copy_file(source_path: str, dest_path: str) -> bool:
    """
    Copy file with automatic directory creation.
    
    Args:
        source_path: Source file path
        dest_path: Destination file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import shutil
        
        # Convert to Path objects
        source = Path(source_path)
        dest = Path(dest_path)
        
        if not source.exists():
            print(f"❌ Source file not found: {source_path}")
            return False
            
        # Create parent directories if they don't exist
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source, dest)
        
        print(f"✅ Copied: {source_path} → {dest_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to copy {source_path} to {dest_path}: {e}")
        return False

def ensure_work_directory_structure(issue_id: str, repo_structure: dict = None) -> str:
    """
    Ensure work directory has proper structure.
    
    Args:
        issue_id: Issue ID (e.g., "astropy__astropy-12907")
        repo_structure: Optional dict of directories to create
        
    Returns:
        str: Work directory path
    """
    work_dir = f"runs/{issue_id}"
    
    try:
        # Create base work directory
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        
        # Create common repository structures if specified
        if repo_structure:
            for dir_path in repo_structure.get('directories', []):
                full_path = Path(work_dir) / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                
        print(f"✅ Work directory ready: {work_dir}")
        return work_dir
        
    except Exception as e:
        print(f"❌ Failed to setup work directory: {e}")
        return work_dir

# Common repository structures for different projects
REPO_STRUCTURES = {
    'astropy': {
        'directories': [
            'astropy/modeling',
            'astropy/modeling/tests',
            'astropy/io',
            'astropy/coordinates',
            'astropy/units',
            'astropy/table',
            'astropy/time',
            'astropy/wcs'
        ]
    },
    'django': {
        'directories': [
            'django/core',
            'django/db',
            'django/forms',
            'django/http',
            'django/template',
            'django/urls',
            'django/views',
            'tests'
        ]
    },
    'matplotlib': {
        'directories': [
            'lib/matplotlib',
            'lib/matplotlib/tests',
            'lib/mpl_toolkits'
        ]
    },
    'requests': {
        'directories': [
            'requests',
            'tests'
        ]
    },
    'pytest': {
        'directories': [
            'src/_pytest',
            'testing'
        ]
    }
}

def get_repo_structure(repo_name: str) -> dict:
    """Get common directory structure for a repository."""
    # Extract repo name from full name (e.g., "astropy/astropy" -> "astropy")
    repo_key = repo_name.split('/')[-1]
    return REPO_STRUCTURES.get(repo_key, {'directories': []})

if __name__ == "__main__":
    # Test the helper
    print("🧪 Testing Smart File Helper")
    
    # Test directory creation
    test_path = "runs/test_issue/astropy/modeling/test_file.py"
    test_content = "# Test file\nprint('Hello, World!')\n"
    
    if smart_write_file(test_path, test_content):
        print("✅ Smart file writing works!")
        
        # Clean up test
        import shutil
        shutil.rmtree("runs/test_issue", ignore_errors=True)
        print("🧹 Cleaned up test files")
    else:
        print("❌ Smart file writing failed!")
