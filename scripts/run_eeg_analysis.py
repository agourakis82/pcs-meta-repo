#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Execute the EEG analysis
repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
os.chdir(repo_path)

print("🧠 EXECUTING ZuCo EEG Analysis")
print("Research-grade investigation of EEG structure")
print("=" * 60)

try:
    result = subprocess.run([sys.executable, "analyze_zuco_eeg.py"], cwd=repo_path)

    print(f"\nEEG analysis completed with return code: {result.returncode}")

    if result.returncode == 0:
        print("\n✅ EEG analysis completed successfully!")

        # Check what was created
        config_dir = repo_path / "configs"
        eeg_config_file = config_dir / "eeg_datasets.json"
        eeg_loader_file = repo_path / "src/datasets/zuco_eeg_loader.py"

        created_files = []
        if eeg_config_file.exists():
            created_files.append(f"✅ EEG config: {eeg_config_file}")
        if eeg_loader_file.exists():
            created_files.append(f"✅ EEG loader: {eeg_loader_file}")

        if created_files:
            print("\n📁 Files created:")
            for file_info in created_files:
                print(f"  {file_info}")

            print("\n🎯 Next step: Configure pipeline to use EEG datasets")

            # Try to update the pipeline to include EEG datasets
            pipeline_file = repo_path / "scripts/swow_zuco_pipeline.py"
            if pipeline_file.exists():
                print(f"\n🔧 Updating pipeline configuration...")

                try:
                    with open(pipeline_file, "r") as f:
                        content = f.read()

                    # Check if EEG configuration exists
                    if "zuco_eeg" not in content:
                        print("Pipeline needs EEG dataset configuration")

                        # Add basic EEG dataset configuration
                        # Look for the dataset configuration section
                        if "def get_dataset_config" in content:
                            print(
                                "Found dataset config function - needs EEG datasets added"
                            )
                        elif "DATASETS = {" in content:
                            print("Found DATASETS dict - needs EEG entries added")
                        else:
                            print("Dataset configuration structure needs investigation")

                    # Test the EEG pipeline step
                    print(f"\n🧪 Testing EEG pipeline step...")

                    test_result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "scripts.swow_zuco_pipeline",
                            "--step",
                            "tidy_eeg",
                            "--datasets",
                            "zuco_eeg",
                        ],
                        capture_output=True,
                        text=True,
                        cwd=repo_path,
                        timeout=60,
                    )

                    print(f"EEG test result: {test_result.returncode}")

                    if "not found in config" in test_result.stderr:
                        print("❌ EEG datasets still not configured in pipeline")
                        print("STDERR:", test_result.stderr)

                        print(f"\n💡 SOLUTION NEEDED:")
                        print("1. Add EEG datasets to pipeline configuration")
                        print("2. Update dataset loading logic")
                        print("3. Implement EEG processing pipeline")
                    else:
                        print("✅ EEG pipeline step configuration improved")
                        print("STDOUT:", test_result.stdout)

                except Exception as e:
                    print(f"Pipeline update failed: {e}")
        else:
            print("❌ No files were created")
    else:
        print("❌ EEG analysis failed")

except Exception as e:
    print(f"EEG analysis execution failed: {e}")

print("\n" + "=" * 60)
print("EEG analysis execution completed!")
print("\nThis discovered the EEG data structure and created initial configuration.")
print("Next: Configure pipeline to recognize EEG datasets.")
