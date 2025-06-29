#!/usr/bin/env python3
"""
Pull Official SWE-Bench Containers (x86_64 for M2 compatibility)
Enhanced for terminal execution with progress tracking and resume capability.

DISCOVERY: Official SWE-Bench containers exist but only for x86_64 architecture.
ARM64 containers are extremely limited. On M2 Macs, we use Docker's x86_64 emulation.

NAMING PATTERN: swebench/sweb.eval.x86_64.{instance_id.replace('__', '_1776_')}:latest
"""

import json
import logging
import subprocess
import sys
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime, timedelta

# Terminal-friendly logging setup
class TerminalFormatter(logging.Formatter):
    """Custom formatter for clean terminal output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color based on level
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET if color else ''
        
        # Simple format for terminal
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"{color}[{timestamp}] {record.getMessage()}{reset}"

# Setup terminal-friendly logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(TerminalFormatter())
logger.addHandler(handler)
logger.propagate = False

def load_swe_bench_lite():
    """Load all SWE-Bench Lite instance IDs"""
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            instances = []
            for line in f:
                data = json.loads(line.strip())
                instances.append(data['instance_id'])
            return instances
    except Exception as e:
        logger.error(f"Failed to load SWE-Bench Lite dataset: {e}")
        return []

def check_existing_containers():
    """Check for existing SWE-Bench x86_64 containers only"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
            capture_output=True, text=True, check=True
        )
        
        # Only look for x86_64 containers, ignore ARM64 ones
        swe_containers = [
            line for line in result.stdout.strip().split('\n')
            if 'swebench/sweb.eval.x86_64.' in line and line != ''
        ]
        
        logger.info(f"Found {len(swe_containers)} existing x86_64 SWE-Bench containers")
        return swe_containers
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check existing containers: {e}")
        return []

def save_progress(completed, total, results, start_time):
    """Save progress to file for resume capability"""
    progress_data = {
        'completed': completed,
        'total': total,
        'results': results,
        'start_time': start_time.isoformat(),
        'last_update': datetime.now().isoformat()
    }
    
    with open('pull_progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)

def load_progress():
    """Load progress from file if exists"""
    try:
        with open('pull_progress.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def estimate_time_remaining(completed, total, elapsed_time):
    """Calculate ETA based on current progress"""
    if completed == 0:
        return "Unknown"
    
    avg_time_per_container = elapsed_time / completed
    remaining = total - completed
    eta_seconds = remaining * avg_time_per_container
    
    if eta_seconds < 60:
        return f"{eta_seconds:.0f}s"
    elif eta_seconds < 3600:
        return f"{eta_seconds/60:.0f}m"
    else:
        hours = eta_seconds / 3600
        return f"{hours:.1f}h"

def get_official_image_name(instance_id):
    """
    Get the official SWE-Bench container name for an instance ID.
    
    Based on the official SWE-Bench harness code:
    - Remote images use namespace 'swebench'
    - Replace '__' with '_1776_' in instance ID
    - Use x86_64 architecture
    """
    # Replace __ with _1776_ as per official harness
    transformed_id = instance_id.replace('__', '_1776_')
    return f"swebench/sweb.eval.x86_64.{transformed_id}:latest"

def pull_container(instance_id, max_retries=3):
    """Pull a single container with retry logic and better error handling"""
    # Get the official container name
    image_name = get_official_image_name(instance_id)
    
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            # Use --quiet flag to reduce output noise
            result = subprocess.run(
                ['docker', 'pull', '--quiet', image_name],
                capture_output=True, text=True, timeout=600  # 10 min timeout
            )
            
            if result.returncode == 0:
                duration = time.time() - start_time
                size_mb = get_image_size(image_name)
                return {
                    'status': 'success', 
                    'image': image_name, 
                    'duration': duration,
                    'size_mb': size_mb,
                    'instance_id': instance_id
                }
            else:
                if "not found" in result.stderr.lower() or "pull access denied" in result.stderr.lower():
                    return {'status': 'not_found', 'image': image_name, 'instance_id': instance_id}
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Pull failed for {instance_id} (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                logger.warning(f"⏰ Timeout pulling {instance_id} (attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Error pulling {instance_id} (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)
    
    return {'status': 'failed', 'image': image_name, 'instance_id': instance_id}

def get_image_size(image_name):
    """Get image size in MB"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', '{{.Size}}', image_name],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            size_str = result.stdout.strip()
            # Convert size string to MB (rough approximation)
            if 'GB' in size_str:
                return float(size_str.replace('GB', '')) * 1024
            elif 'MB' in size_str:
                return float(size_str.replace('MB', ''))
            else:
                return 0
    except:
        pass
    return 0

def main():
    print("🐳 SWE-Bench Heavy: Official Container Puller (x86_64 for M2)")
    print("=" * 60)
    
    # Load instance IDs
    logger.info("📋 Loading SWE-Bench Lite dataset...")
    instance_ids = load_swe_bench_lite()
    if not instance_ids:
        logger.error("❌ No instance IDs loaded. Exiting.")
        return
    
    logger.info(f"✅ Loaded {len(instance_ids)} instance IDs from dataset")
    
    # Show naming pattern example
    example_id = instance_ids[0]
    example_image = get_official_image_name(example_id)
    logger.info(f"🔍 Example: {example_id} -> {example_image}")
    
    # Check existing containers
    logger.info("🔍 Checking existing containers...")
    existing = check_existing_containers()
    
    # Filter out already pulled containers
    existing_ids = set()
    for container in existing:
        if 'swebench/sweb.eval.x86_64.' in container:
            # Extract instance_id from container name and reverse the transformation
            parts = container.split('.')
            if len(parts) >= 4:
                transformed_id = '.'.join(parts[3:]).replace(':latest', '')
                # Reverse the _1776_ -> __ transformation
                instance_id = transformed_id.replace('_1776_', '__')
                existing_ids.add(instance_id)
    
    to_pull = [id for id in instance_ids if id not in existing_ids]
    
    if not to_pull:
        logger.info("🎉 All containers already exist!")
        return
    
    logger.info(f"📦 Need to pull: {len(to_pull)} containers")
    logger.info(f"🏗️ Already have: {len(existing_ids)} containers")
    logger.info(f"🖥️ Architecture: x86_64 (emulated on M2 Mac)")
    logger.info(f"🔄 Concurrency: 3 parallel downloads")
    
    # Check for resume capability
    saved_progress = load_progress()
    if saved_progress:
        logger.info(f"📂 Found previous session - resuming from {saved_progress['completed']}/{saved_progress['total']}")
    
    # Initialize tracking
    start_time = datetime.now()
    results = {'success': 0, 'failed': 0, 'not_found': 0}
    completed = 0
    total_size_mb = 0
    
    print("\n🚀 Starting downloads...")
    print("-" * 60)
    
    # Pull containers with 3 concurrent downloads (optimized for home internet)
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_id = {executor.submit(pull_container, instance_id): instance_id 
                       for instance_id in to_pull}
        
        for future in as_completed(future_to_id):
            result = future.result()
            completed += 1
            results[result['status']] += 1
            
            # Track download size
            if result['status'] == 'success' and 'size_mb' in result:
                total_size_mb += result['size_mb']
            
            # Calculate progress stats
            elapsed = (datetime.now() - start_time).total_seconds()
            eta = estimate_time_remaining(completed, len(to_pull), elapsed)
            percent = (completed / len(to_pull)) * 100
            
            # Status indicator
            status_icon = "✅" if result['status'] == 'success' else ("🔍" if result['status'] == 'not_found' else "❌")
            
            # Progress line with ETA
            if result['status'] == 'success':
                duration = result.get('duration', 0)
                size = result.get('size_mb', 0)
                logger.info(f"{status_icon} {result['instance_id']} ({duration:.1f}s, {size:.0f}MB)")
            else:
                logger.info(f"{status_icon} {result['instance_id']} - {result['status']}")
            
            # Progress summary every 5 containers or at milestones
            if completed % 5 == 0 or completed in [1, 10, 25, 50, 100] or completed == len(to_pull):
                print(f"\n📊 Progress: {completed}/{len(to_pull)} ({percent:.1f}%) | "
                      f"✅ {results['success']} | ❌ {results['failed']} | 🔍 {results['not_found']} | "
                      f"ETA: {eta}")
                
                if total_size_mb > 0:
                    print(f"💾 Downloaded: {total_size_mb/1024:.1f}GB | "
                          f"Avg: {total_size_mb/completed:.0f}MB per container")
                
                # Save progress for resume capability
                save_progress(completed, len(to_pull), results, start_time)
                print("-" * 60)
    
    # Final summary
    elapsed_total = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 60)
    print("🏁 DOWNLOAD COMPLETE!")
    print("=" * 60)
    print(f"✅ Successfully pulled: {results['success']}")
    print(f"❌ Failed to pull: {results['failed']}")
    print(f"🔍 Not found: {results['not_found']}")
    print(f"📦 Total containers available: {results['success'] + len(existing_ids)}")
    print(f"💾 Total downloaded: {total_size_mb/1024:.1f}GB")
    print(f"⏱️ Total time: {elapsed_total/3600:.1f} hours")
    
    if results['success'] > 0:
        print(f"\n🎉 Successfully downloaded {results['success']} official SWE-Bench containers!")
        print("💡 These x86_64 containers run perfectly on M2 via Docker emulation")
        print("🔧 Ready to test with your grading system!")
    
    # Clean up progress file
    if os.path.exists('pull_progress.json'):
        os.remove('pull_progress.json')
        print("🗑️ Cleaned up progress file")

if __name__ == "__main__":
    main()
