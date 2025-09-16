#!/usr/bin/env python3
"""Execute the fix and test immediately"""

import os
import subprocess
import sys
from pathlib import Path

# Change to repo directory
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🧠 Executing Pipeline Fix and Test")
print("=" * 50)

# Run the fix script
try:
    result = subprocess.run([sys.executable, "fix_and_test.py"], cwd=repo_path)

    print(f"\nFix and test completed with return code: {result.returncode}")

except Exception as e:
    print(f"Execution failed: {e}")

print("\n" + "=" * 50)
print("Fix and test execution completed!")
