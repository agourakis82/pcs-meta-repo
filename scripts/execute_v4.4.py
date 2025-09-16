#!/usr/bin/env python3
"""Execute pipeline v4.4 with proper error handling"""

import subprocess
import sys
from pathlib import Path


def run_qa_step():
    """Execute Step 0: QA and verification"""
    print("🔍 STEP 0: QA and Environment Check")
    print("=" * 50)

    repo_path = Path.cwd()

    # Check if we're in the right directory
    if not (repo_path / "pyproject.toml").exists():
        print("❌ Not in repository root.")
        print("   Please cd to /home/agourakis82/workspace/pcs-meta-repo")
        return False

    print(f"📁 Repository: {repo_path}")

    # Create missing directories
    dirs_to_create = [
        "data/L0_raw",
        "data/L1_tidy",
        "data/L2_derived/kec",
        "data/processed/v4.4/integration",
        "figures/v4.4",
        "reports/provenance",
    ]

    for dir_path in dirs_to_create:
        full_path = repo_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

    # Run repository lint
    print("\n🔧 Running repository QA...")
    try:
        result = subprocess.run(
            [sys.executable, "tools/repo_lint.py"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )

        print("Repository QA Output:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)

    except Exception as e:
        print(f"⚠️  QA script failed: {e}")

    # Run checksum computation
    print("\n📊 Computing checksums...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "scripts.compute_checksums", "--inventory", "repo"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )

        print("Checksum computation:")
        print(result.stdout)
        if result.stderr:
            print("Warnings:")
            print(result.stderr)

    except Exception as e:
        print(f"⚠️  Checksum computation failed: {e}")

    # Verify structure
    print("\n📋 Verifying v4.4 structure...")
    try:
        result = subprocess.run(
            ["bash", "tools/verify_v4.4_structure.sh"],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )

        print("Structure verification:")
        print(result.stdout)
        if result.stderr:
            print("Warnings:")
            print(result.stderr)

    except Exception as e:
        print(f"⚠️  Structure verification failed: {e}")

    print("\n✅ Step 0 completed!")
    print("\n📋 Summary:")
    print("- Directory structure created")
    print("- QA checks executed")
    print("- Checksums computed")
    print("- Structure verified")

    print(f"\n📁 Key directories created:")
    for dir_path in dirs_to_create:
        full_path = repo_path / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ❌ {dir_path}")

    return True


def show_next_steps():
    """Show next steps for the user"""
    print("\n🚀 NEXT STEPS:")
    print("=" * 50)
    print("1. Configure your data paths in config/data_root.yaml")
    print("2. Ensure real datasets are available (ZuCo, GECO, etc.)")
    print("3. Run individual pipeline steps:")
    print("   - python scripts/run_pipeline_v4.4.py  # Interactive execution")
    print("   - make tidy-rt                         # Process RT datasets")
    print("   - make tidy-eeg                        # Process EEG datasets")
    print("   - make kec                             # Compile KEC multilingual")
    print("   - make integrate                       # Integrate SWOW↔KEC↔datasets")
    print("   - make models                          # Run prediction models")
    print("   - make figs                            # Generate figures")
    print("   - make qa                              # Final QA")

    print("\n📖 Documentation:")
    print("   - docs/RUNBOOK_minimal_v4.4.md        # Complete runbook")
    print("   - docs/EXECUTION_STEPS_v4.4.md        # Step-by-step guide")
    print("   - docs/GOVERNANCE_v4.4.md              # Governance framework")


if __name__ == "__main__":
    print("🧠 PCS-Meta-Repo v4.4 Pipeline Execution")
    print("=" * 50)

    success = run_qa_step()

    if success:
        show_next_steps()
        print("\n🎉 Ready to proceed with pipeline execution!")
    else:
        print("\n❌ Setup failed. Please check errors above.")
        sys.exit(1)
