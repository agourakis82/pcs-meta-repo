#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the targeted ZuCo analysis
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🎯 EXECUTING Targeted ZuCo Analysis")
print("Finding the real eye-tracking data files")
print("=" * 60)

try:
    result = subprocess.run(
        [sys.executable, "targeted_zuco_analysis.py"], cwd=repo_path
    )

    print(f"\nTargeted analysis completed with return code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ Analysis completed successfully!")

        # Check if corrected loader was created
        corrected_loader = repo_path / "src/datasets/zuco_corrected_loader.py"
        if corrected_loader.exists():
            print(f"✅ Corrected loader created: {corrected_loader}")

            # Test the corrected loader
            print("\n🧪 Testing corrected loader...")

            # Update pipeline to use corrected loader
            pipeline_file = repo_path / "scripts/swow_zuco_pipeline.py"
            if pipeline_file.exists():
                try:
                    with open(pipeline_file, "r") as f:
                        content = f.read()

                    # Update import to use corrected loader
                    old_import = "from src.datasets.zuco_official_loader import load_zuco_rt as loader"
                    new_import = "from src.datasets.zuco_corrected_loader import load_zuco_rt as loader"

                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        with open(pipeline_file, "w") as f:
                            f.write(content)
                        print("✅ Pipeline updated to use corrected loader")

                    # Test the corrected pipeline
                    print("\n🚀 Testing corrected pipeline...")
                    test_result = subprocess.run(
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
                        timeout=120,
                    )

                    print(f"Test result: {test_result.returncode}")

                    if "Successfully processed zuco_rt:" in test_result.stdout:
                        for line in test_result.stdout.split("\n"):
                            if "Successfully processed zuco_rt:" in line:
                                print(f"✅ {line}")

                        # Final test with make tidy-rt
                        print("\n🎯 Final test: make tidy-rt")
                        make_result = subprocess.run(
                            ["make", "tidy-rt"],
                            capture_output=True,
                            text=True,
                            cwd=repo_path,
                        )

                        if (
                            make_result.returncode == 0
                            and "Successfully processed zuco_rt:" in make_result.stdout
                        ):
                            # Extract number of records
                            for line in make_result.stdout.split("\n"):
                                if "Successfully processed zuco_rt:" in line:
                                    try:
                                        records = int(line.split(":")[1].split()[0])
                                        if records > 0:
                                            print(
                                                f"🎉 COMPLETE SUCCESS! {records} ZuCo records processed!"
                                            )
                                            print("✅ make tidy-rt fully operational")
                                        else:
                                            print("⚠️  Still no records extracted")
                                    except:
                                        print("✅ Pipeline completed")
                        else:
                            print("⚠️  make tidy-rt issues remain")
                            print(make_result.stdout)
                    else:
                        print("❌ Still no records processed")
                        print("STDOUT:", test_result.stdout)
                        print("STDERR:", test_result.stderr)

                except Exception as e:
                    print(f"Pipeline testing failed: {e}")
        else:
            print("❌ Corrected loader not created")
    else:
        print("❌ Analysis had issues")

except Exception as e:
    print(f"Targeted analysis failed: {e}")

print("\n" + "=" * 60)
print("Targeted analysis execution completed!")
print("This should identify where the real ZuCo eye-tracking data is located.")
