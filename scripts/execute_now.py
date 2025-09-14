import os
import subprocess
import sys
from pathlib import Path

# Execute the pipeline setup
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🧠 Executing PCS-Meta-Repo v4.4 Pipeline")
print("=" * 50)
print(f"Working directory: {repo_path}")

# Run the executor
try:
    result = subprocess.run(
        [sys.executable, "run_v4.4_now.py"],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )

    print("STDOUT:")
    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print(f"Return code: {result.returncode}")

except Exception as e:
    print(f"Execution failed: {e}")

print("\n" + "=" * 50)
print("Execution completed!")
