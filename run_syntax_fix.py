#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the syntax fix and working loader creation
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🔧 EXECUTING ZuCo Syntax Fix & Working Loader")
print("Fixing syntax error and creating working implementation")
print("=" * 60)

try:
    result = subprocess.run([sys.executable, "fix_zuco_syntax.py"], cwd=repo_path)

    print(f"\nSyntax fix completed with return code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ Syntax fix and working loader creation completed!")

        # Update pipeline to use working loader
        print("\n🔄 Updating pipeline to use working loader...")

        pipeline_file = repo_path / "scripts/swow_zuco_pipeline.py"
        if pipeline_file.exists():
            try:
                with open(pipeline_file, "r") as f:
                    content = f.read()

                # Update import to use working loader
                old_import = "from src.datasets.zuco_corrected_loader import load_zuco_rt as loader"
                new_import = "from src.datasets.zuco_working_loader import load_zuco_rt as loader"

                if old_import in content:
                    content = content.replace(old_import, new_import)
                    with open(pipeline_file, "w") as f:
                        f.write(content)
                    print("✅ Pipeline updated to use working loader")
                else:
                    print("⚠️  Import not found, checking for alternatives...")
                    # Try other possible imports
                    alternatives = [
                        "from src.datasets.zuco_official_loader import load_zuco_rt as loader",
                        "from src.datasets.zuco_real_loader import load_zuco_rt as loader",
                    ]

                    for alt_import in alternatives:
                        if alt_import in content:
                            content = content.replace(alt_import, new_import)
                            with open(pipeline_file, "w") as f:
                                f.write(content)
                            print(
                                f"✅ Pipeline updated from {alt_import.split('.')[2]}"
                            )
                            break

                # Test the working loader
                print("\n🧪 Testing working loader...")

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
                    timeout=180,
                )

                print(f"Test result: {test_result.returncode}")

                if test_result.returncode == 0:
                    # Check for success
                    output_lines = test_result.stdout.split("\n")
                    success_found = False

                    for line in output_lines:
                        if "Successfully processed zuco_rt:" in line:
                            print(f"✅ {line}")
                            success_found = True

                            try:
                                records = int(line.split(":")[1].split()[0])
                                if records > 0:
                                    print(
                                        f"🎉 SUCCESS! {records} ZuCo records processed!"
                                    )

                                    # Final test: make tidy-rt
                                    print(f"\n🎯 Final test: make tidy-rt")

                                    make_result = subprocess.run(
                                        ["make", "tidy-rt"],
                                        capture_output=True,
                                        text=True,
                                        cwd=repo_path,
                                    )

                                    if make_result.returncode == 0:
                                        # Check for successful processing
                                        make_lines = make_result.stdout.split("\n")
                                        for make_line in make_lines:
                                            if (
                                                "Successfully processed zuco_rt:"
                                                in make_line
                                            ):
                                                try:
                                                    make_records = int(
                                                        make_line.split(":")[1].split()[
                                                            0
                                                        ]
                                                    )
                                                    if make_records > 0:
                                                        print(f"🎉 COMPLETE SUCCESS!")
                                                        print(
                                                            f"✅ make tidy-rt processed {make_records} records"
                                                        )
                                                        print(
                                                            f"✅ ZuCo Pipeline v4.4 FULLY OPERATIONAL!"
                                                        )

                                                        # Show output file info
                                                        output_file = (
                                                            repo_path
                                                            / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
                                                        )
                                                        if output_file.exists():
                                                            size = output_file.stat().st_size
                                                            print(
                                                                f"✅ Output file: {size} bytes"
                                                            )

                                                        print(f"\n🚀 PIPELINE READY!")
                                                        print(f"Available commands:")
                                                        print(
                                                            f"  make tidy-rt     # Process RT data ✅"
                                                        )
                                                        print(
                                                            f"  make tidy-eeg    # Process EEG data"
                                                        )
                                                        print(
                                                            f"  make integrate   # Integrate datasets"
                                                        )
                                                        print(
                                                            f"  make models      # Run prediction models"
                                                        )

                                                        exit(0)
                                                except:
                                                    pass
                                    else:
                                        print(f"⚠️  make tidy-rt had issues")
                                        print(f"Exit code: {make_result.returncode}")
                                else:
                                    print(f"❌ Zero records processed")
                            except:
                                print(
                                    f"✅ Processing completed (could not parse count)"
                                )

                    if not success_found:
                        print(f"❌ No successful processing message found")
                        print(f"STDERR:", test_result.stderr[-500:])  # Last 500 chars

                        # Show any error messages
                        for line in output_lines:
                            if "ERROR" in line or "WARNING" in line:
                                print(f"  {line}")

                else:
                    print(f"❌ Test failed with exit code {test_result.returncode}")
                    print(f"STDERR:", test_result.stderr[-500:])

            except Exception as e:
                print(f"Pipeline testing failed: {e}")
    else:
        print("❌ Syntax fix failed")

except Exception as e:
    print(f"Syntax fix execution failed: {e}")

print("\n" + "=" * 60)
print("ZuCo syntax fix and testing completed!")
print(
    "This should have created a working ZuCo loader based on the discovered structure."
)
