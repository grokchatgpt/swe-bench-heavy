#!/usr/bin/env python3
"""
Pull Balanced Sample of SWE-Bench Containers
Select remaining containers to ensure good representation across all 12 repositories.
Target: 100 total containers with balanced distribution.
"""

import json
import logging
import subprocess
import sys
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict
from datetime import datetime

# Terminal-friendly logging setup
class TerminalFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET if color else ''
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"{color}[{timestamp}] {record.getMessage()}{reset}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(TerminalFormatter())
logger.addHandler(handler)
logger.propagate = False

def load_swe_bench_lite():
    """Load all SWE-Bench Lite instances"""
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            instances = []
            for line in f:
                data = json.loads(line.strip())
                instances.append(data)
            return instances
    except Exception as e:
        logger.error(f"Failed to load SWE-Bench Lite dataset: {e}")
        return []

def get_existing_containers():
    """Get existing x86_64 containers and extract instance IDs"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
            capture_output=True, text=True, check=True
        )
        
        existing_containers = [
            line for line in result.stdout.strip().split('\n')
            if 'swebench/sweb.eval.x86_64.' in line and line != ''
        ]
        
        existing_ids = set()
        for container in existing_containers:
            parts = container.split('.')
            if len(parts) >= 4:
                transformed_id = '.'.join(parts[3:]).replace(':latest', '')
                instance_id = transformed_id.replace('_1776_', '__')
                existing_ids.add(instance_id)
        
        return existing_ids
    except Exception as e:
        logger.error(f"Failed to get existing containers: {e}")
        return set()

def calculate_target_distribution(total_target=100):
    """Calculate target number of containers per repository"""
    # Repository sizes in SWE-Bench Lite
    repo_sizes = {
        'astropy/astropy': 6,
        'django/django': 114,
        'matplotlib/matplotlib': 23,
        'mwaskom/seaborn': 4,
        'pallets/flask': 3,
        'psf/requests': 6,
        'pydata/xarray': 5,
        'pylint-dev/pylint': 6,
        'pytest-dev/pytest': 17,
        'scikit-learn/scikit-learn': 23,
        'sphinx-doc/sphinx': 16,
        'sympy/sympy': 77
    }
    
    # Calculate proportional distribution but ensure minimum representation
    total_issues = sum(repo_sizes.values())
    targets = {}
    
    for repo, size in repo_sizes.items():
        # Proportional allocation
        proportional = int((size / total_issues) * total_target)
        # Ensure minimum of 2 containers per repo (except tiny ones)
        if size >= 5:
            targets[repo] = max(proportional, 3)
        elif size >= 3:
            targets[repo] = max(proportional, 2)
        else:
            targets[repo] = min(proportional, size)  # Don't exceed available
    
    # Adjust if we're over target
    current_total = sum(targets.values())
    if current_total > total_target:
        # Reduce from largest repos first
        sorted_repos = sorted(targets.items(), key=lambda x: x[1], reverse=True)
        excess = current_total - total_target
        for repo, count in sorted_repos:
            if excess <= 0:
                break
            reduction = min(excess, max(0, count - 2))  # Don't go below 2
            targets[repo] -= reduction
            excess -= reduction
    
    return targets

def select_balanced_containers(instances, existing_ids, target_total=100):
    """Select containers to achieve balanced distribution"""
    # Group instances by repository
    repo_instances = defaultdict(list)
    for instance in instances:
        repo_instances[instance['repo']].append(instance)
    
    # Count existing containers by repo
    existing_by_repo = Counter()
    for instance_id in existing_ids:
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
            full_repo = repo_mapping.get(repo_part, repo_part)
            existing_by_repo[full_repo] += 1
    
    # Calculate targets
    targets = calculate_target_distribution(target_total)
    
    # Select additional containers needed
    selected = []
    selection_summary = {}
    
    for repo, target_count in targets.items():
        current_count = existing_by_repo.get(repo, 0)
        needed = max(0, target_count - current_count)
        
        if needed > 0 and repo in repo_instances:
            # Get available instances (not already downloaded)
            available = [
                inst for inst in repo_instances[repo]
                if inst['instance_id'] not in existing_ids
            ]
            
            # Select up to 'needed' instances
            selected_from_repo = available[:needed]
            selected.extend(selected_from_repo)
            
            selection_summary[repo] = {
                'existing': current_count,
                'target': target_count,
                'needed': needed,
                'available': len(available),
                'selected': len(selected_from_repo)
            }
        else:
            selection_summary[repo] = {
                'existing': current_count,
                'target': target_count,
                'needed': 0,
                'available': len(repo_instances.get(repo, [])),
                'selected': 0
            }
    
    return selected, selection_summary

def get_official_image_name(instance_id):
    """Get the official container name"""
    transformed_id = instance_id.replace('__', '_1776_')
    return f"swebench/sweb.eval.x86_64.{transformed_id}:latest"

def pull_container(instance, max_retries=3):
    """Pull a single container with retry logic"""
    instance_id = instance['instance_id']
    image_name = get_official_image_name(instance_id)
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            result = subprocess.run(
                ['docker', 'pull', '--quiet', image_name],
                capture_output=True, text=True, timeout=600
            )
            
            if result.returncode == 0:
                duration = time.time() - start_time
                size_mb = get_image_size(image_name)
                return {
                    'status': 'success',
                    'image': image_name,
                    'duration': duration,
                    'size_mb': size_mb,
                    'instance_id': instance_id,
                    'repo': instance['repo']
                }
            else:
                if "not found" in result.stderr.lower():
                    return {'status': 'not_found', 'image': image_name, 'instance_id': instance_id, 'repo': instance['repo']}
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Pull failed for {instance_id} (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2 ** attempt)
                    
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                logger.warning(f"⏰ Timeout pulling {instance_id} (attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Error pulling {instance_id} (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)
    
    return {'status': 'failed', 'image': image_name, 'instance_id': instance_id, 'repo': instance['repo']}

def get_image_size(image_name):
    """Get image size in MB"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', '{{.Size}}', image_name],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            size_str = result.stdout.strip()
            if 'GB' in size_str:
                return float(size_str.replace('GB', '')) * 1024
            elif 'MB' in size_str:
                return float(size_str.replace('MB', ''))
        return 0
    except:
        return 0

def main():
    print("🎯 SWE-Bench Balanced Container Sampler")
    print("=" * 60)
    print("Selecting containers for balanced representation across all 12 repositories")
    print()
    
    # Load data
    logger.info("📋 Loading SWE-Bench Lite dataset...")
    instances = load_swe_bench_lite()
    if not instances:
        logger.error("❌ No instances loaded. Exiting.")
        return
    
    logger.info("🔍 Checking existing containers...")
    existing_ids = get_existing_containers()
    logger.info(f"✅ Found {len(existing_ids)} existing containers")
    
    # Select balanced sample
    logger.info("🎯 Calculating balanced selection...")
    selected_instances, summary = select_balanced_containers(instances, existing_ids, target_total=100)
    
    # Show selection summary
    print("\n📊 SELECTION SUMMARY:")
    print("-" * 60)
    total_existing = sum(s['existing'] for s in summary.values())
    total_selected = len(selected_instances)
    
    for repo, stats in sorted(summary.items()):
        print(f"{repo}:")
        print(f"  Current: {stats['existing']} | Target: {stats['target']} | Selecting: {stats['selected']}")
    
    print(f"\n🎯 TOTALS:")
    print(f"  Current containers: {total_existing}")
    print(f"  Will download: {total_selected}")
    print(f"  Final total: {total_existing + total_selected}")
    
    if not selected_instances:
        logger.info("🎉 Already have balanced distribution!")
        return
    
    # Confirm before proceeding
    print(f"\n🚀 Ready to download {total_selected} containers for balanced sampling")
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return
    
    # Download selected containers
    print("\n🚀 Starting balanced downloads...")
    print("-" * 60)
    
    start_time = datetime.now()
    results = {'success': 0, 'failed': 0, 'not_found': 0}
    completed = 0
    total_size_mb = 0
    repo_progress = Counter()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_instance = {executor.submit(pull_container, instance): instance 
                            for instance in selected_instances}
        
        for future in as_completed(future_to_instance):
            result = future.result()
            completed += 1
            results[result['status']] += 1
            repo_progress[result['repo']] += 1
            
            if result['status'] == 'success' and 'size_mb' in result:
                total_size_mb += result['size_mb']
            
            # Progress indicator
            status_icon = "✅" if result['status'] == 'success' else ("🔍" if result['status'] == 'not_found' else "❌")
            repo_short = result['repo'].split('/')[-1]
            
            if result['status'] == 'success':
                duration = result.get('duration', 0)
                size = result.get('size_mb', 0)
                logger.info(f"{status_icon} {repo_short}: {result['instance_id']} ({duration:.1f}s, {size:.0f}MB)")
            else:
                logger.info(f"{status_icon} {repo_short}: {result['instance_id']} - {result['status']}")
            
            # Progress summary every 5 containers
            if completed % 5 == 0 or completed == len(selected_instances):
                elapsed = (datetime.now() - start_time).total_seconds()
                percent = (completed / len(selected_instances)) * 100
                
                print(f"\n📊 Progress: {completed}/{len(selected_instances)} ({percent:.1f}%) | "
                      f"✅ {results['success']} | ❌ {results['failed']} | 🔍 {results['not_found']}")
                
                if total_size_mb > 0:
                    print(f"💾 Downloaded: {total_size_mb/1024:.1f}GB | "
                          f"Avg: {total_size_mb/completed:.0f}MB per container")
                
                print("📈 By repository:", dict(repo_progress.most_common()))
                print("-" * 60)
    
    # Final summary
    elapsed_total = (datetime.now() - start_time).total_seconds()
    final_total = total_existing + results['success']
    
    print("\n" + "=" * 60)
    print("🏁 BALANCED SAMPLING COMPLETE!")
    print("=" * 60)
    print(f"✅ Successfully downloaded: {results['success']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"🔍 Not found: {results['not_found']}")
    print(f"📦 Total containers now: {final_total}")
    print(f"💾 Total downloaded: {total_size_mb/1024:.1f}GB")
    print(f"⏱️ Total time: {elapsed_total/60:.1f} minutes")
    
    print(f"\n🎯 You now have a balanced sample of {final_total} containers")
    print("🔧 Ready to test with your grading system across all 12 repositories!")

if __name__ == "__main__":
    main()
