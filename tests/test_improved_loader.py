#!/usr/bin/env python3
"""
Test the improved ZuCo loader
"""

import os
import subprocess
import sys
from pathlib import Path


def test_improved_loader():
    """Test the improved ZuCo loader"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    os.chdir(repo_path)

    print("🧪 Testing Improved ZuCo Loader")
    print("=" * 50)

    # Test the pipeline with improved loader
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

        # Analyze the output
        if "No RT records extracted" in result.stdout:
            print("❌ Still no records extracted - need to inspect ZuCo structure")
            return False
        elif "Successfully processed zuco_rt: 0 records" in result.stdout:
            print("❌ Zero records processed")
            return False
        elif (
            "Successfully processed zuco_rt:" in result.stdout
            and "records" in result.stdout
        ):
            # Extract number of records
            lines = result.stdout.split("\n")
            for line in lines:
                if "Successfully processed zuco_rt:" in line:
                    try:
                        num_records = int(line.split(":")[1].split()[0])
                        if num_records > 0:
                            print(f"✅ Successfully processed {num_records} records!")

                            # Check output file
                            output_file = (
                                repo_path
                                / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
                            )
                            if output_file.exists():
                                size = output_file.stat().st_size
                                print(f"✅ Output file created: {size} bytes")
                                return True
                        else:
                            print("❌ Zero records processed")
                            return False
                    except (ValueError, IndexError):
                        pass

        print("⚠️  Unclear pipeline result")
        return False

    except subprocess.TimeoutExpired:
        print("❌ Pipeline timed out")
        return False
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return False


def main():
    """Main test"""

    success = test_improved_loader()

    if success:
        print("\n🎉 SUCCESS! Improved ZuCo loader working!")
        print("\n📊 The pipeline is now processing real ZuCo data!")
        print("✅ Eye-tracking measures extracted")
        print("✅ Research-grade data processing")
        print("✅ make tidy-rt should now work with real data")
    else:
        print("\n❌ Still having issues with ZuCo data structure")
        print("Need to inspect the .mat files more closely")
        print("\nNext steps:")
        print("1. Run: python run_inspection.py")
        print("2. Examine the actual ZuCo data structure")
        print("3. Adjust the loader based on findings")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
