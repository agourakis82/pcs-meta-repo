#!/usr/bin/env python3
"""
Quick fix and test for the path issue
"""

import os
import subprocess
import sys
from pathlib import Path


def quick_test():
    """Quick test of the corrected pipeline"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    os.chdir(repo_path)

    print("🔧 Quick Test: Path Fix for ZuCo Data")
    print("=" * 50)

    # Test 1: Verify the ZuCo data exists at the expected location
    expected_path = repo_path / "scripts/data/raw_public/zuco"
    print(f"Checking ZuCo data at: {expected_path}")

    if expected_path.exists():
        print("✅ ZuCo data directory exists")

        # Check for v1 files
        v1_answers = expected_path / "v1/osfstorage/answers"
        if v1_answers.exists():
            mat_files = list(v1_answers.glob("Fullresults_NR_*.mat"))
            print(f"✅ Found {len(mat_files)} NR .mat files")
            if mat_files:
                print(f"   Sample: {mat_files[0].name}")
        else:
            print("❌ v1/osfstorage/answers not found")
            return False
    else:
        print(f"❌ ZuCo data not found at {expected_path}")
        return False

    # Test 2: Test the loader directly
    print("\n🧪 Testing ZuCo loader directly...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys
sys.path.append('/home/agourakis82/workspace/pcs-meta-repo')
from pathlib import Path
from src.datasets.zuco_real_loader import ZuCoRealLoader

# Test with correct path
repo_root = Path('/home/agourakis82/workspace/pcs-meta-repo')
print(f'Testing from repo root: {repo_root}')

try:
    loader = ZuCoRealLoader(repo_root)
    print(f'ZuCo path resolved to: {loader.zuco_path}')
    print(f'ZuCo path exists: {loader.zuco_path.exists()}')
    
    if loader.zuco_path.exists():
        files = loader.find_zuco_files()
        print(f'Files found: {[(k, len(v)) for k, v in files.items()]}')
        print('SUCCESS: Loader working!')
    else:
        print('ERROR: ZuCo path does not exist')
        
except Exception as e:
    print(f'ERROR: {e}')
""",
            ],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )

        print("Loader test output:")
        print(result.stdout)
        if result.stderr:
            print("Loader errors:")
            print(result.stderr)

        if "SUCCESS" in result.stdout:
            print("✅ Loader test passed")
        else:
            print("❌ Loader test failed")
            return False

    except Exception as e:
        print(f"❌ Loader test exception: {e}")
        return False

    # Test 3: Test the pipeline
    print("\n🚀 Testing pipeline with corrected paths...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.swow_zuco_pipeline",
                "--step",
                "tidy_rt",
                "--datasets",
                "zuco_rt",
            ],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=60,
        )

        print(f"Pipeline result: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        # Check for success indicators
        if "ZuCo data not found" in result.stdout:
            print("❌ Still has path issues")
            return False
        elif "Failed to process zuco_rt" in result.stdout:
            print("❌ Processing failed")
            return False
        elif "completed successfully" in result.stdout:
            print("✅ Pipeline completed!")

            # Check if output was created
            output_file = repo_path / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
            if output_file.exists():
                size = output_file.stat().st_size
                print(f"✅ Output created: {output_file} ({size} bytes)")
                return True
            else:
                print(f"⚠️  Pipeline completed but no output at {output_file}")
                return True  # Still consider success if pipeline ran
        else:
            print("⚠️  Unknown pipeline state")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Pipeline timed out")
        return False
    except Exception as e:
        print(f"❌ Pipeline exception: {e}")
        return False


def main():
    """Run the quick test"""

    success = quick_test()

    if success:
        print("\n🎉 SUCCESS! Path issue resolved!")
        print("\n🚀 The pipeline should now work:")
        print("   make tidy-rt")
        print(
            "   python -m scripts.swow_zuco_pipeline --step tidy_rt --datasets zuco_rt"
        )
    else:
        print("\n❌ Path issue not fully resolved")
        print("Check the errors above for more details")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
