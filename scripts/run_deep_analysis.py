#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the deep ZuCo analysis
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🔬 EXECUTING Deep ZuCo Structure Analysis")
print("Research-grade investigation of data structure")
print("=" * 60)

try:
    result = subprocess.run([sys.executable, "deep_zuco_analysis.py"], cwd=repo_path)

    print(f"\nDeep analysis completed with return code: {result.returncode}")

    print("\n" + "=" * 60)
    print("NEXT: Based on the findings above, I'll create the correct ZuCo loader")
    print("The analysis should reveal the exact path to sentence/word data.")

except Exception as e:
    print(f"Deep analysis failed: {e}")

print("\n" + "=" * 60)
print("Deep analysis execution completed!")
print("Now I can create the targeted fix based on the discovered structure.")
