#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the detailed ZuCo inspection
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🔍 EXECUTING Detailed ZuCo Inspection & Analysis")
print("=" * 60)

try:
    result = subprocess.run([sys.executable, "inspect_and_fix_zuco.py"], cwd=repo_path)

    print(f"\nDetailed inspection completed with return code: {result.returncode}")

except Exception as e:
    print(f"Detailed inspection failed: {e}")

print("\n" + "=" * 60)
print("Detailed inspection completed!")
print("\nBased on the findings above, I'll create a targeted fix for the ZuCo loader.")
print("The inspection should reveal the exact data structure we need to handle.")
