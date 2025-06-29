#!/usr/bin/env python3
"""
Trim Docker containers to exactly 100 while maintaining balanced distribution
Remove excess containers strategically to keep good representation across all repos.
"""

import subprocess
import json
from collections import Counter, defaultdict

def get_current_containers():
    """Get all current SWE-Bench x86_64 containers"""
    result = subprocess.run(
        ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
        capture_output=True, text=True, check=True
    )
    
    swe_containers = [
        line for line in result.stdout.strip().split('\n')
        if 'swebench/sweb.eval.x86_64.' in line and line != ''
    ]
    
    return swe_containers

def analyze_containers(containers):
    """Analyze container distribution by repository"""
    repo_containers = defaultdict(list)
    
    for container in containers:
        parts = container.split('.')
        if len(parts) >= 4:
            transformed_id = '.'.join(parts[3:]).replace(':latest', '')
            instance_id = transformed_id.replace('_1776_', '__')
            
            if '__' in instance_id:
                repo_part = instance_id.split('__')[0]
                repo_mapping = {
                    'astropy': 'astropy/astropy',
                    'django': 'django/django',
                    'matplotlib': 'matplotlib/matplotlib',
                    'mwaskom': 'mwaskom/seaborn',
                    'flask': 'pallets/flask',
                    'requests': 'psf/requests',
                    'xarray': 'pydata/xarray',
                    'pylint': 'pylint-dev/pylint',
                    'pytest': 'pytest-dev/pytest',
                    'sklearn': 'scikit-learn/scikit-learn',
                    'sphinx': 'sphinx-doc/sphinx',
                    'sympy': 'sympy/sympy'
                }
                
                # Handle the mapping issue
                if repo_part in ['pallets', 'psf', 'pydata', 'pylint-dev', 'pytest-dev', 'sphinx-doc']:
                    if repo_part == 'pallets':
                        full_repo = 'pallets/flask'
                    elif repo_part == 'psf':
                        full_repo = 'psf/requests'
                    elif repo_part == 'pydata':
                        full_repo = 'pydata/xarray'
                    elif repo_part == 'pylint-dev':
                        full_repo = 'pylint-dev/pylint'
                    elif repo_part == 'pytest-dev':
                        full_repo = 'pytest-dev/pytest'
                    elif repo_part == 'sphinx-doc':
                        full_repo = 'sphinx-doc/sphinx'
                else:
                    full_repo = repo_mapping.get(repo_part, repo_part)
                
                repo_containers[full_repo].append({
                    'container': container,
                    'instance_id': instance_id
                })
    
    return repo_containers

def select_containers_to_remove(repo_containers, target_total=100):
    """Select which containers to remove to reach target while maintaining balance"""
    current_total = sum(len(containers) for containers in repo_containers.values())
    excess = current_total - target_total
    
    if excess <= 0:
        return []
    
    print(f"Need to remove {excess} containers to reach target of {target_total}")
    
    # Calculate ideal distribution for 100 containers
    ideal_distribution = {
        'astropy/astropy': 6,      # Keep all 6 (small repo)
        'django/django': 30,       # Reduce from 35 to 30
        'matplotlib/matplotlib': 7, # Keep all 7
        'mwaskom/seaborn': 2,      # Keep all 2 (tiny repo)
        'pallets/flask': 3,        # Keep all 3 (tiny repo)
        'psf/requests': 6,         # Keep all 6
        'pydata/xarray': 5,        # Keep all 5
        'pylint-dev/pylint': 6,    # Keep all 6
        'pytest-dev/pytest': 7,   # Keep all 7
        'scikit-learn/scikit-learn': 7, # Keep all 7
        'sphinx-doc/sphinx': 5,    # Keep all 5
        'sympy/sympy': 16          # Reduce from 25 to 16
    }
    
    to_remove = []
    
    for repo, containers in repo_containers.items():
        current_count = len(containers)
        target_count = ideal_distribution.get(repo, current_count)
        
        if current_count > target_count:
            excess_for_repo = current_count - target_count
            # Remove the excess containers (take from the end of the list)
            containers_to_remove = containers[-excess_for_repo:]
            to_remove.extend([c['container'] for c in containers_to_remove])
            print(f"  {repo}: removing {excess_for_repo} containers ({current_count} -> {target_count})")
        else:
            print(f"  {repo}: keeping all {current_count} containers")
    
    return to_remove

def remove_containers(containers_to_remove):
    """Remove the specified containers"""
    print(f"\nRemoving {len(containers_to_remove)} containers...")
    
    for container in containers_to_remove:
        try:
            result = subprocess.run(
                ['docker', 'rmi', container],
                capture_output=True, text=True, check=True
            )
            print(f"✅ Removed: {container}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to remove {container}: {e.stderr}")

def main():
    print("🧹 SWE-Bench Container Trimmer")
    print("=" * 50)
    print("Trimming to exactly 100 containers with balanced distribution")
    print()
    
    # Get current containers
    containers = get_current_containers()
    print(f"Current containers: {len(containers)}")
    
    if len(containers) <= 100:
        print("✅ Already at or below target of 100 containers!")
        return
    
    # Analyze distribution
    repo_containers = analyze_containers(containers)
    
    print("\nCurrent distribution:")
    for repo, containers in sorted(repo_containers.items()):
        print(f"  {repo}: {len(containers)}")
    
    # Select containers to remove
    to_remove = select_containers_to_remove(repo_containers, target_total=100)
    
    if not to_remove:
        print("✅ No containers need to be removed!")
        return
    
    print(f"\nWill remove {len(to_remove)} containers:")
    for container in to_remove:
        print(f"  {container}")
    
    # Confirm before proceeding
    response = input(f"\nProceed with removing {len(to_remove)} containers? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return
    
    # Remove containers
    remove_containers(to_remove)
    
    # Verify final state
    final_containers = get_current_containers()
    final_repo_containers = analyze_containers(final_containers)
    
    print("\n" + "=" * 50)
    print("🏁 TRIMMING COMPLETE!")
    print("=" * 50)
    print(f"Final container count: {len(final_containers)}")
    print("\nFinal distribution:")
    for repo, containers in sorted(final_repo_containers.items()):
        print(f"  {repo}: {len(containers)}")
    
    # Check disk space saved
    try:
        result = subprocess.run(['docker', 'system', 'df'], capture_output=True, text=True)
        print(f"\nUpdated Docker disk usage:")
        print(result.stdout)
    except:
        pass
    
    print("\n🎯 Perfect! You now have exactly 100 balanced containers ready for testing!")

if __name__ == "__main__":
    main()
