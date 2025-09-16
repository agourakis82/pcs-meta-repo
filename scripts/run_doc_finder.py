#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the dataset documentation finder
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("📚 EXECUTING Dataset Documentation Finder")
print("Research-grade analysis of official processing instructions")
print("=" * 60)

try:
    result = subprocess.run([sys.executable, "find_dataset_docs.py"], cwd=repo_path)

    print(f"\nDocumentation search completed with return code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ Documentation successfully extracted!")

        # Check what was created
        docs_dir = repo_path / "docs/dataset_docs"
        if docs_dir.exists():
            files = list(docs_dir.glob("*"))
            print(f"\n📁 Created documentation files:")
            for file in files:
                size = file.stat().st_size
                print(f"  - {file.name} ({size} bytes)")

            # Show snippet of processing instructions
            proc_file = docs_dir / "processing_instructions.md"
            if proc_file.exists():
                print(f"\n📋 Processing Instructions Preview:")
                with open(proc_file, "r") as f:
                    content = f.read()
                    # Show first 500 characters
                    print(content[:500] + "..." if len(content) > 500 else content)

            # Show ZuCo analysis if available
            zuco_file = docs_dir / "zuco_official_analysis.json"
            if zuco_file.exists():
                print(f"\n🔍 ZuCo Official Analysis Available:")
                print(f"  File: {zuco_file}")
                print("  Contains patterns from official utils_ZuCo.py")

        print(f"\n🚀 Next Steps:")
        print("1. Review docs/dataset_docs/processing_instructions.md")
        print("2. Study official ZuCo loader patterns")
        print("3. Create research-grade loader based on official methods")

    else:
        print("❌ Documentation search had issues")

except Exception as e:
    print(f"Documentation search failed: {e}")

print("\n" + "=" * 60)
print("Documentation search completed!")
print("Now we have official processing instructions to follow!")
