#!/usr/bin/env python3
"""
Pull Official SWE-Bench Pre-built Containers
Downloads all 300 containers from the official SWE-Bench registry
"""

import json
import subprocess
import sys
import os
import time
from pathlib import Path
import docker
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OfficialContainerPuller:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.swe_bench_path = Path("swe-bench-official")
        
        # Official SWE-Bench namespace - this is where pre-built containers are stored
        self.namespace = "swebench"  # This is the official namespace
        
    def get_all_instance_ids(self) -> List[str]:
        """Get ALL 300 instance IDs from official SWE-Bench Lite dataset"""
        logger.info("Loading ALL 300 SWE-Bench Lite instance IDs...")
        
        try:
            sys.path.append(str(self.swe_bench_path))
            from datasets import load_dataset
            
            # Load the complete official dataset
            dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
            instance_ids = [instance["instance_id"] for instance in dataset]
            
            logger.info(f"Loaded {len(instance_ids)} instance IDs from official dataset")
            return sorted(instance_ids)
            
        except Exception as e:
            logger.error(f"Failed to load official dataset: {e}")
            raise Exception("Could not load instance IDs from official dataset")
    
    def get_container_image_name(self, instance_id: str, arch: str = "arm64") -> str:
        """Get the official container image name for an instance"""
        # Based on the test_spec.py code:
        # key = f"sweb.eval.{self.arch}.{self.instance_id.lower()}:{self.instance_image_tag}"
        # if self.is_remote_image:
        #     key = f"{self.namespace}/{key}".replace("__", "_1776_")
        
        clean_instance_id = instance_id.lower().replace("__", "_1776_")
        image_name = f"{self.namespace}/sweb.eval.{arch}.{clean_instance_id}:latest"
        return image_name
    
    def pull_single_container(self, instance_id: str, arch: str = "arm64") -> Dict[str, Any]:
        """Pull a single container image"""
        image_name = self.get_container_image_name(instance_id, arch)
        
        start_time = time.time()
        try:
            logger.info(f"Pulling {image_name}...")
            
            # Try to pull the image
            image = self.docker_client.images.pull(image_name)
            
            pull_time = time.time() - start_time
            logger.info(f"✅ Successfully pulled {image_name} ({pull_time:.1f}s)")
            
            return {
                "instance_id": instance_id,
                "image_name": image_name,
                "status": "success",
                "pull_time": pull_time,
                "image_id": image.id,
                "size": image.attrs.get("Size", 0)
            }
            
        except docker.errors.ImageNotFound:
            logger.warning(f"❌ Image not found: {image_name}")
            return {
                "instance_id": instance_id,
                "image_name": image_name,
                "status": "not_found",
                "error": "Image not found in registry"
            }
        except Exception as e:
            logger.error(f"❌ Failed to pull {image_name}: {e}")
            return {
                "instance_id": instance_id,
                "image_name": image_name,
                "status": "error",
                "error": str(e)
            }
    
    def pull_all_containers(self, max_workers: int = 4) -> Dict[str, Any]:
        """Pull all 300 containers in parallel"""
        logger.info("Starting to pull all official SWE-Bench containers...")
        
        # Get all instance IDs
        instance_ids = self.get_all_instance_ids()
        logger.info(f"Will attempt to pull {len(instance_ids)} containers")
        
        # Determine architecture
        import platform
        if platform.machine() in {"aarch64", "arm64"}:
            arch = "arm64"
        else:
            arch = "x86_64"
        
        logger.info(f"Using architecture: {arch}")
        
        # Pull containers in parallel
        results = []
        successful = 0
        failed = 0
        not_found = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pull tasks
            future_to_instance = {
                executor.submit(self.pull_single_container, instance_id, arch): instance_id 
                for instance_id in instance_ids
            }
            
            # Process completed tasks
            for future in as_completed(future_to_instance):
                result = future.result()
                results.append(result)
                
                if result["status"] == "success":
                    successful += 1
                elif result["status"] == "not_found":
                    not_found += 1
                else:
                    failed += 1
                
                # Progress update
                total_processed = successful + failed + not_found
                logger.info(f"Progress: {total_processed}/{len(instance_ids)} "
                          f"(✅ {successful} | ❌ {failed} | 🔍 {not_found})")
        
        # Summary
        summary = {
            "total_instances": len(instance_ids),
            "successful": successful,
            "failed": failed,
            "not_found": not_found,
            "results": results,
            "architecture": arch,
            "namespace": self.namespace
        }
        
        logger.info(f"Pull complete: {successful}/{len(instance_ids)} successful")
        logger.info(f"Failed: {failed}, Not found: {not_found}")
        
        return summary
    
    def save_results(self, summary: Dict[str, Any]):
        """Save pull results to file"""
        results_file = Path("container_pull_results.json")
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results saved to {results_file}")
    
    def check_existing_containers(self) -> List[str]:
        """Check which SWE-Bench containers already exist locally"""
        existing = []
        try:
            images = self.docker_client.images.list()
            for image in images:
                for tag in image.tags:
                    if f"{self.namespace}/sweb.eval." in tag:
                        existing.append(tag)
        except Exception as e:
            logger.error(f"Error checking existing containers: {e}")
        
        logger.info(f"Found {len(existing)} existing SWE-Bench containers")
        return existing

def main():
    """Main entry point"""
    puller = OfficialContainerPuller()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Pull official SWE-Bench pre-built containers")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of parallel downloads")
    parser.add_argument("--check-only", action="store_true", help="Only check existing containers")
    
    args = parser.parse_args()
    
    if args.check_only:
        existing = puller.check_existing_containers()
        for container in existing:
            print(container)
        return True
    
    # Check existing containers first
    existing = puller.check_existing_containers()
    if existing:
        logger.info(f"Found {len(existing)} existing containers")
    
    # Pull all containers
    summary = puller.pull_all_containers(max_workers=args.max_workers)
    
    # Save results
    puller.save_results(summary)
    
    # Final summary
    if summary["successful"] == summary["total_instances"]:
        print("🎉 All containers pulled successfully!")
        print("You can now use the official pre-built containers for testing!")
        return True
    else:
        print(f"⚠️  {summary['failed'] + summary['not_found']} containers failed to pull")
        print("Check container_pull_results.json for details")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
