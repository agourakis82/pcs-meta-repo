#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the ZuCo structure inspection
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🔍 EXECUTING ZuCo Structure Inspection")
print("=" * 50)

try:
    result = subprocess.run(
        [sys.executable, "inspect_zuco_structure.py"], cwd=repo_path
    )

    print(f"\nInspection completed with return code: {result.returncode}")

except Exception as e:
    print(f"Inspection failed: {e}")

print("\n" + "=" * 50)
print("Inspection completed!")
