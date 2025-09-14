#!/usr/bin/env python3
"""
ZuCo EEG Pipeline Configuration Analysis
Research-grade investigation of EEG data structure and pipeline setup

Following successful ZuCo RT correction methodology:
1. Analyze EEG data structure in ZuCo files
2. Configure pipeline datasets
3. Implement EEG processing following neuroscience best practices

References:
- Hollenstein et al. (2018). ZuCo corpus with simultaneous EEG
- MNE-Python best practices for EEG preprocessing
- EEGLAB pipeline standards
"""

import json
import logging
from pathlib import Path

import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_zuco_eeg_structure():
    """Analyze EEG data structure in ZuCo files"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    print("🧠 ZUCO EEG STRUCTURE ANALYSIS")
    print("Research-grade investigation of EEG data")
    print("=" * 60)

    # Use the same files that worked for RT data
    zuco_path = repo_path / "scripts/data/raw_public/zuco/v1/osfstorage"

    # Check EEG data in the working SR files
    sr_matlab_dir = zuco_path / "task1- SR/Matlab files"

    if not sr_matlab_dir.exists():
        print("❌ SR Matlab directory not found")
        return None

    # Use the same file that worked for RT
    test_file = sr_matlab_dir / "resultsZJM_SR.mat"

    if not test_file.exists():
        print("❌ Test file not found")
        return None

    print(f"📁 Analyzing: {test_file.name}")

    try:
        # Load the same file structure we know works
        mat_data = scipy.io.loadmat(
            str(test_file), squeeze_me=True, struct_as_record=False
        )

        if "sentenceData" not in mat_data:
            print("❌ No sentenceData found")
            return None

        sentence_data = mat_data["sentenceData"]
        print(f"✅ Found {len(sentence_data)} sentences")

        # Analyze first sentence for EEG structure
        first_sentence = sentence_data[0]
        sentence_attrs = [a for a in dir(first_sentence) if not a.startswith("_")]

        print(f"\n📊 Sentence-level attributes:")
        eeg_sentence_attrs = []
        for attr in sentence_attrs:
            if "eeg" in attr.lower() or "mean" in attr.lower():
                eeg_sentence_attrs.append(attr)
                print(f"  - {attr}")

        # Analyze word-level EEG data
        if hasattr(first_sentence, "word"):
            words = first_sentence.word
            if hasattr(words, "__len__") and len(words) > 0:
                first_word = words[0]
                word_attrs = [a for a in dir(first_word) if not a.startswith("_")]

                print(f"\n🔬 Word-level attributes:")
                eeg_word_attrs = []
                raw_eeg_attrs = []

                for attr in word_attrs:
                    attr_lower = attr.lower()
                    if "eeg" in attr_lower:
                        if "raw" in attr_lower:
                            raw_eeg_attrs.append(attr)
                        else:
                            eeg_word_attrs.append(attr)
                        print(f"  - {attr}")

                # Check for EEG band-specific measures
                eeg_bands = [
                    "a1",
                    "a2",
                    "b1",
                    "b2",
                    "g1",
                    "g2",
                    "t1",
                    "t2",
                ]  # alpha, beta, gamma, theta
                band_attrs = []

                for attr in word_attrs:
                    for band in eeg_bands:
                        if f"_{band}" in attr.lower():
                            band_attrs.append(attr)
                            break

                if band_attrs:
                    print(f"\n🌊 EEG Band-specific measures found:")
                    for attr in band_attrs[:10]:  # Show first 10
                        print(f"  - {attr}")
                    if len(band_attrs) > 10:
                        print(f"  ... and {len(band_attrs) - 10} more")

                # Analyze raw EEG data structure
                if raw_eeg_attrs:
                    print(f"\n⚡ Raw EEG data analysis:")
                    for raw_attr in raw_eeg_attrs:
                        try:
                            raw_data = getattr(first_word, raw_attr)
                            print(
                                f"  - {raw_attr}: {type(raw_data)}, shape: {getattr(raw_data, 'shape', 'no shape')}"
                            )
                        except Exception as e:
                            print(f"  - {raw_attr}: Error accessing - {e}")

                return {
                    "sentence_eeg_attrs": eeg_sentence_attrs,
                    "word_eeg_attrs": eeg_word_attrs,
                    "raw_eeg_attrs": raw_eeg_attrs,
                    "band_attrs": band_attrs,
                    "structure_valid": True,
                }

        return None

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None


def check_pipeline_config():
    """Check current pipeline configuration for EEG datasets"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    print(f"\n🔧 PIPELINE CONFIGURATION ANALYSIS")
    print("-" * 50)

    # Check config files
    config_files = [
        "scripts/swow_zuco_pipeline.py",
        "configs/datasets.json",
        "configs/pipeline.json",
    ]

    for config_file in config_files:
        config_path = repo_path / config_file
        if config_path.exists():
            print(f"✅ Found: {config_file}")

            if config_file.endswith(".py"):
                # Check Python pipeline file
                with open(config_path, "r") as f:
                    content = f.read()

                if "zuco_eeg" in content:
                    print(f"  - Contains 'zuco_eeg' reference")
                else:
                    print(f"  - No 'zuco_eeg' reference found")

                if "tidy_eeg" in content:
                    print(f"  - Contains 'tidy_eeg' step")

            elif config_file.endswith(".json"):
                # Check JSON config
                try:
                    with open(config_path, "r") as f:
                        config_data = json.load(f)
                    print(f"  - JSON keys: {list(config_data.keys())}")
                except Exception as e:
                    print(f"  - Error reading JSON: {e}")
        else:
            print(f"❌ Not found: {config_file}")

    return True


def create_eeg_pipeline_config(eeg_structure):
    """Create EEG pipeline configuration based on discovered structure"""

    repo_path = Path("/home/agourakis82/workspace/pcs-meta-repo")

    print(f"\n🎯 CREATING EEG PIPELINE CONFIGURATION")
    print("-" * 50)

    if not eeg_structure or not eeg_structure.get("structure_valid"):
        print("❌ Invalid EEG structure, cannot create config")
        return False

    # Create EEG dataset configuration
    eeg_config = {
        "zuco_eeg": {
            "type": "eeg",
            "source": "zuco",
            "raw_data_path": "scripts/data/raw_public/zuco",
            "structure": {
                "hierarchy": "sentenceData -> word -> rawEEG",
                "sentence_measures": eeg_structure["sentence_eeg_attrs"],
                "word_measures": eeg_structure["word_eeg_attrs"],
                "raw_data_fields": eeg_structure["raw_eeg_attrs"],
                "frequency_bands": eeg_structure["band_attrs"][:20],  # Limit for config
            },
            "preprocessing": {
                "sampling_rate": "detect_from_data",
                "filters": "research_grade",
                "artifacts": "automatic_detection",
                "epoching": "word_based",
            },
            "output": {
                "format": "parquet",
                "path": "data/L1_tidy/zuco_eeg/",
                "files": {
                    "word_events_eeg": "word_events_eeg.parquet",
                    "raw_eeg": "raw_eeg_epochs.parquet",
                    "frequency_bands": "eeg_bands.parquet",
                },
            },
        },
        "derco_eeg": {
            "type": "eeg",
            "source": "derco",
            "status": "to_be_implemented",
            "note": "DERCO corpus EEG data",
        },
        "lpp_eeg": {
            "type": "eeg",
            "source": "lpp",
            "status": "to_be_implemented",
            "note": "LPP corpus EEG data",
        },
    }

    # Save EEG configuration
    config_dir = repo_path / "configs"
    config_dir.mkdir(exist_ok=True)

    eeg_config_file = config_dir / "eeg_datasets.json"
    with open(eeg_config_file, "w") as f:
        json.dump(eeg_config, f, indent=2)

    print(f"✅ Created EEG config: {eeg_config_file}")

    # Create basic EEG loader template
    eeg_loader_template = f'''#!/usr/bin/env python3
"""
ZuCo EEG data loader - Research-grade EEG processing
Based on discovered structure: {eeg_structure}

References:
- Hollenstein et al. (2018). ZuCo simultaneous EEG and eye-tracking
- MNE-Python documentation for EEG preprocessing
- EEGLAB preprocessing pipeline standards
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import scipy.io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZuCoEEGLoader:
    """
    ZuCo EEG loader following neuroscience best practices
    Implements research-grade EEG preprocessing pipeline
    """
    
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        # Use same path resolution as working RT loader
        if str(self.data_root).endswith('scripts'):
            self.zuco_path = self.data_root / "data/raw_public/zuco"
        else:
            self.zuco_path = self.data_root / "scripts/data/raw_public/zuco"
        
        if not self.zuco_path.exists():
            raise FileNotFoundError(f"ZuCo data not found at {{self.zuco_path}}")
            
        logger.info(f"Initialized ZuCo EEG loader for {{self.zuco_path}}")
    
    def find_zuco_eeg_files(self) -> List[Path]:
        """Find ZuCo files with EEG data (same as RT files)"""
        
        files = []
        task_dirs = ["task1- SR", "task2 - NR", "task3 - TSR"]
        
        for task_dir in task_dirs:
            matlab_dir = self.zuco_path / "v1/osfstorage" / task_dir / "Matlab files"
            if matlab_dir.exists():
                mat_files = list(matlab_dir.glob("results*.mat"))
                files.extend(mat_files)
                logger.info(f"Found {{len(mat_files)}} EEG files in {{task_dir}}/Matlab files")
        
        return files[:3]  # Limit for initial testing
    
    def load_zuco_eeg_data(self, output_path: Path) -> pd.DataFrame:
        """
        Load ZuCo EEG data using research-grade preprocessing
        
        Implementation note: This is a template - needs full EEG preprocessing
        """
        logger.info("Loading ZuCo EEG data...")
        
        # Find files (same as RT)
        eeg_files = self.find_zuco_eeg_files()
        
        if not eeg_files:
            logger.error("No ZuCo EEG files found")
            return pd.DataFrame()
        
        # TODO: Implement full EEG preprocessing pipeline
        # This would include:
        # 1. Raw EEG data extraction
        # 2. Filtering (band-pass, notch)
        # 3. Artifact detection and removal
        # 4. Epoching around word events
        # 5. Frequency band analysis
        # 6. Statistical feature extraction
        
        logger.warning("ZuCo EEG loader template created - needs full implementation")
        logger.info("EEG preprocessing pipeline requires:")
        logger.info("  - MNE-Python for signal processing")
        logger.info("  - Artifact detection algorithms")  
        logger.info("  - Frequency band decomposition")
        logger.info("  - Word-event synchronization")
        
        # Create placeholder DataFrame for pipeline testing
        placeholder_data = [{{
            'subject_id': 'template',
            'task_id': 'eeg_test',
            'word': 'placeholder',
            'eeg_alpha': np.nan,
            'eeg_beta': np.nan,
            'eeg_gamma': np.nan,
            'eeg_theta': np.nan
        }}]
        
        df = pd.DataFrame(placeholder_data)
        
        # Save placeholder
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved EEG template to {{output_path}}")
        
        return df

def load_zuco_eeg(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    """Main entry point for ZuCo EEG loading"""
    repo_root = raw_dir.parent.parent.parent
    loader = ZuCoEEGLoader(repo_root)
    return loader.load_zuco_eeg_data(output_path)

if __name__ == "__main__":
    # Test EEG loader template
    repo_root = Path("/home/agourakis82/workspace/pcs-meta-repo")
    output_file = repo_root / "data/L1_tidy/zuco_eeg/word_events_eeg.parquet"
    
    df = load_zuco_eeg(repo_root / "scripts/data/raw_public/zuco", output_file)
    print(f"EEG template created: {{len(df)}} records")
'''

    # Save EEG loader template
    eeg_loader_file = repo_path / "src/datasets/zuco_eeg_loader.py"
    with open(eeg_loader_file, "w") as f:
        f.write(eeg_loader_template)

    print(f"✅ Created EEG loader template: {eeg_loader_file}")

    return True


def main():
    """Main EEG pipeline analysis and configuration"""

    print("🧠 ZUCO EEG PIPELINE SETUP")
    print("Research-grade analysis following RT success")
    print("=" * 60)

    # 1. Analyze EEG structure
    eeg_structure = analyze_zuco_eeg_structure()

    # 2. Check pipeline config
    check_pipeline_config()

    # 3. Create EEG configuration
    if eeg_structure:
        config_created = create_eeg_pipeline_config(eeg_structure)

        if config_created:
            print(f"\n🎯 NEXT STEPS FOR EEG PIPELINE:")
            print("1. Review EEG structure analysis")
            print("2. Implement full EEG preprocessing pipeline")
            print("3. Add EEG datasets to main pipeline config")
            print("4. Test EEG processing with research-grade validation")

            print(f"\n📚 EEG IMPLEMENTATION REQUIREMENTS:")
            print("- MNE-Python for signal processing")
            print("- Frequency band analysis (alpha, beta, gamma, theta)")
            print("- Artifact detection and removal")
            print("- Word-event synchronization")
            print("- Statistical feature extraction")

            return True

    return False


if __name__ == "__main__":
    success = main()
    print(f"\nEEG analysis completed: {'Success' if success else 'Failed'}")
