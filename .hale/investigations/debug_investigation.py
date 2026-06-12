#!/usr/bin/env python3
"""Auto-generated investigation script."""
import sys, os, json

results = {}

# Check import paths
results['sys_path'] = sys.path[:5]
results['cwd'] = os.getcwd()

print(json.dumps(results, indent=2))