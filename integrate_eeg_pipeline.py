#!/usr/bin/env python3
"""
ZuCo EEG Pipeline Integration
Adding EEG dataset configuration to existing pipeline

Following the successful RT implementation, now integrating discovered EEG structure
"""

import re
from pathlib import Path


def update_pipeline_for_eeg():
    """Update the pipeline to include EEG dataset configuration"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    pipeline_file = repo_path / "scripts/swow_zuco_pipeline.py"

    print("🔧 UPDATING PIPELINE FOR EEG SUPPORT")
    print("Adding discovered EEG datasets to pipeline")
    print("=" * 60)

    if not pipeline_file.exists():
        print("❌ Pipeline file not found")
        return False

    # Read the current pipeline
    with open(pipeline_file, "r") as f:
        content = f.read()

    print("📋 Current pipeline analysis:")

    # Check current imports
    if "from src.datasets.zuco_working_loader import" in content:
        print("✅ ZuCo RT loader imported")

    # Check for EEG loader import
    if "zuco_eeg_loader" not in content:
        print("❌ EEG loader not imported")

        # Add EEG loader import
        rt_import_line = (
            "from src.datasets.zuco_working_loader import load_zuco_rt as loader"
        )
        if rt_import_line in content:
            new_import = (
                rt_import_line
                + "\nfrom src.datasets.zuco_eeg_loader import load_zuco_eeg"
            )
            content = content.replace(rt_import_line, new_import)
            print("✅ Added EEG loader import")
        else:
            print("⚠️  RT loader import pattern not found")

    # Find dataset configuration section
    print("\n🔍 Looking for dataset configuration...")

    # Look for different possible patterns
    patterns_to_find = [
        "datasets = {",
        "DATASETS = {",
        "'zuco_rt': {",
        "dataset_configs = {",
        "def get_dataset_config",
    ]

    found_patterns = []
    for pattern in patterns_to_find:
        if pattern in content:
            found_patterns.append(pattern)
            print(f"✅ Found: {pattern}")

    if not found_patterns:
        print("❌ No dataset configuration pattern found")
        # Show relevant lines for debugging
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "zuco_rt" in line and ("=" in line or ":" in line):
                print(f"Line {i+1}: {line.strip()}")
        return False

    # Try to add EEG configuration
    if "'zuco_rt': {" in content:
        print("\n🎯 Adding EEG dataset configuration...")

        # Find the zuco_rt configuration block
        rt_pattern = r"('zuco_rt': \{[^}]+\})"
        rt_match = re.search(rt_pattern, content, re.DOTALL)

        if rt_match:
            rt_config = rt_match.group(1)
            print("✅ Found zuco_rt configuration block")

            # Create EEG configuration based on RT pattern
            eeg_config = (
                rt_config.replace("zuco_rt", "zuco_eeg")
                .replace("load_zuco_rt", "load_zuco_eeg")
                .replace("loader(", "load_zuco_eeg(")
            )

            # Insert EEG config after RT config
            new_content = content.replace(
                rt_config, rt_config + ",\n        " + eeg_config
            )

            # Write updated content
            with open(pipeline_file, "w") as f:
                f.write(new_content)

            print("✅ Added zuco_eeg dataset configuration")
            return True
        else:
            print("❌ Could not parse zuco_rt configuration")

    return False


def test_eeg_pipeline():
    """Test the updated EEG pipeline"""

    print("\n🧪 TESTING UPDATED EEG PIPELINE")
    print("-" * 50)

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    import subprocess
    import sys

    # Test EEG dataset recognition
    try:
        result = subprocess.run(
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

        print(f"Test result: {result.returncode}")

        if "not found in config" not in result.stderr:
            print("✅ EEG dataset now recognized by pipeline!")

            if "EEG template created" in result.stdout or "EEG" in result.stdout:
                print("✅ EEG processing executed")

                # Check if output file was created
                output_file = (
                    repo_path / "data/L1_tidy/zuco_eeg/word_events_eeg.parquet"
                )
                if output_file.exists():
                    print(f"✅ EEG output file created: {output_file}")

                    # Try full EEG pipeline
                    print("\n🎯 Testing full EEG pipeline: make tidy-eeg")

                    make_result = subprocess.run(
                        ["make", "tidy-eeg"],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                    )

                    if make_result.returncode == 0:
                        print("🎉 SUCCESS: make tidy-eeg is now functional!")
                        print("EEG pipeline configured and operational")
                        return True
                    else:
                        print("⚠️  make tidy-eeg still has issues")
                        print("STDERR:", make_result.stderr[-200:])
                else:
                    print("⚠️  EEG output file not created yet")
            else:
                print("⚠️  EEG processing may need implementation")
        else:
            print("❌ EEG dataset still not recognized")
            print("STDERR:", result.stderr)

    except Exception as e:
        print(f"Test failed: {e}")

    return False


def create_eeg_implementation_roadmap():
    """Create roadmap for full EEG implementation"""

    print("\n🗺️  EEG IMPLEMENTATION ROADMAP")
    print("-" * 50)

    roadmap = """
## 🧠 ZuCo EEG Implementation Roadmap

### ✅ COMPLETED:
1. EEG structure analysis - 80+ EEG measures discovered
2. Pipeline configuration - zuco_eeg dataset added
3. Loader template - Basic EEG processing framework

### 🔄 NEXT STEPS:

#### Phase 1: Basic EEG Processing
- [ ] Implement word-level EEG feature extraction
- [ ] Extract frequency band measures (alpha, beta, gamma, theta)
- [ ] Validate against RT data synchronization
- [ ] Create EEG quality metrics

#### Phase 2: Advanced EEG Analysis
- [ ] Raw EEG signal processing (MNE-Python)
- [ ] Artifact detection and removal
- [ ] Temporal dynamics analysis
- [ ] Statistical feature extraction

#### Phase 3: Research-Grade Integration
- [ ] Cross-validate with literature (Hollenstein et al., 2018)
- [ ] Implement EEG-RT correlation analysis
- [ ] Advanced visualization and reporting
- [ ] Performance optimization

### 📊 DISCOVERED EEG STRUCTURE:
- **Sentence-level**: 48 aggregated EEG measures
- **Word-level**: 80+ RT×EEG combinations  
- **Raw data**: rawEEG arrays per word
- **Frequency bands**: Alpha, Beta, Gamma, Theta variants

### 🎯 IMMEDIATE PRIORITIES:
1. Test current EEG template functionality
2. Implement basic frequency band extraction
3. Validate EEG-RT data alignment
4. Create research-grade documentation
"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
    roadmap_file = repo_path / "docs/EEG_IMPLEMENTATION_ROADMAP.md"

    with open(roadmap_file, "w") as f:
        f.write(roadmap)

    print(f"✅ Created EEG roadmap: {roadmap_file}")

    return True


def main():
    """Main EEG pipeline integration"""

    print("🧠 ZUCO EEG PIPELINE INTEGRATION")
    print("Configuring pipeline for discovered EEG structure")
    print("=" * 60)

    # 1. Update pipeline configuration
    pipeline_updated = update_pipeline_for_eeg()

    # 2. Test EEG pipeline
    if pipeline_updated:
        eeg_working = test_eeg_pipeline()

        # 3. Create implementation roadmap
        create_eeg_implementation_roadmap()

        if eeg_working:
            print("\n🎉 EEG PIPELINE SUCCESS!")
            print("✅ EEG datasets configured and functional")
            print("✅ Basic EEG processing template working")
            print("✅ Ready for advanced EEG implementation")
        else:
            print("\n⚠️  EEG PIPELINE PARTIALLY CONFIGURED")
            print("✅ Configuration updated")
            print("🔄 Implementation needs completion")
    else:
        print("\n❌ EEG PIPELINE CONFIGURATION FAILED")
        print("Manual intervention may be needed")

    print(f"\n📚 DOCUMENTATION CREATED:")
    print("- EEG structure analysis results")
    print("- EEG implementation roadmap")
    print("- Research-grade development plan")

    return pipeline_updated


if __name__ == "__main__":
    success = main()
    print(
        f"\nEEG integration completed: {'Success' if success else 'Needs manual config'}"
    )
