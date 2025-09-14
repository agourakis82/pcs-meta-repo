#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the quick test
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🔧 EXECUTING Quick Path Fix Test")
print("=" * 50)

try:
    result = subprocess.run([sys.executable, "quick_path_test.py"], cwd=repo_path)

    print(f"\nQuick test completed with return code: {result.returncode}")

    if result.returncode == 0:
        print("\n🎉 PATH ISSUE RESOLVED!")

        # Now test the actual make command
        print("\n" + "=" * 40)
        print("FINAL TEST: make tidy-rt")

        try:
            make_result = subprocess.run(
                ["make", "tidy-rt"], cwd=repo_path, capture_output=True, text=True
            )

            print(f"make tidy-rt result: {make_result.returncode}")
            print("Output:")
            print(make_result.stdout)

            if make_result.stderr:
                print("Errors:")
                print(make_result.stderr)

            # Check the specific error message
            if "ZuCo data not found at scripts/scripts/" in make_result.stdout:
                print("❌ Still has double scripts/ issue")
            elif "ZuCo data not found" in make_result.stdout:
                print("❌ Still has path issues")
            elif "Failed to process zuco_rt" in make_result.stdout:
                print("❌ Processing failed")
            elif "completed successfully" in make_result.stdout:
                print("✅ make tidy-rt now works!")
            else:
                print("⚠️  Unknown result")

        except Exception as e:
            print(f"Make test failed: {e}")

    else:
        print("❌ Quick test failed")

except Exception as e:
    print(f"Test execution failed: {e}")

print("\n" + "=" * 50)
print("Path fix test completed!")
