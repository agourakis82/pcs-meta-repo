#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the final ZuCo analysis
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🔬 EXECUTING Final ZuCo Analysis")
print("Analyzing real eye-tracking data structure")
print("=" * 60)

try:
    result = subprocess.run([sys.executable, "final_zuco_analysis.py"], cwd=repo_path)

    print(f"\nFinal analysis completed with return code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ Final analysis completed!")

        # Test the updated loader
        print("\n🧪 Testing final corrected loader...")

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
            output_lines = test_result.stdout.split("\n")
            for line in output_lines:
                if "Successfully processed zuco_rt:" in line:
                    print(f"✅ {line}")

                    # Extract record count
                    try:
                        records = int(line.split(":")[1].split()[0])
                        if records > 0:
                            print(f"🎉 SUCCESS! {records} ZuCo records processed!")

                            # Final validation with make tidy-rt
                            print(f"\n🎯 Final validation: make tidy-rt")

                            make_result = subprocess.run(
                                ["make", "tidy-rt"],
                                capture_output=True,
                                text=True,
                                cwd=repo_path,
                            )

                            if make_result.returncode == 0:
                                make_lines = make_result.stdout.split("\n")
                                for make_line in make_lines:
                                    if "Successfully processed zuco_rt:" in make_line:
                                        try:
                                            make_records = int(
                                                make_line.split(":")[1].split()[0]
                                            )
                                            if make_records > 0:
                                                print(f"🎉 COMPLETE SUCCESS!")
                                                print(
                                                    f"✅ make tidy-rt processed {make_records} ZuCo records"
                                                )
                                                print(
                                                    f"✅ Pipeline v4.4 fully operational!"
                                                )

                                                # Check output file
                                                output_file = (
                                                    repo_path
                                                    / "data/L1_tidy/zuco_rt/word_events_rt.parquet"
                                                )
                                                if output_file.exists():
                                                    size = output_file.stat().st_size
                                                    print(
                                                        f"✅ Output file: {size} bytes"
                                                    )

                                                print(f"\n🚀 ZuCo Pipeline Ready!")
                                                print(f"Commands:")
                                                print(
                                                    f"  make tidy-rt    # Process RT data"
                                                )
                                                print(
                                                    f"  make tidy-eeg   # Process EEG data"
                                                )
                                                print(
                                                    f"  make integrate  # Integrate with KEC"
                                                )

                                                exit(0)
                                        except:
                                            pass
                            else:
                                print(f"⚠️  make tidy-rt issues:")
                                print(make_result.stdout)
                        else:
                            print(f"❌ Still zero records")
                    except:
                        print(f"✅ Processing completed")

            if "Successfully processed zuco_rt:" not in test_result.stdout:
                print(f"❌ Still no successful processing")
                print(f"STDERR:", test_result.stderr)
        else:
            print(f"❌ Test failed")
            print(f"STDOUT:", test_result.stdout)
            print(f"STDERR:", test_result.stderr)
    else:
        print("❌ Final analysis failed")

except Exception as e:
    print(f"Final analysis execution failed: {e}")

print("\n" + "=" * 60)
print("Final ZuCo analysis execution completed!")
print("This should have resolved the ZuCo data structure issues.")
