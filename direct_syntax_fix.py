#!/usr/bin/env python3
"""
Direct syntax fix for ZuCo pipeline
Correcting indentation error at line 71
"""

from pathlib import Path


def fix_pipeline_syntax():
    """Fix the syntax error directly"""

    pipeline_file = Path(
        "/home/agourakis82/workspace/pcs-meta-repo/scripts/swow_zuco_pipeline.py"
    )

    print("🔧 DIRECT SYNTAX FIX")
    print("=" * 40)

    # Read the file
    with open(pipeline_file, "r") as f:
        lines = f.readlines()

    print(f"File has {len(lines)} lines")

    # Check around line 71
    for i in range(max(0, 68), min(len(lines), 75)):
        line_num = i + 1
        line = lines[i].rstrip()
        marker = ">>> " if line_num == 71 else "    "
        print(f"{marker}{line_num:3d}: {line}")

    # Fix the indentation issue
    fixed = False
    for i, line in enumerate(lines):
        if 'elif dataset.startswith("geco"):' in line:
            # Check if it's improperly indented
            if not line.startswith("        elif"):  # Should have 8 spaces
                lines[i] = '        elif dataset.startswith("geco"):\n'
                print(f"✅ Fixed line {i+1} indentation")
                fixed = True
            break

    if not fixed:
        # More comprehensive fix - look for the pattern and fix context
        for i, line in enumerate(lines):
            if 'elif dataset.startswith("geco"):' in line:
                # Ensure the previous line ends properly
                if i > 0:
                    prev_line = lines[i - 1].rstrip()
                    if not prev_line.endswith("}"):
                        # Look backwards for the closing brace
                        for j in range(i - 1, max(0, i - 10), -1):
                            if lines[j].strip().endswith("}"):
                                # Insert missing brace or fix structure
                                break

                # Fix current line indentation
                lines[i] = '        elif dataset.startswith("geco"):\n'
                print(f"✅ Fixed line {i+1}")
                fixed = True
                break

    if not fixed:
        print("❌ Could not find the problematic line")
        return False

    # Write the corrected file
    with open(pipeline_file, "w") as f:
        f.writelines(lines)

    print("✅ File written with corrections")

    return True


def test_syntax():
    """Test if the syntax is now correct"""

    import subprocess
    import sys

    print("\n🧪 TESTING SYNTAX")
    print("-" * 30)

    try:
        result = subprocess.run(
            [sys.executable, "-c", "import scripts.swow_zuco_pipeline"],
            cwd=Path("/home/agourakis82/workspace/pcs-meta-repo"),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Syntax is now valid!")
            return True
        else:
            print("❌ Syntax error remains:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_eeg_functionality():
    """Test EEG functionality after syntax fix"""

    import subprocess
    import sys

    print("\n🧪 TESTING EEG FUNCTIONALITY")
    print("-" * 35)

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    try:
        eeg_test = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.swow_zuco_pipeline",
                "--step",
                "tidy_eeg",
                "--datasets",
                "zuco_eeg",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        print(f"EEG test result: {eeg_test.returncode}")

        if eeg_test.returncode == 0:
            if "not found in config" not in eeg_test.stderr:
                print("✅ zuco_eeg dataset recognized!")

                # Test make tidy-eeg
                print("\n🎯 Testing make tidy-eeg...")

                make_result = subprocess.run(
                    ["make", "tidy-eeg"], cwd=repo_path, capture_output=True, text=True
                )

                if make_result.returncode == 0:
                    print("🎉 make tidy-eeg SUCCESS!")

                    # Show results
                    for line in make_result.stdout.split("\n"):
                        if "Successfully processed" in line:
                            print(f"✅ {line}")

                    return True
                else:
                    print("⚠️  make tidy-eeg issues")
                    print("STDERR:", make_result.stderr[-200:])
            else:
                print("❌ EEG dataset still not recognized")
        else:
            print("❌ EEG test failed")
            print("STDERR:", eeg_test.stderr)

    except Exception as e:
        print(f"EEG test failed: {e}")

    return False


def main():
    """Main syntax fix"""

    print("🔧 ZUCO PIPELINE SYNTAX FIX")
    print("Direct correction of indentation error")
    print("=" * 50)

    # Fix syntax
    syntax_fixed = fix_pipeline_syntax()

    if syntax_fixed:
        # Test syntax
        syntax_valid = test_syntax()

        if syntax_valid:
            # Test EEG functionality
            eeg_working = test_eeg_functionality()

            if eeg_working:
                print("\n🎉 COMPLETE SUCCESS!")
                print("✅ Syntax fixed")
                print("✅ EEG pipeline operational")
                print("✅ make tidy-eeg functional")

                print("\n🚀 ZUCO PIPELINE v4.4 STATUS:")
                print("✅ make tidy-rt    - RT data processing")
                print("✅ make tidy-eeg   - EEG data processing")
                print("🔄 make integrate  - Cross-dataset integration")
                print("🔄 make models     - Predictive modeling")

            else:
                print("\n⚠️  SYNTAX FIXED, EEG NEEDS CONFIGURATION")
                print("✅ No more syntax errors")
                print("🔄 EEG dataset configuration needs work")
        else:
            print("\n❌ SYNTAX ERRORS REMAIN")
            print("Manual inspection needed")
    else:
        print("\n❌ COULD NOT FIX SYNTAX AUTOMATICALLY")

    return syntax_fixed


if __name__ == "__main__":
    success = main()
    print(
        f"\nSyntax fix completed: {'Success' if success else 'Manual intervention needed'}"
    )
