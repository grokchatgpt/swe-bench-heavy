#!/usr/bin/env python3

import json

# Read the 12 issues we want
with open('test_12_instances.json', 'r') as f:
    target_issues = json.load(f)

print("Target issues:")
for i, issue in enumerate(target_issues):
    print(f"{i}: {issue}")

# Read the full dataset and find indices
indices = []
with open('swe_bench_lite.jsonl', 'r') as f:
    for line_num, line in enumerate(f):
        data = json.loads(line.strip())
        instance_id = data['instance_id']
        if instance_id in target_issues:
            indices.append(line_num)
            print(f"Found {instance_id} at index {line_num}")

print(f"\nIndices for config.json: {','.join(map(str, sorted(indices)))}")

# Verify we have one issue per repo
repos = set()
for idx in sorted(indices):
    with open('swe_bench_lite.jsonl', 'r') as f:
        for i, line in enumerate(f):
            if i == idx:
                data = json.loads(line.strip())
                repo = data['repo']
                repos.add(repo)
                print(f"Index {idx}: {data['instance_id']} ({repo})")
                break

print(f"\nRepos covered ({len(repos)}):")
for repo in sorted(repos):
    print(f"  {repo}")
